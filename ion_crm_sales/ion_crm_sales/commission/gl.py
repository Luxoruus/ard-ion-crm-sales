
# -*- coding: utf-8 -*-
import frappe
from frappe.utils import today, flt


def _get_quarter(doc) -> str:
    q = getattr(doc, "custom_quarter", None) or getattr(doc, "quarter", None)
    if not q:
        frappe.throw("Quarter is missing on the sheet.")
    return q


def _validate_accounts(expense_acc, payable_acc, company):
    # if expense_acc == payable_acc:
    #     frappe.throw("Commission Expense and Commission Payable accounts must be different.")
    exp = frappe.get_doc("Account", expense_acc)
    pay = frappe.get_doc("Account", payable_acc)
    # if exp.is_group or pay.is_group:
    #     frappe.throw("Select leaf (ledger) accounts (not groups).")
    # if exp.root_type != "Expense":
    #     frappe.throw(f"Expense account '{expense_acc}' is not an Expense account.")
    # if pay.root_type != "Liability":
    #     frappe.throw(f"Payable account '{payable_acc}' is not a Liability account.")
    # if exp.company != company or pay.company != company:
    #     frappe.throw("Expense/Payable accounts must belong to the same Company as the sheet.")


def _settings_accounts():
    expense_acc = frappe.db.get_single_value("Commission Policy Settings", "expense_account")
    payable_acc = frappe.db.get_single_value("Commission Policy Settings", "payable_account")
    if not expense_acc or not payable_acc:
        frappe.throw("Set Expense and Payable accounts in Commission Policy Settings.")
    return expense_acc, payable_acc


def _ensure_single_posted_per_quarter(sheet):
    quarter = _get_quarter(sheet)
    conflict = frappe.get_all(
        "Sales Target and Commission Sheet",
        filters={
            "company": sheet.company,
            "fiscal_year": sheet.fiscal_year,
            "quarter": quarter,              # if your field is custom_quarter, add a property setter to map; or keep both
            "status": "Posted",
            "name": ["!=", sheet.name],
        },
        fields=["name", "accrual_je"],
        limit=1,
    )
    # If you store only custom_quarter in DB, also check it:
    if not conflict:
        conflict = frappe.get_all(
            "Sales Target and Commission Sheet",
            filters={
                "company": sheet.company,
                "fiscal_year": sheet.fiscal_year,
                "quarter": quarter,
                "status": "Posted",
                "name": ["!=", sheet.name],
            },
            fields=["name", "accrual_je"],
            limit=1,
        )
    if conflict:
        c = conflict[0]
        frappe.throw(
            f"A sheet for {sheet.company} {sheet.fiscal_year} {quarter} is already Posted "
            f"(Sheet: {c['name']}, JE: {c.get('accrual_je')})."
        )


def post_accrual(sheet):
    _ensure_single_posted_per_quarter(sheet)

    expense_acc, payable_acc = _settings_accounts()
    _validate_accounts(expense_acc, payable_acc, sheet.company)

    amount = flt(sheet.total_commission)
    if amount <= 0:
        frappe.throw("Commission total is zero; nothing to accrue.")

    q = _get_quarter(sheet)

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = today()
    je.company = sheet.company
    je.user_remark = f"Commission accrual for {sheet.company} {sheet.fiscal_year} {q} - sheet {sheet.name}"

    je.append("accounts", {"account": expense_acc, "debit_in_account_currency": amount})
    je.append("accounts", {"account": payable_acc, "credit_in_account_currency": amount})

    je.insert()
    je.submit()
    je.add_comment("Comment", text=f"Accrual posted from sheet {sheet.name}")

    sheet.accrual_posted_amount = amount
    sheet.accrual_je = je.name
    sheet.save()
