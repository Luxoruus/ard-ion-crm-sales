
# -*- coding: utf-8 -*-
import frappe
from frappe.utils import getdate  # normalize dates safely


def _quarter_of_date(d, fy_name):
    """Return 'Q1'..'Q4' for date d within Fiscal Year fy_name."""
    d = getdate(d)

    fy = frappe.get_doc("Fiscal Year", fy_name)
    ysd = fy.year_start_date

    from datetime import timedelta
    def addm(dt, months):
        from calendar import monthrange
        y = dt.year + (dt.month - 1 + months) // 12
        m = (dt.month - 1 + months) % 12 + 1
        day = min(dt.day, monthrange(y, m)[1])
        from datetime import date
        return date(y, m, day)

    bounds = [
        (ysd,                 addm(ysd, 3) - timedelta(days=1), "Q1"),
        (addm(ysd, 3),        addm(ysd, 6) - timedelta(days=1), "Q2"),
        (addm(ysd, 6),        addm(ysd, 9) - timedelta(days=1), "Q3"),
        (addm(ysd, 9),        addm(ysd,12) - timedelta(days=1), "Q4"),
    ]
    for start, end, label in bounds:
        if start <= d <= end:
            return label
    return "Q1"


def _touch_related_sheets(doc, method=None):
    """
    Triggered from Sales Invoice / Payment Entry events.
    Finds Sheets for same Company + FY + Quarter and calls the API to recalc.
    """
    from .api import recalculate_sheet  # import here to avoid circulars

    company = getattr(doc, "company", None)
    posting_date = getattr(doc, "posting_date", None)
    if not company or not posting_date:
        return

    posting_date = getdate(posting_date)

    # Resolve fiscal year covering the document date
    fy = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", posting_date), "year_end_date": (">=", posting_date)},
        "name"
    )
    if not fy:
        return

    quarter = _quarter_of_date(posting_date, fy)

    # Only fetch existing, standard fields
    sheets = frappe.get_all(
        "Sales Target and Commission Sheet",
        filters={"company": company, "fiscal_year": fy, "status": ["in", ["Draft", "Submitted", "Approved"]]},
        fields=["name", "quarter"]   # <-- removed custom_quarter to avoid SELECT errors
    )

    for s in sheets:
        if s.get("quarter") != quarter:
            continue
        try:
            recalculate_sheet(name=s["name"])
        except Exception:
            frappe.log_error(
                f"ion_crm_sales: failed to auto-recalculate sheet {s['name']}",
                "Commission Trigger"
            )
