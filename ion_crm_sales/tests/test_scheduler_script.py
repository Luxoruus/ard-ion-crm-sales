import frappe
from frappe.tests.utils import FrappeTestCase
from ion_crm_sales.notifications import send_subscription_expiry_alerts

class TestSchedulerScript(FrappeTestCase):
    def test_script_execution(self):
        
        send_subscription_expiry_alerts(window_days=60)

        # Assert: check Notification Log or Email Queue entries as needed
        # logs = frappe.get_all("Notification Log", filters={"document_type": "Subscription", "document_name": sub.name})
        # self.assertTrue(len(logs) >= 1)
