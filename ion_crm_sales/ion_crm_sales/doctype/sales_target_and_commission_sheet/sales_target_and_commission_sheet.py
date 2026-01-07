
import frappe
from frappe.model.document import Document
from frappe.utils import flt

# Import at module level (no imports inside methods)
from ...commission import compute as commission_compute
from ...commission.gl import post_accrual

ALLOWED_STATES = {"Draft", "Submitted", "Approved"}

def _state(doc) -> str:
    """Read current state from 'status' (workflow override) or fallback to 'workflow_state'."""
    return (getattr(doc, "status", None) or getattr(doc, "workflow_state", None) or "").strip()

class SalesTargetandCommissionSheet(Document):
    def validate(self):
        # Recompute when editable/allowed states
        if _state(self) in ALLOWED_STATES and self.docstatus in (0, 1):
            commission_compute.compute_totals(self)

    def before_submit(self):
        # Basic checks before submission
        if not self.get("commission_lines"):
            frappe.throw("Add at least one commission line.")
        for line in self.get("commission_lines"):
            if not flt(line.target_value):
                frappe.throw(f"Missing target for {line.sales_person}.")

    def on_update_after_submit(self):
        """
        - Recompute while Submitted/Approved (per BRD).
        - If the document reaches 'Posted' via workflow, auto-create accrual JE
          so we don't end up Posted without accounting.
        """
        current_state = _state(self)

        if current_state in ALLOWED_STATES:
            commission_compute.compute_totals(self)

        # Auto-post accrual if just moved to Posted and no JE exists yet
        if current_state == "Posted" and self.docstatus == 1 and not self.accrual_je:
            commission_compute.compute_totals(self)  # safety recompute
            post_accrual(self)
            # post_accrual sets accrual_je and accrual_posted_amount
