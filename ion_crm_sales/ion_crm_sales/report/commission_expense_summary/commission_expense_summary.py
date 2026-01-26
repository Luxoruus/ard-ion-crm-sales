
# -*- coding: utf-8 -*-
import frappe
from frappe import _

def execute(filters=None):
    """Script Report: Commission Expense Summary

    - Uses optional 'expense_account' filter (falls back to Single doctype)
    - Sums debit_in_account_currency grouped by posting_date, company, user_remark
    """
    filters = frappe._dict(filters or {})

# Server-side fallback: pull expense_account from Single doctype if user didn't provide it
    if not filters.get("expense_account"):
        filters.expense_account = frappe.db.get_single_value(
            "Commission Policy Settings", "expense_account"
        ) or ""

    # Required filters: company, from_date, to_date (enforced in Report filters)
    required = ("company", "from_date", "to_date")
    missing = [k for k in required if not filters.get(k)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))

    conditions = [
        "je.company = %(company)s",
        "je.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    # Optional filter: only add WHERE clause if present
    if filters.get("expense_account"):
        conditions.append("acc.account = %(expense_account)s")

    query = f"""
        SELECT
            je.posting_date,
            je.company,
            je.user_remark,
            SUM(acc.debit_in_account_currency) AS expense
        FROM `tabJournal Entry Account` acc
        JOIN `tabJournal Entry` je ON acc.parent = je.name
        WHERE {" AND ".join(conditions)}
        GROUP BY je.posting_date, je.company, je.user_remark
        ORDER BY je.posting_date
    """

    data = frappe.db.sql(query, filters, as_dict=True)

    columns = [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
        {"label": _("User Remark"), "fieldname": "user_remark", "fieldtype": "Small Text", "width": 300},
        {"label": _("Expense"), "fieldname": "expense", "fieldtype": "Currency", "width": 120},
    ]

    # You can also return (columns, data, message, chart, report_summary, report_chart)
    return columns, data
