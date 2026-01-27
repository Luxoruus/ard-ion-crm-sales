# Copyright (c) 2026, ard.ly and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})

    parent_dt = "Sales Target and Commission Sheet"
    child_dt = "Commission Lines"

    conditions = [
        "stcs.quarter = %(quarter)s",
        "stcs.fiscal_year = %(fiscal_year)s",
        "stcs.status = 'Posted'"
    ]

    child_sales_person = "sales_person"
    child_target = "target_value"
    child_actual = "actual_sales"

    query = f"""
            SELECT
                line.`{child_sales_person}` AS sales_person,
                COALESCE(line.`{child_target}`, 0) AS target,
                COALESCE(line.`{child_actual}`, 0) AS actual,
                (COALESCE(line.`{child_actual}`, 0) - COALESCE(line.`{child_target}`, 0)) AS difference
            FROM `tab{parent_dt}` stcs
            JOIN `tab{child_dt}` line
              ON line.parent = stcs.name
            WHERE {" AND ".join(conditions)} AND line.department = %(department)s
            ORDER BY line.`{child_sales_person}`
        """

    data = frappe.db.sql(query, filters, as_dict=True)

    columns = [
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Link", "options": "Sales Person",
         "width": 110},
        {"label": _("Target"), "fieldname": "target", "fieldtype": "Currency",
         "width": 160},
        {"label": _("Actual"), "fieldname": "actual", "fieldtype": "Currency",
         "width": 300},
        {"label": _("Difference"), "fieldname": "difference", "fieldtype": "Currency", "width": 120},
    ]
    return columns, data
