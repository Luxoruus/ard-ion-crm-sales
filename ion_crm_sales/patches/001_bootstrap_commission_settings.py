
import frappe

def execute():
    try:
        frappe.get_doc("Commission Policy Settings")
    except frappe.DoesNotExistError:
        frappe.get_doc({"doctype":"Commission Policy Settings"}).insert(ignore_permissions=True)
    settings = frappe.get_single("Commission Policy Settings")
    if not settings.rate_above_140:
        settings.rate_above_140 = 7
        settings.save()
