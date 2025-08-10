import frappe

@frappe.whitelist()
def handle_lead(doc, method):
    if(doc.source == 'RMT'):
        opp = frappe.new_doc("Opportunity")
        opp.opportunity_from = "Lead"
        opp.party_name = doc.name
        opp.insert()