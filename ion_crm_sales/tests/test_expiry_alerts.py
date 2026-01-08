
# apps/ion_crm_sales/ion_crm_sales/tests/test_expiry_alerts.py
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days

class TestExpiryAlerts(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        # Allow queuing emails in tests
        frappe.flags.mute_emails = False

        # Clean previous artefacts (optional but helpful)
        frappe.db.delete("Notification Log", {"document_type": "Subscription"})
        frappe.db.delete("Email Queue Recipient", {})
        frappe.db.delete("Email Queue", {})

    def test_alerts_queue_mail_and_log_on_existing_subscription(self):
        # 1) Pick any existing Subscription for Customer (no plan checks)
        sub_rows = frappe.get_all(
            "Subscription",
            filters={"party_type": "Customer"},
            fields=["name", "party", "end_date"],
            limit=1
        )
        if not sub_rows:
            self.skipTest("No existing Customer Subscriptions found in this DB.")

        sub = frappe.get_doc("Subscription", sub_rows[0]["name"])

        # 2) Ensure Customer has a valid Account Manager user w/ email
        cust = frappe.get_doc("Customer", sub.party)
        am_user = cust.get("account_manager")
        if not am_user or not frappe.db.exists("User", am_user):
            am = frappe.get_doc({
                "doctype": "User",
                "email": "am@example.com",
                "first_name": "AM",
                "user_type": "System User",
                "roles": [{"role": "System Manager"}],
                "send_welcome_email": 0
            }).insert(ignore_permissions=True)
            am_user = am.name
            cust.db_set("account_manager", am_user)
        if not frappe.db.get_value("User", am_user, "email"):
            frappe.db.set_value("User", am_user, "email", "am@example.com")

        # 3) Put the Subscription within the alert window (e.g., 10 days)
        original_end = sub.get("end_date")
        sub.db_set("end_date", add_days(today(), 5))  # within window

        try:
            # 4) Call the pure function and collect results
            from ion_crm_sales.notifications import send_subscription_expiry_alerts
            results = send_subscription_expiry_alerts(window_days=5, return_results=True)

            # 5) Assert result row for our Subscription (intent)
            mine = [r for r in results if r.get("subscription") == sub.name]
            self.assertTrue(mine, "Expected our Subscription in the processed results")
            self.assertTrue(mine[0].get("email_queued"), "Expected email_queued=True in result")
            self.assertTrue(mine[0].get("notification_log"), "Expected Notification Log name in result")

            # 6) Assert DB: Email Queue exists (select only safe columns)
            eq = frappe.get_all(
                "Email Queue",
                filters={
                    "reference_doctype": "Subscription",
                    "reference_name": sub.name,
                    "status": ["in", ["Not Sent", "Queued"]]  # DB values differ; this covers both
                },
                fields=["name"],
                limit=1
            )
            self.assertTrue(eq, "Expected Email Queue row for the alert")

            # 7) Assert DB: Recipient exists for AM email
            eqr = frappe.get_all(
                "Email Queue Recipient",
                filters={"parent": eq[0]["name"], "recipient": "am@example.com"},
                limit=1
            )
            self.assertTrue(eqr, "Expected Email Queue Recipient row for Account Manager")

            # 8) Assert DB: Notification Log exists
            nlog = frappe.get_all(
                "Notification Log",
                filters={"document_type": "Subscription", "document_name": sub.name},
                limit=1
            )
            self.assertTrue(nlog, "Expected Notification Log row")

        finally:
            # Restore original end_date
            if original_end:
                sub.db_set("end_date", original_end)
