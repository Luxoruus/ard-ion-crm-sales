import frappe

def send_email(email, subject, message, doc):
	frappe.sendmail(
		recipients=email,
		subject=subject,
		message=message,
		reference_doctype="Issue",
		reference_name=doc
	)

@frappe.whitelist()
def new_issue_notification(doc, method):
	email_ids = doc.get("custom_email_ids_to_notify")
	for email_id in email_ids:
		send_email(email_id.email, f"New Issue - {doc.name}", f"A new issue ({doc.name}) has been created.", doc.name)

@frappe.whitelist()
def issue_status_update(doc, method):
	old = doc.get_doc_before_save()

	if not old:
		return

	if old.status == doc.status:
		return

	email_ids = doc.get("custom_email_ids_to_notify")
	for email_id in email_ids:
		send_email(email_id.email, f"New Updates on Issue {doc.name}", f"Issue ({doc.name}) has a status update. New status: {doc.status}", doc.name)
