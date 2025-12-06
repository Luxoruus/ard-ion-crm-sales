import frappe

def before_insert(doc, method):
    if not doc.get("distributor_codeid"):
        code = frappe.utils.generate_hash(length=12).upper()
        while frappe.db.exists("Distributor", {"distributor_codeid": code}):
            code = frappe.utils.generate_hash(length=12).upper()
        doc.distributor_codeid = code


def create_sales_partner_for_distributor(doc, method=None):
    if getattr(doc, "sales_partner", None):
        return

    partner_name = getattr(doc, "distributor_name", None) or doc.name

    existing_sp = frappe.db.get_value(
        "Sales Partner",
        {"partner_name": partner_name},
        "name"
    )
    if existing_sp:
        sp_name = existing_sp
    else:
        sp = frappe.new_doc("Sales Partner")
        sp.partner_name = partner_name
        sp.commission_rate = 1
        sp.territory = "All Territories"
        # Optional: set other fields your Sales Partner requires
        sp.insert(ignore_permissions=True)
        sp_name = sp.name

    frappe.db.set_value("Distributor", doc.name, "sales_partner", sp_name)
