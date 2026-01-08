
# ion_crm_sales/notifications.py
import frappe
from frappe.utils import today, add_days, date_diff

def push_subscription_expiry_alerts(window_days: int = 15,
                                    account_manager_field: str = "account_manager",
                                    return_results: bool = False):
    """
    Push-only alerts:
      - Create Notification Log rows for AM
      - Fire realtime 'show_notification' to AM (toast if online)
    No emails are sent.
    """
    start = today()
    end = add_days(start, window_days)
    results = []

    subs = frappe.get_all(
        "Subscription",
        filters={"party_type": "Customer", "end_date": ["between", [start, end]]},
        fields=["name", "party", "end_date"]
    )

    for s in subs:
        row = {"subscription": s["name"], "customer": s["party"], "end_date": s["end_date"]}
        try:
            am_user = frappe.db.get_value("Customer", s["party"], account_manager_field)
            if not am_user or not frappe.db.exists("User", am_user):
                row["skipped"] = "no_account_manager_user"
                results.append(row)
                continue

            days_left = date_diff(s["end_date"], start)
            subject = f"[Expiry Alert] Subscription {s['name']} ends on {s['end_date']}"
            message = (
                f"Subscription: {s['name']}\n"
                f"Customer: {s['party']}\n"
                f"End Date: {s['end_date']}\n"
                f"Days to Expiry: {days_left}\n"
            )

            # 1) Create bell notification (in-app)
            nlog = frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": am_user,
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": "Subscription",
                "document_name": s["name"],
            }).insert(ignore_permissions=True)

            # 2) Fire a realtime toast (if AM is online in Desk)
            #     'show_notification' is a standard event; message can be plain text or dict.
            frappe.publish_realtime(
                event="show_notification",
                message={"message": subject, "indicator": "orange"},
                user=am_user
            )

            row["notification_log"] = nlog.name
            row["pushed"] = True
            results.append(row)

        except Exception as e:
            frappe.log_error(
                title="push_subscription_expiry_alerts failure",
                message=f"Sub={s['name']} party={s['party']} error={e}"
            )
            row["error"] = str(e)
            results.append(row)

    return results if return_results else None


def send_subscription_expiry_alerts(window_days: int = 15,
                                    account_manager_field: str = "account_manager",
                                    return_results: bool = False) -> list | None:
    """
    Alert Account Managers about Customer subscriptions expiring within `window_days`.
    Creates Email Queue rows and Notification Log entries.
    Returns a list of results if return_results=True for test assertions.
    """
    # --- defensive: ensure tests can enqueue email ---
    if frappe.flags.get("mute_emails", None) is True:
        frappe.flags.mute_emails = False

    start = today()
    end = add_days(start, window_days)

    results = []

    # fetch subs that qualify
    subs = frappe.get_all(
        "Subscription",
        filters={"party_type": "Customer", "end_date": ["between", [start, end]]},
        fields=["name", "party", "end_date"]
    )

    for s in subs:
        row = {"subscription": s["name"], "customer": s["party"], "end_date": s["end_date"]}
        try:
            # resolve account manager (standard field on Customer)
            am_user = frappe.db.get_value("Customer", s["party"], account_manager_field)
            row["am_user"] = am_user
            
            print(am_user)

            if not am_user or not frappe.db.exists("User", am_user):
                row["skipped"] = "no_account_manager_user"
                results.append(row)
                continue

            am_email = frappe.db.get_value("User", am_user, "email")
            row["am_email"] = am_email
            if not am_email:
                row["skipped"] = "account_manager_has_no_email"
                results.append(row)
                continue

            days_left = date_diff(s["end_date"], start)
            subject = f"[Expiry Alert] Subscription {s['name']} ends on {s['end_date']}"
            message = (
                f"Subscription: {s['name']}\n"
                f"Customer: {s['party']}\n"
                f"End Date: {s['end_date']}\n"
                f"Days to Expiry: {days_left}\n"
            )

            # queue email (reference fields make DB assertions clean across versions)
            # frappe.sendmail(
            #     recipients=["Administrator"],
            #     subject=subject,
            #     message=message,
            # )
            
            from frappe.core.doctype.communication.email import make

            test_var = make(subject=subject, content=message, receipients=[am_email], send_email = True, sender = "d.jaziri@ard.ly")

            print(test_var, "Test Var -----------------")

            # create in-app notification (bell)
            nlog = frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": am_user,
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": "Subscription",
                "document_name": s["name"],
            }).insert(ignore_permissions=True)

            row["email_queued"] = True
            row["notification_log"] = nlog.name
            results.append(row)

        except Exception as e:
            # capture any silent failure into the Error Log so you can inspect it
            frappe.log_error(
                title="send_subscription_expiry_alerts failure",
                message=f"Sub={s['name']} party={s['party']} error={e}"
            )
            row["error"] = str(e)
            results.append(row)

    return results if return_results else None

def send_custom_system_notification(user_id, subject, message):
    # Create a new Notification Log entry (optional, but keeps a record)
    notification_log = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "from_user": frappe.session.user,
        "notification_type": "Alert", # Use "Alert" for the bell icon type
        "for_user": user_id,
        "content": message,
    })
    notification_log.insert(ignore_permissions=True)
    
    # Publish the event in real-time to the specific user's session
    frappe.publish_realtime(
        "notification",
        user=user_id,
        after_commit=True # Ensures notification is sent after the current transaction is committed
    )