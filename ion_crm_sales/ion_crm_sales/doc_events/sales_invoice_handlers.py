import frappe

COMMISSION_MODIFIERS = {
    "Old Accounts": 0.0075,
    "Lead Acquisition": 0.01,
    "Upsell": 0.02,
    "Above Target": 0.06
}

def on_submit(doc, method):
    if (doc.subscription):
        subscription = frappe.get_doc("Subscription", doc.subscription)
        grand_total = doc.grand_total
        comtr = frappe.new_doc("Commission Transaction")

        beneficiaries = []

        for d in subscription.custom_parties:
            beneficiaries.append({
                "party": d.party,
                "beneficiary": d.person,
            })

        comtr.update({
            "amount": grand_total * COMMISSION_MODIFIERS.get(subscription.custom_type, 0),
            "invoice": doc.name,
            "invoice_status": doc.status,
            "commission_status": "Unpaid",
            "beneficiaries": beneficiaries,
            "percentage": COMMISSION_MODIFIERS.get(subscription.custom_type, 0) * 100
        })
        

        comtr.save()

def on_change(doc, method):
    print("#############################")
    print("#############################")
    print("#############################")
    print("#############################")
    print("#############################")
    print(doc.status)
    print("#############################")
    print("#############################")
    print("#############################")
    print("#############################")
    print("#############################")
    print("#############################")

    if (not doc.has_value_changed("status")):
        return
    
    if (doc.subscription):
        comtr_name = frappe.get_value("Commission Transaction", {"invoice": doc.name}, "name")
        if comtr_name:
            comtr = frappe.get_doc("Commission Transaction", comtr_name)
            comtr.invoice_status = doc.status
            comtr.save()