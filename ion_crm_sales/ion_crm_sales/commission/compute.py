
# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt, getdate
from datetime import date, timedelta
from calendar import monthrange

from .config import SALES_ITEM_GROUPS, SALES_RATES, SALES_SPLITS

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
    """Same robust reader as BA."""
    even = {i: 1.0/12.0 for i in range(1, 13)}
    try:
        md = frappe.get_doc("Monthly Distribution", md_name)
    except Exception:
        return even

    # Shape A: child table rows
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

    # Shape B: legacy
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
# Sales category detection
# --------------------------

def _sales_category_of_item_group(ig: str) -> str | None:
    if ig == SALES_ITEM_GROUPS["HOME"]:
        return "HOME"
    if ig == SALES_ITEM_GROUPS["HOTSPOT"]:
        return "HOTSPOT"
    return None

def _sales_category_amounts_for_si(si) -> dict[str, float]:
    out = {}
    for it in (si.get("items") or []):
        # ig = it.get("item_group")
        ig = si.get("custom_service_category")
        amt = flt(it.get("base_amount") or 0)
        cat = _sales_category_of_item_group(ig)
        if not cat:
            continue
        out[cat] = out.get(cat, 0.0) + amt
    return out

# --------------------------
# Manager / rest on invoice
# --------------------------

def _is_sales_manager(sp: str) -> bool:
    # Prefer custom_ field; fallback to legacy if it exists
    val = frappe.db.get_value("Sales Person", sp, "custom_is_sales_manager")
    if val is None:
        val = frappe.db.get_value("Sales Person", sp, "is_sales_manager")
    return bool(val)

def _managers_on_si(si) -> list[str]:
    out = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if sp and _is_sales_manager(sp):
            out.append(sp)
    return out

def _rest_on_si(si) -> list[str]:
    out = []
    for st in (si.get("sales_team") or []):
        sp = st.get("sales_person")
        if not sp: continue
        if not _is_sales_manager(sp):
            emp = frappe.db.get_value("Sales Person", sp, "employee")
            if emp:
                out.append(sp)
    return out

# --------------------------
# Compute (Sales engine)
# --------------------------

def compute_totals_quarterly(sheet):
    """
    SALES (Home/Hotspot):
      • Base: normal rate on whole amount, split by manager/rest (even split).
      • Above: add-on = full 'above' rate on the over-target slice per person
               (per invoice, in fully-paid order across the quarter).
      • No penalties in Sales.
    """
    q_start, q_end, months3 = get_quarter_window(sheet.fiscal_year, sheet.quarter)

    # Sales lines (people) & their quarter targets
    people = [ln.sales_person for ln in (sheet.get("commission_lines") or []) if ln.department == "Sales"]
    if len(people) == 0:
        return

    target = {sp: quarter_target_from_distribution(sp, sheet.fiscal_year, months3) for sp in people}

    # Candidate invoices sorted by fully-paid date (include prior-FY)
    cand = frappe.get_all(
        "Sales Invoice",
        filters={"company": sheet.company, "docstatus": 1, "posting_date": ["<=", q_end]},
        fields=["name"]
    )
    cand_sorted = []
    for inv in cand:
        po = get_invoice_fully_paid_on(inv["name"])
        if po and (q_start <= po <= q_end):
            cand_sorted.append((po, inv["name"]))
    cand_sorted.sort()

    # Running exposure (amount) per person to compute over-target slices
    cum_exposure = {sp: 0.0 for sp in people}
    # Outputs
    per_person   = {sp: 0.0 for sp in people}
    actual_basis = {sp: 0.0 for sp in people}

    for po, si_name in cand_sorted:
        si = frappe.get_doc("Sales Invoice", si_name)
        cat_amounts = _sales_category_amounts_for_si(si)
        mgrs = _managers_on_si(si)
        rest = _rest_on_si(si)

        for cat, amount in cat_amounts.items():
            rates  = SALES_RATES[cat]
            splits = SALES_SPLITS[cat]

            # Base commission (normal rate) split manager/rest
            base_mgr_comm  = amount * rates["normal"] * splits["normal"]["manager"]
            base_rest_comm = amount * rates["normal"] * splits["normal"]["rest"]

            if mgrs:
                eq = base_mgr_comm / len(mgrs)
                for sp in mgrs:
                    if sp in per_person:
                        per_person[sp] = per_person.get(sp, 0) + eq
            else:
                # reallocate manager base to rest
                if rest:
                    eq = base_mgr_comm / len(rest)
                    for sp in rest:
                        if sp in per_person:
                            per_person[sp] = per_person.get(sp, 0) + eq

            if rest:
                eq = base_rest_comm / len(rest)
                for sp in rest:
                    if sp in per_person:
                        per_person[sp] = per_person.get(sp, 0) + eq

            # Exposure slices (amount), used for Above add-on
            # Manager exposure share
            if mgrs:
                eq_mgr_amt = amount * splits["normal"]["manager"] / len(mgrs)
                for sp in mgrs:
                    if sp not in actual_basis:
                        continue
                    # exposure for actual / achievement reporting
                    actual_basis[sp] += eq_mgr_amt
                    # over-target slice
                    tgt  = target.get(sp, 0.0) or 0.0
                    prev = cum_exposure.get(sp, 0.0) or 0.0
                    above_part = max(0.0, (prev + eq_mgr_amt) - tgt) - max(0.0, prev - tgt)
                    if above_part > 0:
                        per_person[sp] = per_person.get(sp, 0) + above_part * rates["above"]
                    cum_exposure[sp] = prev + eq_mgr_amt
            else:
                # if no managers, manager exposure realloc to rest too
                if rest:
                    eq_amt = amount * splits["normal"]["manager"] / len(rest)
                    for sp in rest:
                        if sp in actual_basis:
                            actual_basis[sp] += eq_amt
                        tgt  = target.get(sp, 0.0) or 0.0
                        prev = cum_exposure.get(sp, 0.0) or 0.0
                        above_part = max(0.0, (prev + eq_amt) - tgt) - max(0.0, prev - tgt)
                        if above_part > 0:
                            per_person[sp] = per_person.get(sp, 0) + above_part * rates["above"]
                        cum_exposure[sp] = prev + eq_amt

            # Rest exposure share
            if rest:
                eq_rest_amt = amount * splits["normal"]["rest"] / len(rest)
                for sp in rest:
                    if sp in actual_basis:
                        actual_basis[sp] += eq_rest_amt
                    tgt  = target.get(sp, 0.0) or 0.0
                    prev = cum_exposure.get(sp, 0.0) or 0.0
                    above_part = max(0.0, (prev + eq_rest_amt) - tgt) - max(0.0, prev - tgt)
                    if above_part > 0:
                        per_person[sp] = per_person.get(sp, 0) + above_part * rates["above"]
                    cum_exposure[sp] = prev + eq_rest_amt

    # Update Sales lines on the sheet
    total_target = total_actual = total_commission = 0.0
    for ln in (sheet.get("commission_lines") or []):
        if ln.department != "Sales":
            continue
        ln.target_value = flt(target.get(ln.sales_person) or 0.0)
        ln.actual_sales = flt(actual_basis.get(ln.sales_person) or 0.0)
        ln.achievement_pct = round((ln.actual_sales / ln.target_value * 100.0), 2) if ln.target_value else 0.0
        ln.commission_value = flt(per_person.get(ln.sales_person) or 0.0)

        total_target    += flt(ln.target_value)
        total_actual    += flt(ln.actual_sales)
        total_commission+= flt(ln.commission_value)

    sheet.total_target = round(total_target, 2)
    sheet.total_actual_sales = round(total_actual, 2)
    sheet.total_commission = round(total_commission, 2)
