import frappe
import requests

RMT_API_URL = ""
API_KEY = ""

def fetch_rmt_opportunities():
    response = requests.get(RMT_API_URL, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()
    return response.json()

def create_opportunity(data):
    doc = frappe.new_doc("Opportunity")
    doc.opportunity_from = "Customer"
    doc.party_name = data["customer_name"]
    doc.title = data["title"]
    doc.items = [{"item_code": item["item_code"], "qty": item["qty"], "item_name": item["item_name"], "rate": item["rate"], "amount": item["amount"]} for item in data.get("items", [])]
    doc.source = "RMT"

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

def sync_rmt_opportunities():
    opportunities = fetch_rmt_opportunities()
    for opp in opportunities:
        if not frappe.db.exists("Opportunity", {"title": opp["title"]}):
            create_opportunity(opp)