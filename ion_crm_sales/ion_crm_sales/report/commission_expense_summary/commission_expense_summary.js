// Copyright (c) 2026, ard.ly and contributors
// For license information, please see license.txt

frappe.query_reports["Commission Expense Summary"] = {
	"filters": [

		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_default("company") || frappe.sys_defaults.company || ""
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			reqd: 1,
			// JS default (evaluated at runtime)
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "expense_account",
			label: "Expense Account",
			fieldtype: "Link",
			options: "Account",
			reqd: 0
		}

	],

	onload(report) {

		frappe.db
			.get_single_value("Commission Policy Settings", "expense_account")
			.then((val) => {
				if (val && !report.get_values().expense_account) {
					report.set_filter_value("expense_account", val);

					// If the report already auto-ran before this async call resolves,
					// refresh to re-run with the now-set filter.
					report.trigger_refresh();
				}
			});

	}
};
