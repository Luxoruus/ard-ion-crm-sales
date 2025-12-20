import frappe
from .compute import compute_totals
from .gl import post_adjustment

def _fy_for_date(dt):
    res = frappe.db.sql("""
        SELECT name FROM `tabFiscal Year`
        WHERE %s BETWEEN year_start_date AND year_end_date
        LIMIT 1
    """, (dt,), as_dict=True)
    return res[0]["name"] if res else None

def _refresh_person_in_sheets(sales_person, company, fiscal_year):
    sheets = frappe.get_all("Sales Target and Commission Sheet",
        filters={"company": company, "fiscal_year": fiscal_year, "status": ["in", ["Draft","Submitted","Approved"]]},
        pluck="name"
    )
    for s in sheets:
        doc = frappe.get_doc("Sales Target and Commission Sheet", s)
        for line in doc.get("commission_lines") or []:
            if line.sales_person == sales_person:
                compute_totals(doc)
                doc.save()
                if doc.docstatus == 1 and doc.status == "Approved" and doc.accrual_je:
                    post_adjustment(doc)
                break

def on_sales_invoice_submit(doc, method):
    for st in doc.get("sales_team") or []:
        fy = _fy_for_date(doc.posting_date)
        _refresh_person_in_sheets(st.sales_person, doc.company, fy)

def on_sales_invoice_cancel(doc, method):
    for st in doc.get("sales_team") or []:
        fy = _fy_for_date(doc.posting_date)
        _refresh_person_in_sheets(st.sales_person, doc.company, fy)

def on_sales_invoice_update_after_submit(doc, method):
    for st in doc.get("sales_team") or []:
        fy = _fy_for_date(doc.posting_date)
        _refresh_person_in_sheets(st.sales_person, doc.company, fy)

def on_payment_entry_submit(doc, method):
    if doc.payment_type != "Receive":
        return
    for ref in doc.get("references") or []:
        if ref.reference_doctype == "Sales Invoice":
            inv = frappe.get_doc("Sales Invoice", ref.reference_name)
            for st in inv.get("sales_team") or []:
                fy = _fy_for_date(inv.posting_date)
                _refresh_person_in_sheets(st.sales_person, inv.company, fy)
