import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def create_issue(source_name, target_doc=None):
	def set_missing_values(source, target):
		pass

	doclist = get_mapped_doc(
		frappe.flags.args.issue_from_dt,
		source_name,
		{
			frappe.flags.args.issue_from_dt: {
				"doctype": "Issue",
				"field_map": {"party_name": "customer"},
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist
