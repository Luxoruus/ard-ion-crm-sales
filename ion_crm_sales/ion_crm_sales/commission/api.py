import frappe
from .compute import compute_totals
from .gl import post_accrual, post_adjustment

@frappe.whitelist()
def recalculate_sheet(name: str):
    doc = frappe.get_doc("Sales Target and Commission Sheet", name)
    if doc.docstatus == 2 or doc.status == "Posted":
        frappe.throw("Recalculation is not allowed on Cancelled or Posted sheets.")
    compute_totals(doc)
    doc.save()
    if doc.docstatus == 1 and doc.status == "Approved" and doc.accrual_je:
        post_adjustment(doc)
    return {"message": "Recalculated."}

@frappe.whitelist()
def post_sheet_accrual(name: str):
    doc = frappe.get_doc("Sales Target and Commission Sheet", name)
    if doc.docstatus != 1 or doc.status != "Approved":
        frappe.throw("Only Approved & Submitted sheets can be posted.")
    compute_totals(doc)
    doc.save()
    post_accrual(doc)
    doc.status = "Posted"
    doc.save()
    return {"message": f"Accrual posted: {doc.accrual_je}"}
