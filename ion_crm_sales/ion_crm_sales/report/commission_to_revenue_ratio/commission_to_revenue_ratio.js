// Copyright (c) 2026, ard.ly and contributors
// For license information, please see license.txt

frappe.query_reports["Commission to Revenue Ratio"] = {
	filters: [
		{
			fieldname: 'company',
			label: 'Company',
			fieldtype: 'Link',
			options: 'Company',
			reqd: true,
			default: 'ION'
		},
		{
			fieldname: "quarter",
			label: __("Quarter"),
			fieldtype: "Select",
			reqd: 1,
			// Typical fiscal quarters. Adjust if you use custom quarters.
			options: "Q1\nQ2\nQ3\nQ4",
			// Default current quarter dynamically
			default: (function () {
				const m = parseInt(frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth(), 10) + 1;
				if (m >= 1 && m <= 3) return "Q1";
				if (m >= 4 && m <= 6) return "Q2";
				if (m >= 7 && m <= 9) return "Q3";
				return "Q4";
			})(),
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
			// Try to default to current fiscal year if available
			default: frappe.datetime.get_today().split("-")[0]
		},
	],
};
