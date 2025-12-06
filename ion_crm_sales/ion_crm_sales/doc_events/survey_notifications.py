
# ion_crm_sales/ion_crm_sales/doc_events/survey_notifications.py

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
# Notification Log inserts the bell item and, based on user settings, sends emails for "Alert".
# It also publishes a realtime event so the bell indicator updates immediately.  [4](https://deepwiki.com/frappe/frappe/2.1-document-api)[5](https://docs.frappe.io/erpnext/user/manual/en/opportunity)

TABLE_FIELD = "custom_surveyors"        # child table field on parent doctypes
CHILD_DOCTYPE = "Technical Surveyor"    # child row doctype
SURVEYOR_FIELD = "surveyor"             # Link to User on child row
DEPARTMENT_FIELD = "department"         # department field on child row


def on_before_save(doc, method):
    """Find newly added rows in `custom_surveyors` and notify each assigned surveyor.

    Works for: Opportunity, Opportunity SM, Opportunity Hotels, Opportunity Tenders.
    """
    current_rows = doc.get(TABLE_FIELD) or []

    # Use Frappe's snapshot from the save lifecycle to compute a diff of child rows. [3](https://support.aakvatech.com/wiki/document-event-hooks-in-frappe)
    prev = doc.get_doc_before_save()
    if not prev:
        added_rows = current_rows[:]  # first save: all present rows are "added"
    else:
        previous_rows = prev.get(TABLE_FIELD) or []
        prev_names = {r.name for r in previous_rows}  # child row `name` is unique/stable
        added_rows = [r for r in current_rows if r.name not in prev_names]

    if not added_rows:
        return

    # One Notification Log per added row (keeps context granular).
    for row in added_rows:
        if row.doctype != CHILD_DOCTYPE:
            # Guard in case of custom changes to child doctype.
            continue

        user_id = row.get(SURVEYOR_FIELD)
        if not user_id:
            continue

        # Notification Log helper expects list of user **emails** (not user_ids). [4](https://deepwiki.com/frappe/frappe/2.1-document-api)
        recipient_email = _get_user_email(user_id)
        if not recipient_email:
            continue

        dept = row.get(DEPARTMENT_FIELD) or _("(No Department)")

        subject = _("Survey Assignment for {dept}").format(dept=dept)
        email_content = frappe.render_template(
            """
            <p>You have been assigned as <b>Surveyor</b> for a network survey.</p>
            <ul>
              <li><b>Opportunity:</b> {{ doc.doctype }} {{ doc.name }}</li>
              <li><b>Department:</b> {{ dept }}</li>
            </ul>
            <p>Please open the document for details and proceed.</p>
            """,
            {"doc": doc, "dept": dept},
        )

        notify_doc = {
            "type": "Alert",                  # allows email based on user preferences for Alerts [4](https://deepwiki.com/frappe/frappe/2.1-document-api)
            "subject": subject,
            "email_content": email_content,
            "document_type": doc.doctype,     # link back to the parent record in the bell/email
            "document_name": doc.name,
            "from_user": frappe.session.user, # the Survey Manager assigning
        }

        # Creates the bell notification and sends email if enabled (queued, safe in save cycle).
        enqueue_create_notification([recipient_email], notify_doc)  # [4](https://deepwiki.com/frappe/frappe/2.1-document-api)


def _get_user_email(user_id: str) -> str | None:
    """Return the user's email; fall back to user name if it looks like an email."""
    user = frappe.db.get_value("User", user_id, ["email", "name"], as_dict=True)
    if not user:
        return None
    if user.get("email"):
        return user["email"]
    # Many sites use email as User.name; fallback if it contains "@"
    if user.get("name") and "@" in user["name"]:
        return user["name"]
    return None
