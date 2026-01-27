# -*- coding: utf-8 -*-
import frappe
from frappe import _

def execute(filters=None):
    """Accrued Commission Payable (Journal Entry–based)

    - Increases to payable = credits on Commission Payable account
    - Decreases to payable = debits on Commission Payable account
    - Optional: show Commission Expense (debits on expense account) for reference
    - Grouped by posting_date, company, user_remark
    - Shows opening & closing balance for the payable account in report_summary
    """
    filters = frappe._dict(filters or {})

    # ---- Pull defaults from Single doctype (if not provided via UI) ----
    # Adjust these field names if your Single doctype differs
    if not filters.get("payable_account"):
        filters.payable_account = (
            frappe.db.get_single_value("Commission Policy Settings", "payable_account")
            or frappe.db.get_single_value("Commission Policy Settings", "commission_payable_account")
            or ""
        )
    if not filters.get("expense_account"):
        filters.expense_account = (
            frappe.db.get_single_value("Commission Policy Settings", "expense_account")
            or frappe.db.get_single_value("Commission Policy Settings", "commission_expense_account")
            or ""
        )

    # ---- Required filters ----
    required = ("company", "from_date", "to_date")
    missing = [k for k in required if not filters.get(k)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))

    # Payable account is essential for this report
    if not filters.get("payable_account"):
        frappe.throw(_("Please set a Payable Account (either in filters or in Commission Policy Settings)."))

    # ---- Base conditions ----
    conditions = [
        "je.docstatus = 1",
        "je.company = %(company)s",
        "je.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    # Restrict to the accounts we care about for performance
    account_clauses = ["acc.account = %(payable_account)s"]
    if filters.get("expense_account"):
        account_clauses.append("acc.account = %(expense_account)s")
    conditions.append("(" + " OR ".join(account_clauses) + ")")

    # Optional: filter by text found in user_remark (e.g., salesperson name/code)
    if filters.get("sales_person_text"):
        filters.sales_person_like = f"%{filters.sales_person_text}%"
        conditions.append("je.user_remark LIKE %(sales_person_like)s")

    # ---- Main query: aggregate by posting_date, company, user_remark ----
    query = f"""
        SELECT
            je.posting_date,
            je.company,
            je.user_remark,
            /* Info columns (account-currency) */
            SUM(CASE WHEN acc.account = %(expense_account)s
                     THEN acc.debit_in_account_currency ELSE 0 END) AS commission_expense,
            SUM(CASE WHEN acc.account = %(payable_account)s
                     THEN acc.credit_in_account_currency ELSE 0 END) AS accrued_credit,
            SUM(CASE WHEN acc.account = %(payable_account)s
                     THEN acc.debit_in_account_currency ELSE 0 END) AS settled_debit
        FROM `tabJournal Entry Account` acc
        JOIN `tabJournal Entry` je ON acc.parent = je.name
        WHERE {" AND ".join(conditions)}
        GROUP BY je.posting_date, je.company, je.user_remark
        ORDER BY je.posting_date, je.company, je.user_remark
    """

    data = frappe.db.sql(query, filters, as_dict=True) or []

    # Post-process: compute net change for the period
    total_change = 0
    total_expense = 0
    for row in data:
        expense = row.get("commission_expense") or 0
        accrued = row.get("accrued_credit") or 0  # liability increases via credit
        settled = row.get("settled_debit") or 0   # liability decreases via debit
        row["commission_payable_change"] = accrued - settled
        total_change += row["commission_payable_change"]
        total_expense += expense

    # ---- Opening & Closing balance on payable account (company-level) ----
    opening_sql = """
        SELECT
            IFNULL(SUM(acc.credit_in_account_currency - acc.debit_in_account_currency), 0) AS opening
        FROM `tabJournal Entry Account` acc
        JOIN `tabJournal Entry` je ON acc.parent = je.name
        WHERE
            je.docstatus = 1
            AND je.company = %(company)s
            AND je.posting_date < %(from_date)s
            AND acc.account = %(payable_account)s
    """
    opening = frappe.db.sql(opening_sql, filters, as_dict=True)[0]["opening"] if filters.get("from_date") else 0
    closing = opening + total_change

    # ---- Columns ----
    columns = [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
        # We reuse user_remark as the 'dimension' (e.g., Sales Person text) like your earlier report
        {"label": _("Remark"), "fieldname": "user_remark", "fieldtype": "Small Text", "width": 220},
        {"label": _("Commission Expense (Dr)"), "fieldname": "commission_expense", "fieldtype": "Currency", "width": 160},
        {"label": _("Accrued to Payable (Cr)"), "fieldname": "accrued_credit", "fieldtype": "Currency", "width": 160},
        {"label": _("Settled from Payable (Dr)"), "fieldname": "settled_debit", "fieldtype": "Currency", "width": 160},
        {"label": _("Net Change in Payable"), "fieldname": "commission_payable_change", "fieldtype": "Currency", "width": 170},
    ]

    # ---- Summary (shown at the top of the report) ----
    report_summary = [
        {"label": _("Opening Balance (Payable)"), "value": opening, "indicator": "blue"},
        {"label": _("Net Change (Period)"), "value": total_change, "indicator": "orange"},
        {"label": _("Closing Balance (Payable)"), "value": closing, "indicator": "green"},
    ]
    # Include total expense if expense_account is set
    if filters.get("expense_account"):
        report_summary.insert(1, {"label": _("Total Commission Expense"), "value": total_expense, "indicator": "gray"})

    # You can also return chart/report_chart later if you want
    return columns, data, None, None, report_summary, None
