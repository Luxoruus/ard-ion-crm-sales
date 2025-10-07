import frappe

def validate(doc, method):
    # Custom logic to execute when a Subscription is submitted
    frappe.msgprint(f"Subscription {doc.subscription} has been submitted.")
        