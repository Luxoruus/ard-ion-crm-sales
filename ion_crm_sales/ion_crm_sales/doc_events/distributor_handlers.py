import frappe

def before_insert(doc, method):
    if not doc.get("distributor_codeid"):
        code = frappe.utils.generate_hash(length=12).upper()
        while frappe.db.exists("Distributor", {"distributor_codeid": code}):
            code = frappe.utils.generate_hash(length=12).upper()
        doc.distributor_codeid = code