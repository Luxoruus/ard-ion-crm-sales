
# ion_crm_sales/ion_crm_sales/commission/gl.py
import frappe
from frappe.utils import today, flt

def _settings_accounts():
    expense_acc = frappe.db.get_single_value("Commission Policy Settings", "expense_account")
    payable_acc = frappe.db.get_single_value("Commission Policy Settings", "payable_account")
    if not expense_acc or not payable_acc:
        frappe.throw("Set Commission Expense and Payable accounts in Commission Policy Settings.")
    return expense_acc, payable_acc

def post_accrual(sheet):
    expense_acc, payable_acc = _settings_accounts()
    amount = flt(sheet.total_commission)
    if amount <= 0:
        frappe.throw("Commission total is zero; nothing to accrue.")

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = today()
    je.company = sheet.company
    je.user_remark = f"Commission accrual for sheet {sheet.name}"

    # DR expense
    je.append("accounts", {
        "account": expense_acc,
        "debit_in_account_currency": amount,
    })
    # CR payable
    je.append("accounts", {
        "account": payable_acc,
        "credit_in_account_currency": amount,
    })

    je.insert()
    je.submit()

    # Optional: leave a comment thread link
    je.add_comment("Comment", text=f"Accrual posted from Sales Target and Commission Sheet {sheet.name}")

    sheet.accrual_posted_amount = amount
    sheet.accrual_je = je.name
    sheet.save()

def post_adjustment(sheet):
    expense_acc, payable_acc = _settings_accounts()
    new_total = flt(sheet.total_commission)
    old_posted = flt(sheet.accrual_posted_amount or 0)
    delta = new_total - old_posted
    if abs(delta) < 0.005:
        return

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = today()
    je.company = sheet.company
    je.user_remark = f"Commission adjustment for sheet {sheet.name} (delta: {delta:.2f})"

    if delta > 0:
        # increase accrual
        je.append("accounts", {"account": expense_acc, "debit_in_account_currency": delta})
        je.append("accounts", {"account": payable_acc, "credit_in_account_currency": delta})
    else:
        # decrease accrual
        je.append("accounts", {"account": payable_acc, "debit_in_account_currency": abs(delta)})
        je.append("accounts", {"account": expense_acc, "credit_in_account_currency": abs(delta)})

    je.insert()
    je.submit()
    je.add_comment("Comment", text=f"Adjustment posted from Sales Target and Commission Sheet {sheet.name}")

    sheet.accrual_posted_amount = new_total
    sheet.save()
