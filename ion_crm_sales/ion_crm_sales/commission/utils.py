
import frappe
from frappe.utils import flt

def get_fy_dates(fiscal_year):
    fy = frappe.get_doc("Fiscal Year", fiscal_year)
    return fy.year_start_date, fy.year_end_date

def _excluded_item_groups():
    csv = (frappe.db.get_single_value("Commission Policy Settings", "exclude_item_groups") or "").strip()
    return [g.strip() for g in csv.split(",") if g.strip()]

def _is_paid(inv):
    return flt(inv.get("outstanding_amount") or 0) == 0

def _commissionable_base(inv, exclude_taxes_shipping=True, excluded_groups=None):
    if not exclude_taxes_shipping:
        return flt(inv.get("base_grand_total") or 0)
    total = 0.0
    items = frappe.get_all("Sales Invoice Item",
                           filters={"parent": inv["name"]},
                           fields=["item_group", "base_amount"])
    for it in items:
        if excluded_groups and it["item_group"] in excluded_groups:
            continue
        total += flt(it["base_amount"] or 0)
    return total

def actual_sales_for_person(sales_person, company, fiscal_year):
    ps = frappe.get_single("Commission Policy Settings")
    start_date, end_date = get_fy_dates(fiscal_year)
    excluded_groups = _excluded_item_groups() if ps.exclude_item_groups else []

    invoices = frappe.get_all("Sales Invoice",
        filters={"company": company, "docstatus": 1, "posting_date": ["between", [start_date, end_date]]},
        fields=["name", "outstanding_amount", "base_grand_total"]
    )

    total = 0.0
    for inv in invoices:
        st = frappe.get_all("Sales Team",
            filters={"parenttype":"Sales Invoice","parent":inv["name"],"sales_person":sales_person},
            fields=["allocated_percentage"]
        )
        if not st:
            continue
        if ps.count_paid_only and not _is_paid(inv):
            continue

        base = _commissionable_base(inv, exclude_taxes_shipping=bool(ps.exclude_taxes_shipping), excluded_groups=excluded_groups)
        alloc = flt(st[0].get("allocated_percentage") or 100.0) if ps.apportion_by_sales_team else 100.0
        total += base * alloc / 100.0

    if ps.include_returns:
        returns = frappe.get_all("Sales Invoice",
            filters={"company": company, "docstatus": 1, "is_return": 1, "posting_date": ["between", [start_date, end_date]]},
            fields=["name", "base_grand_total"]
        )
        for cn in returns:
            st = frappe.get_all("Sales Team",
                filters={"parenttype":"Sales Invoice","parent":cn["name"],"sales_person":sales_person},
                fields=["allocated_percentage"]
            )
            if not st:
                continue
            base = _commissionable_base(cn, exclude_taxes_shipping=bool(ps.exclude_taxes_shipping), excluded_groups=excluded_groups)
            alloc = flt(st[0].get("allocated_percentage") or 100.0) if ps.apportion_by_sales_team else 100.0
            total -= base * alloc / 100.0

    return round(total, 2)