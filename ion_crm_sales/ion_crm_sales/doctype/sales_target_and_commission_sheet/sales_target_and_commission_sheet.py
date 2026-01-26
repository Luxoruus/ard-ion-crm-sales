
# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import flt

# SALES engine (two-level absolute path because controller is outside /commission)
from ion_crm_sales.ion_crm_sales.commission.compute import (
    compute_totals_quarterly as compute_sales_quarterly,
    get_quarter_window,
    quarter_target_from_distribution,
)

# BA engine (two-level absolute)
from ion_crm_sales.ion_crm_sales.commission.ba import compute_ba_for_sheet



ALLOWED_STATES = {"Draft", "Submitted", "Approved"}


def _ensure_quarter_on(doc: Document) -> str:
    """
    Normalize doc.quarter so engines that expect 'quarter' keep working.
    Returns 'Q1'/'Q2'/'Q3'/'Q4'. Throws if missing.
    """
    q = getattr(doc, "custom_quarter", None) or getattr(doc, "quarter", None)
    if not q:
        frappe.throw("Please set Quarter (Q1/Q2/Q3/Q4) on the sheet.")
    # Also write back to doc.quarter so compute modules see it
    if getattr(doc, "quarter", None) != q:
        setattr(doc, "quarter", q)
    return q


class SalesTargetandCommissionSheet(Document):
    def validate(self):
        _ensure_quarter_on(self)

        # SALES engine (Home/Hotspot)
        compute_sales_quarterly(self)

        # BA engine
        self._compute_ba_lines()

        # Recompute parent totals in case BA updated them via lines
        self._retotal()

    def before_submit(self):
        if not self.get("commission_lines"):
            frappe.throw("Add at least one commission line.")

        # Ensure every line has a quarter target (Sales/BA)
        for ln in (self.get("commission_lines") or []):
            if not flt(ln.target_value):
                frappe.throw(f"Missing quarter target for {ln.sales_person} in {ln.department}. "
                             f"Make sure Sales Person Targets are entered and have a Monthly Distribution.")

    def on_update_after_submit(self):
        # Allow recompute while not Posted
        if self.status in ALLOWED_STATES:
            _ensure_quarter_on(self)
            compute_sales_quarterly(self)
            self._compute_ba_lines()
            self._retotal()

    # ---------- helpers ---------- #

    def _compute_ba_lines(self):
        """Fill BA lines using BA engine results; also fill BA quarter targets for visibility."""
        q_start, q_end, months3 = get_quarter_window(self.fiscal_year, _ensure_quarter_on(self))
        ba_map = compute_ba_for_sheet(self)  # {sales_person: commission_value}

        for ln in (self.get("commission_lines") or []):
            if ln.department != "Business Accounts":
                continue
            # Quarter target from distribution (BA)
            ln.target_value = quarter_target_from_distribution(ln.sales_person, self.fiscal_year, months3)
            # Commission (computed by BA engine)
            ln.commission_value = flt(ba_map.get(ln.sales_person) or 0.0)

    def _retotal(self):
        total_target = total_actual = total_commission = 0.0
        for ln in (self.get("commission_lines") or []):
            total_target += flt(ln.target_value)
            total_actual += flt(ln.actual_sales)
            total_commission += flt(ln.commission_value)
        self.total_target = round(total_target, 2)
        self.total_actual_sales = round(total_actual, 2)
        self.total_commission = round(total_commission, 2)
