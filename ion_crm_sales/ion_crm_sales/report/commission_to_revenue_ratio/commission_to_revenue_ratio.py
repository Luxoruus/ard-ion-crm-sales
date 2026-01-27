# Copyright (c) 2026, ard.ly and contributors
# For license information, please see license.txt

import frappe

from frappe import _


def execute(filters=None):

	filters = frappe._dict(filters or {})

	required = ["quarter", "fiscal_year", "company"]
	missing = [k for k in required if not filters.get(k)]
	if missing:
		frappe.throw(_("Missing required filter(s): {0}").format(", ".join(missing)))

	conditions = [
		"stcs.quarter = %(quarter)s",
		"stcs.fiscal_year = %(fiscal_year)s",
		"stcs.company = %(company)s",
	]

	query = f"""
		SELECT
			stcs.total_actual_sales,
			stcs.total_commission
		FROM `tabSales Target and Commission Sheet` stcs
		WHERE {" AND ".join(conditions)}
	"""

	data = frappe.db.sql(query, filters, as_dict=True)
	columns = [
		{"label": _("Total Actual Sales"), "fieldname": "total_actual_sales", "fieldtype": "Currency",
		 "width": 110},
		{"label": _("Total Commission"), "fieldname": "total_commission", "fieldtype": "Currency", "width": 160},
		{"label": _("Ratio"), "fieldname": "ratio", "fieldtype": "Percent",
		 "width": 300},
	]
	return columns, data
