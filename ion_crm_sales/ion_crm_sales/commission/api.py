
# -*- coding: utf-8 -*-
import frappe
from ion_crm_sales.ion_crm_sales.commission.compute import compute_totals_quarterly as compute_sales_quarterly
from ion_crm_sales.ion_crm_sales.commission.ba import compute_ba_for_sheet
from ion_crm_sales.ion_crm_sales.commission.gl import post_accrual


def _ensure_quarter_on(doc):
    q = getattr(doc, "custom_quarter", None) or getattr(doc, "quarter", None)
    if not q:
        frappe.throw("Please set Quarter (Q1/Q2/Q3/Q4) on the sheet.")
    if getattr(doc, "quarter", None) != q:
        setattr(doc, "quarter", q)
    return q


@frappe.whitelist()
def recalculate_sheet(name: str):
    doc = frappe.get_doc("Sales Target and Commission Sheet", name)
    if doc.docstatus == 2 or doc.status == "Posted":
        frappe.throw("Recalculation is not allowed on Cancelled or Posted sheets.")

    _ensure_quarter_on(doc)

    # SALES engine
    compute_sales_quarterly(doc)

    # BA engine
    _apply_ba(doc)

    doc.save()
    return {"message": "Recalculated."}


def _apply_ba(doc):
    ba_map = compute_ba_for_sheet(doc)
    for ln in (doc.get("commission_lines") or []):
        if ln.department == "Business Accounts":
            ln.commission_value = ba_map.get(ln.sales_person) or 0.0


@frappe.whitelist()
def post_sheet_accrual(name: str):
    doc = frappe.get_doc("Sales Target and Commission Sheet", name)
    if doc.docstatus != 1 or doc.status != "Approved":
        frappe.throw("Only Approved & Submitted sheets can be posted.")

    _ensure_quarter_on(doc)

    # Refresh numbers before posting
    compute_sales_quarterly(doc)
    _apply_ba(doc)
    doc.save()

    post_accrual(doc)  # sets accrual_je, accrual_posted_amount and changes status to Posted
    doc.status = "Posted"
    doc.save()
    return {"message": f"Accrual posted: {doc.accrual_je}"}
