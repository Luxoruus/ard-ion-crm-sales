
# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt, getdate
from datetime import date, timedelta
from calendar import monthrange

from .config import (
    BA_ITEM_GROUPS, BA_RATES, ION_ROLE_RATES, ION_ABOVE_ADDON,
    FIRST_YEAR_ADDON_RATE, PROJECT_ACQ_BONUS, PENALTY_PLANS
)

# ------------------------
# Utilities: dates & FY Q
# ------------------------

def _add_months(d: date, m: int) -> date:
    y = d.year + (d.month - 1 + m) // 12
    m2 = (d.month - 1 + m) % 12 + 1
    day = min(d.day, monthrange(y, m2)[1])
    return date(y, m2, day)

def get_quarter_window(fiscal_year: str, quarter: str) -> tuple[date, date, list[int]]:
    fy = frappe.get_doc("Fiscal Year", fiscal_year)
    off = {"Q1": 0, "Q2": 3, "Q3": 6, "Q4": 9}[quarter]
    q_start = _add_months(fy.year_start_date, off)
    q_end = _add_months(q_start, 3) - timedelta(days=1)
    months = []
    m = q_start.month; y = q_start.year
    for _ in range(3):
        months.append(m)
        m += 1
        if m > 12:
            m = 1; y += 1
    return q_start, q_end, months

# ------------------------------------
# Fully-paid date (Payment Entry refs)
# ------------------------------------

def get_invoice_fully_paid_on(si_name: str):
    si = frappe.get_doc("Sales Invoice", si_name)
    if flt(si.outstanding_amount):
        return None
    per = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_doctype": "Sales Invoice", "reference_name": si_name, "docstatus": 1},
        fields=["parent"]
    )
    dates = []
    for r in per:
        pe_date = frappe.db.get_value("Payment Entry", r["parent"], "posting_date")
        if pe_date:
            dates.append(getdate(pe_date))
    return max(dates) if dates else getdate(si.modified)

# ---------------------------------
# Monthly Distribution reader (robust)
# ---------------------------------

def _get_monthly_distribution(md_name: str) -> dict[int, float]:
    """
    Return {1..12: fraction} for a Monthly Distribution.
    Supports:
      A) child rows (Monthly Distribution Percentage: month + percentage/percentage_allocation)
      B) legacy parent columns jan..dec
    Normalizes to fractions that sum ~1.0; if missing/empty → even split.
    """
    even = {i: 1.0/12.0 for i in range(1, 13)}
    try:
        md = frappe.get_doc("Monthly Distribution", md_name)
    except Exception:
        return even

    # Shape A: child table
    try:
        meta = frappe.get_meta("Monthly Distribution")
        child_fieldname = None
        for f in meta.fields:
            if getattr(f, "fieldtype", "") == "Table" and f.options:
                if f.options == "Monthly Distribution Percentage":
                    child_fieldname = f.fieldname
                    break
                if not child_fieldname:
                    child_fieldname = f.fieldname
        rows = md.get(child_fieldname) if child_fieldname else None
        if rows:
            month_map = {
                "jan":1,"january":1,  "feb":2,"february":2, "mar":3,"march":3,
                "apr":4,"april":4,    "may":5,
                "jun":6,"june":6,     "jul":7,"july":7,
                "aug":8,"august":8,   "sep":9,"sept":9,"september":9,
                "oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12
            }
            out = {i: 0.0 for i in range(1, 13)}
            total = 0.0
            for r in rows:
                m_val = (r.get("month") or r.get("month_name") or r.get("month_no") or "").strip()
                p_val = r.get("percentage", None)
                if p_val is None:
                    p_val = r.get("percentage_allocation", None)
                try:
                    m_num = int(m_val)
                except Exception:
                    m_num = month_map.get(str(m_val).lower())
                p = flt(p_val or 0)
                if m_num in out:
                    out[m_num] += p
                    total += p
            if total > 0:
                if abs(total - 100.0) < 1e-6:
                    return {m: out[m] / 100.0 for m in out}
                if 0.999 <= total <= 1.001:
                    return out
                return {m: out[m] / total for m in out}
            return even
    except Exception:
        pass

    # Shape B: legacy jan..dec columns
    try:
        values = {
            1: flt(getattr(md, "jan", 0) or 0),  2: flt(getattr(md, "feb", 0) or 0),  3: flt(getattr(md, "mar", 0) or 0),
            4: flt(getattr(md, "apr", 0) or 0),  5: flt(getattr(md, "may", 0) or 0),  6: flt(getattr(md, "jun", 0) or 0),
            7: flt(getattr(md, "jul", 0) or 0),  8: flt(getattr(md, "aug", 0) or 0),  9: flt(getattr(md, "sep", 0) or 0),
            10: flt(getattr(md, "oct", 0) or 0), 11: flt(getattr(md, "nov", 0) or 0), 12: flt(getattr(md, "dec", 0) or 0),
        }
        total = sum(values.values())
        if total > 0:
            if abs(total - 100.0) < 1e-6:
                return {m: values[m] / 100.0 for m in values}
            if 0.999 <= total <= 1.001:
                return values
            return {m: values[m] / total for m in values}
    except Exception:
        pass

    return even

# ---------------------------------
# Targets from Target Detail rows
# ---------------------------------

def quarter_target_from_distribution(sales_person: str, fiscal_year: str, months3: list[int]) -> float:
    rows = frappe.get_all(
        "Target Detail",
        filters={"parenttype": "Sales Person", "parent": sales_person, "fiscal_year": fiscal_year},
        fields=["target_amount", "distribution_id"],
    )
    if not rows:
        return 0.0

    total = 0.0
    for r in rows:
        amt = flt(r.get("target_amount") or 0)
        if not amt:
            continue
        md_name = r.get("distribution_id")
        if md_name:
            dist = _get_monthly_distribution(md_name)
            share = sum(dist.get(m, 0) for m in months3)
            total += amt * share
        else:
            total += amt * (3.0 / 12.0)
    return round(total, 2)

# --------------------------
# Category detection (BA)
# --------------------------

def _category_of_item_by_group(ig: str) -> str | None:
    for key, name in BA_ITEM_GROUPS.items():
        if ig == name:
            return key
    return None

def _category_amounts_for_si(si) -> dict[str, float]:
    out = {}
    for it in (si.get("items") or []):
        ig = si.get("custom_service_category")
        # ig = it.get("item_group")
        amt = flt(it.get("base_amount") or 0)
        cat = _category_of_item_by_group(ig)
        if not cat:
            continue
        out[cat] = out.get(cat, 0.0) + amt
    return out

# -------------------------------------------------
# Transaction type detection (Old / NewLead / Upsell)
# -------------------------------------------------

def _customer_has_prior_invoice(customer: str, before_date: date | None = None) -> bool:
    filters = {"customer": customer, "docstatus": 1}
    if before_date:
        filters["posting_date"] = ("<", before_date)  # <= handles same-day postings
    if customer == "Commission Test":
        print(frappe.db.get_list("Sales Invoice", filters=filters))
    return bool(frappe.db.exists("Sales Invoice", filters))

def _customer_has_prior_fully_paid(customer: str, before_paid_on: date | None = None) -> bool:
    """True if any SI for this customer is fully paid strictly before before_paid_on."""
    if not before_paid_on:
        return False
    # Pull a small set: up to 200 recent SIs for this customer (submitted)
    sis = frappe.get_all("Sales Invoice", filters={"customer": customer, "docstatus": 1},
                         fields=["name"], order_by="posting_date asc", limit=200)
    for r in sis:
        other = r["name"]
        try:
            paid = get_invoice_fully_paid_on(other)
        except Exception:
            paid = None
        if paid and paid < before_paid_on:
            return True
    return False

def detect_tx_type(si, fully_paid_on: "date", is_renewal_flag=False) -> str:
    """
    NewLead ⇢ no submitted SI for this customer at/before this posting_date
              AND no fully-paid SI strictly before this fully_paid_on.
    Renewal  ⇢ if explicit flag passed (not auto-detected here).
    Upsell   ⇢ otherwise (has prior history).
    """
    had_prior_by_posting = _customer_has_prior_invoice(si.customer, before_date=si.posting_date)
    had_prior_by_paid    = _customer_has_prior_fully_paid(si.customer, before_paid_on=fully_paid_on)
    if not had_prior_by_posting and not had_prior_by_paid:
        return "NewLead"
    if is_renewal_flag:
        return "Old"
    return "Upsell"

# -------------------------------------------
# AM / SM detection via Role Profile
# -------------------------------------------

def _is_user_role_profile(user: str, code: str) -> bool:
    rp = (frappe.db.get_value("User", user, "role_profile_name") or "").strip().upper()
    return rp == code.upper()

def _salesperson_is_am(sales_person: str) -> bool:
    emp = frappe.db.get_value("Sales Person", sales_person, "employee")
    if not emp:
        return False
    user = frappe.db.get_value("Employee", emp, "user_id")
    if not user:
        return False
    return _is_user_role_profile(user, "AM")

def _is_manager_or_sm(sales_person: str) -> bool:
    emp = frappe.db.get_value("Sales Person", sales_person, "employee")
    if not emp:
        return False
    user = frappe.db.get_value("Employee", emp, "user_id")
    if not user:
        return False
    rp = (frappe.db.get_value("User", user, "role_profile_name") or "").strip().upper()
    return rp in {"AM", "SM", "SALES MANAGER"}

# -----------------------------------------
# Payment plan & penalties
# -----------------------------------------

def _payment_plan(si) -> str:
    plan = (getattr(si, "custom_payment_plan", None) or getattr(si, "payment_plan", None) or "").strip().lower()
    return {"yearly":"yearly", "6 months":"6mo", "quarterly":"quarterly"}.get(plan, "yearly")

def _grace_and_cadence_days(plan_key: str) -> tuple[int, int]:
    plan = PENALTY_PLANS.get(plan_key) or PENALTY_PLANS["yearly"]
    return int(plan["grace_days"]), int(plan["cadence_days"])

def _penalty_anchor_date(si):
    """Anchor penalties to SI.due_date (fallback to posting_date)."""
    return getdate(getattr(si, "due_date", None) or si.posting_date)

def _penalty_factor_for_si(si, fully_paid_on: "date") -> float:
    # skip penalty when exception approved
    if getattr(si, "custom_penalty_exception_approved", None) or getattr(si, "penalty_exception_approved", None):
        return 1.0
    plan = _payment_plan(si)               # 'yearly' | '6mo' | 'quarterly'
    grace, cadence = _grace_and_cadence_days(plan)
    anchor_date = _penalty_anchor_date(si) # due_date
    late_days = (getdate(fully_paid_on) - anchor_date).days
    if late_days <= grace:
        return 1.0
    over = late_days - grace
    blocks = 0 if cadence <= 0 else (over // cadence)
    factor = 1.0 - 0.50 - 0.10 * blocks
    return max(0.0, factor)

# -----------------------
# BA rate lookup helpers
# -----------------------

def _rate_non_ion(cat_key: str, tx_type: str, is_above: bool) -> float:
    if is_above:
        return BA_RATES[cat_key]["above"]
    if tx_type == "Old":
        return BA_RATES[cat_key]["old"]
    if tx_type == "NewLead":
        return BA_RATES[cat_key]["new"]
    return BA_RATES[cat_key]["upsell"]

def _rate_ion(role: str, is_above: bool) -> float:
    base = ION_ROLE_RATES.get(role, 0.0)
    return base + (ION_ABOVE_ADDON if is_above else 0.0)

# -----------------------
# Helpers for recipients
# -----------------------

def _skip_ba_commission(si) -> bool:
    # Customer-level exclusions (partnership at cost, ISP BW at cost)
    cust = frappe.get_doc("Customer", si.customer)
    if getattr(cust, "custom_partnership_at_cost", None) or getattr(cust, "partnership_at_cost", None):
        return True
    if getattr(cust, "custom_isp_bw_partnership", None) or getattr(cust, "isp_bw_partnership", None):
        return True
    return False

def _ba_team_on_si(si, include_externals: bool) -> list[str]:
    out = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if not sp: continue
        emp = frappe.db.get_value("Sales Person", sp, "employee")
        dep = frappe.db.get_value("Employee", emp, "department") if emp else None
        if dep and "business" not in dep.lower():
            continue
        # externals excluded unless approved
        if not emp and not include_externals:
            continue
        if sp not in out:
            out.append(sp)
    return out

def _ion_role_for_person_on_si(si, sales_person: str) -> str | None:
    for st in (si.get("sales_team") or []):
        if st.get("sales_person") == sales_person:
            role = (st.get("custom_ion_role") or st.get("ion_role") or "").strip()
            return role if role else None
    return None

def _ba_recipients_for_category(si, cat_key: str, externals_ok) -> list[str]:
    if cat_key == "ION_SOLUTIONS":
        holders = []
        for st in (si.get("sales_team") or []):
            role = (st.get("custom_ion_role") or st.get("ion_role") or "").strip()
            if role in ("Account Lead Acquisition", "Offer Team", "Execution Team"):
                holders.append(st.get("sales_person"))
        return holders
    return _ba_team_on_si(si, bool(externals_ok))

def _ams_on_si(si) -> list[str]:
    ams = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if not sp: continue
        if _salesperson_is_am(sp):
            ams.append(sp)
    return ams

def _non_am_sm_employees_on_si(si) -> list[str]:
    out = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if not sp: continue
        if not _is_manager_or_sm(sp):
            emp = frappe.db.get_value("Sales Person", sp, "employee")
            if emp:
                out.append(sp)
    return out

def _employees_on_si(si) -> list[str]:
    out = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if not sp: continue
        emp = frappe.db.get_value("Sales Person", sp, "employee")
        if emp:
            out.append(sp)
    return out

# --------------------------------------
# Main BA computation per sheet quarter
# --------------------------------------

def compute_ba_for_sheet(sheet) -> dict[str, float]:
    """
    Returns per-person commission map {sales_person: amount} for BA department.

    Key behaviors:
      • Even split of category amounts among eligible BA recipients (ION = role-holders only).
      • Above = add-on on the over-target slice per person (non-ION); ION = role rate + 3% addon when Above (no over-target slicing).
      • +1% first-year add-on: split among non AM/SM employees (New Lead only).
      • +3000 acquisition bonus: split among ALL employees (Hotspot/Ultra; New Lead only).
      • Penalties (AM only): factor applied to AM % commissions for this invoice.
    """
    q_start, q_end, months3 = get_quarter_window(sheet.fiscal_year, sheet.quarter)

    # Lines → people
    people = [ln.sales_person for ln in (sheet.get("commission_lines") or []) if ln.department == "Business Accounts"]

    # Quarter targets per person
    quarter_target = {sp: quarter_target_from_distribution(sp, sheet.fiscal_year, months3) for sp in people}

    # Candidate invoices: posted <= quarter end; include prior-FY as well
    cand_all = frappe.get_all(
        "Sales Invoice",
        filters={"company": sheet.company, "docstatus": 1, "posting_date": ["<=", q_end]},
        fields=["name", "customer", "posting_date", "outstanding_amount"]  # only standards; custom via si.get(...)
    )
    # Sorted by fully-paid date for correct over-target allocation
    cand_sorted = []
    for inv in cand_all:
        paid_on = get_invoice_fully_paid_on(inv["name"])
        if paid_on and (q_start <= paid_on <= q_end):
            cand_sorted.append((paid_on, inv))
    cand_sorted.sort(key=lambda x: (x[0], x[1]["name"]))

    # Running exposure & results
    cum_exposure = {sp: 0.0 for sp in people}
    commission_by_person = {sp: 0.0 for sp in people}

    for paid_on, inv in cand_sorted:
        si = frappe.get_doc("Sales Invoice", inv["name"])
        if _skip_ba_commission(si):
            continue

        # --- SNAPSHOT exposure BEFORE processing this invoice (for penalty recomputation) ---
        prev_cum_before = dict(cum_exposure)

        tx_type = detect_tx_type(si, paid_on, is_renewal_flag=False)
        cat_amounts = _category_amounts_for_si(si)
        externals_ok = bool(si.get("custom_external_rep_approved") or getattr(si, "external_rep_approved", None))

        # % commissions (even split) with over-target add-on for non-ION
        for cat_key, amount in cat_amounts.items():
            if amount <= 0: continue
            rec = _ba_recipients_for_category(si, cat_key, externals_ok)
            if not rec: continue
            eq_base = amount / len(rec)

            for sp in rec:
                if sp not in commission_by_person:
                    continue

                if cat_key == "ION_SOLUTIONS":
                    # ION: role rate + 3% addon if Above; no over-target slicing for ION
                    role = _ion_role_for_person_on_si(si, sp)
                    if not role: continue
                    is_above_now = bool(cum_exposure[sp] >= (quarter_target.get(sp) or 0.0))
                    rate = _rate_ion(role, is_above_now)
                    commission_by_person[sp] += eq_base * rate
                    # exposure increases by eq_base
                    cum_exposure[sp] = cum_exposure.get(sp, 0) + eq_base
                else:
                    # non-ION: base on ALL + full above on over-target slice
                    base_rate  = _rate_non_ion(cat_key, tx_type, False)
                    above_rate = _rate_non_ion(cat_key, tx_type, True)

                    commission_by_person[sp] += eq_base * base_rate

                    tgt      = quarter_target.get(sp, 0.0) or 0.0
                    prev_cum = cum_exposure.get(sp, 0.0) or 0.0
                    above_part = max(0.0, (prev_cum + eq_base) - tgt) - max(0.0, prev_cum - tgt)
                    if above_part > 0:
                        commission_by_person[sp] += above_part * above_rate
                    if sp == "Test Penalty":
                        print(commission_by_person.get("Test Penalty", 0))
                        print(si.customer)
                        print("By posting", _customer_has_prior_invoice(si.customer, before_date=si.posting_date))
                        print("By paid", _customer_has_prior_fully_paid(si.customer, before_paid_on=paid_on))

                    cum_exposure[sp] = prev_cum + eq_base

        # +1% first-year add-on (non AM/SM only), New Lead only
        is_new_lead_tx = (tx_type == "NewLead")
        if is_new_lead_tx and (si.get("custom_first_year_contract_invoice") or getattr(si, "first_year_contract_invoice", None)):
            non_mgr = _non_am_sm_employees_on_si(si)
            if non_mgr:
                addon = flt(si.base_grand_total) * FIRST_YEAR_ADDON_RATE
                per   = addon / len(non_mgr)
                for sp in non_mgr:
                    if sp in commission_by_person:
                        commission_by_person[sp] += per

        # +3000 acquisition bonus (Hotspot/Ultra), New Lead only, split among ALL employees
        if is_new_lead_tx and (si.get("custom_ba_project_acquisition_bonus") or getattr(si, "ba_project_acquisition_bonus", None)):
            has_hs_or_um = (cat_amounts.get("HOTSPOT", 0) > 0) or (cat_amounts.get("ULTRA_MALLS", 0) > 0)
            if has_hs_or_um:
                employees = _employees_on_si(si)
                if employees:
                    per = PROJECT_ACQ_BONUS / len(employees)
                    for sp in employees:
                        if sp in commission_by_person:
                            commission_by_person[sp] += per

        # Penalties (AM only): factor applied to AM % commissions for THIS invoice
        factor = _penalty_factor_for_si(si, paid_on)
        if factor < 1.0:
            ams = _ams_on_si(si)
            if ams:
                # Recompute AM subtotal pre-penalty for this invoice using the SNAPSHOT baseline
                am_subtotal = 0.0
                for cat_key, amount in cat_amounts.items():
                    if amount <= 0: continue
                    rec = _ba_recipients_for_category(si, cat_key, externals_ok)
                    if not rec: continue
                    eq_base = amount / len(rec)
                    for sp in rec:
                        if sp not in ams: continue
                        if cat_key == "ION_SOLUTIONS":
                            role = _ion_role_for_person_on_si(si, sp)
                            if not role: continue
                            is_above_prev = bool(prev_cum_before.get(sp, 0.0) >= (quarter_target.get(sp) or 0.0))
                            rate = _rate_ion(role, is_above_prev)
                            am_subtotal += eq_base * rate
                        else:
                            base_rate  = _rate_non_ion(cat_key, tx_type, False)
                            above_rate = _rate_non_ion(cat_key, tx_type, True)
                            am_subtotal += eq_base * base_rate

                            tgt      = quarter_target.get(sp, 0.0) or 0.0
                            prev_cum = prev_cum_before.get(sp, 0.0) or 0.0
                            above_part = max(0.0, (prev_cum + eq_base) - tgt) - max(0.0, prev_cum - tgt)
                            if above_part > 0:
                                am_subtotal += above_part * above_rate

                reduction = am_subtotal * (1.0 - factor)
                per_am_reduction = reduction / len(ams)
                for sp in ams:
                    commission_by_person[sp] = max(0.0, commission_by_person.get(sp, 0.0) - per_am_reduction)

    return commission_by_person
