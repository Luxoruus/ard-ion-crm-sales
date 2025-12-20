
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from ...commission.compute import compute_totals

ALLOWED_STATES = {"Draft","Submitted","Approved"}

class SalesTargetandCommissionSheet(Document):
    def validate(self):
        if self.status in ALLOWED_STATES and self.docstatus in (0,1):
            compute_totals(self)

    def before_submit(self):
        if not self.get("commission_lines"):
            frappe.throw("Add at least one commission line.")
        for line in self.get("commission_lines"):
            if not flt(line.target_value):
                frappe.throw(f"Missing target for {line.sales_person}.")

    def on_update_after_submit(self):
        if self.status in ALLOWED_STATES:
            compute_totals(self)
