import frappe

@frappe.whitelist()
def before_save(doc, method):
    if not doc.get_doc_before_save():
        return

    # source_doc = frappe.get_doc("Opportunity", doc)

    source_doc = doc

    if source_doc.get_doc_before_save().workflow_state != source_doc.workflow_state and source_doc.workflow_state == "Converted":
        target_doc = frappe.new_doc("Opportunity SM")

        # Get list of fields (excluding system fields)
        doctype_meta = frappe.get_meta("Opportunity SM")
        fields_to_copy = [f.fieldname for f in doctype_meta.fields if f.fieldtype not in ("Section Break", "Column Break")]
        for field in fields_to_copy:
            if hasattr(source_doc, field):
                if field == "workflow_state":
                    continue
                else:
                    setattr(target_doc, field, getattr(source_doc, field))

        try:
            target_doc.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            print(f"Error creating Opportunity SM: {str(e)}")
            print(f"Failed to create Opportunity SM: {str(e)}")

        target_doc.workflow_state = "Scoping"
        target_doc.save(ignore_permissions=True)

        frappe.msgprint(f"Opportunity SM created: {target_doc.name}")

        return target_doc.name

@frappe.whitelist()
def price_list_fetch(doc, items):

    frappe.msgprint('TEst')
    return
    if (doc.workflow_state in ['Surveyed', 'Approved', 'Accepted']):
        price_list = frappe.get_doc("Price List", 'Dedicated')
        