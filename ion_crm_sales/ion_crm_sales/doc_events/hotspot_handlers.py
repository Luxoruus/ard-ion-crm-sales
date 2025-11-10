import frappe

@frappe.whitelist()
def before_save(doc, method):
    if not doc.get_doc_before_save():
        return
    
    if doc.workflow_state in ["Setup", "Active"]:
        items = doc.maintenance_log
        for item in items:
            if not item.get("notified"):  # Custom flag to avoid duplicate emails
                agent = item.get("agent")
                if agent:
                    user = frappe.get_doc("User", agent)
                    frappe.sendmail(
                        recipients=[user.email],
                        subject="New Maintenance Assigned",
                        message=f"A new Maintenance Item has been added and assigned to you in Maintenance Log: <b>{doc.name}</b>."
                    )
                    item.notified = 1  # Set flag to avoid resending

    if not doc.workflow_state == "Surveying":
        return

    # Create Price List with the name of the Hotspot if it doesn't exist
    price_list_name = doc.name
    if not frappe.db.exists("Price List", price_list_name):
        price_list = frappe.new_doc("Price List")
        price_list.price_list_name = price_list_name
        price_list.enabled = 1
        price_list.selling = 1
        price_list.buying = 0
        price_list.currency = doc.get("currency") or frappe.defaults.get_user_default("currency") or "USD"
        price_list.insert(ignore_permissions=True)
    else:
        price_list = frappe.get_doc("Price List", price_list_name)

    # Add items from Hotspot items table to Item Price
    for item_row in doc.get("items", []):
        item_code = item_row.get("item")
        if not item_code:
            continue
        # Check if Item Price already exists for this item and price list
        if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list_name}):
            item_price = frappe.new_doc("Item Price")
            item_price.item_code = item_code
            item_price.price_list = price_list_name
            item_price.price_list_rate = item_row.get("rate") or 0
            item_price.currency = price_list.currency
            item_price.uom = item_row.get("uom") or None
            item_price.valid_from = frappe.utils.nowdate()
            item_price.insert(ignore_permissions=True)
    
    
