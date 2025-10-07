# Copyright (c) 2025, ard.ly and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate
import json

class CommissionTransaction(Document):
	pass


@frappe.whitelist()
def create_commission_payment(source_docname, amount, beneficiaries):
    # 1. Fetch the source document for a complete data reference
    source_doc = frappe.get_doc('Commission Transaction', source_docname)

    # 2. Create a new document object for Commission Payment
    new_doc = frappe.new_doc('Commission Payment')

    # 3. Map fields from the source document to the new document

    # Linking the documents
    new_doc.commission_transaction = source_docname # Create a Link field in Commission Payment for Commission Transaction
    
    # Other important fields
    new_doc.date_of_payment = nowdate() # Set payment date to today
    new_doc.status = 'Draft' # Start as Draft

    for b in json.loads(beneficiaries):
        new_doc.append('beneficiaries', {
            'party': b['party'],
            'beneficiary': b['beneficiary'],
            'share': (float(amount) / len(beneficiaries)) if len(beneficiaries) > 0 else 0
        })

    try:
        source_doc.commission_status = 'Paid'
        source_doc.save()
        # 4. Save and insert the new document
        new_doc.insert(ignore_permissions=True)
        # Note: If Commission Payment has a naming series, insert will generate the name.
        frappe.db.commit()

        # 5. Return the name of the new document
        return new_doc.name

    except Exception as e:
        # Log the error and throw an exception to the user
        frappe.log_error(frappe.get_traceback(), 'Commission Payment Creation Error')
        frappe.throw(f"Could not create Commission Payment: {e}")
