
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


def send_subscription_expiry_alerts(
    window_days: int = 15,
    account_manager_field: str = "account_manager",
    return_results: bool = False
) -> list | None:
    """
    Robust scheduler-safe and dev-safe version.

    Sends email + in-app notifications (Notification Log)
    about subscriptions expiring within `window_days`.

    • Captures ALL failures in Error Log
    • Detects missing outgoing Email Account
    • Ensures no non-serializable objects are returned
    • Works with bench execute, bench schedule, and enqueue

    Returns:
        list if return_results=True, else None
    """

    # ------------------------------
    # 0) Ensure emails are not muted
    # ------------------------------
    if frappe.flags.get("mute_emails", None) is True:
        frappe.flags.mute_emails = False

    results = []
    start = today()
    end = add_days(start, window_days)

    # ------------------------------
    # 1) Check outgoing email account
    # ------------------------------
    outgoing_exists = bool(
        frappe.db.exists("Email Account", {"enable_outgoing": 1})
    )

    if not outgoing_exists:
        frappe.log_error(
            title="No Outgoing Email Account Configured",
            message=(
                "send_subscription_expiry_alerts: No outgoing email account found. "
                "Emails will NOT be sent or queued. Notifications will still be created."
            )
        )

    # ------------------------------
    # 2) Fetch subscriptions in range
    # ------------------------------
    subs = frappe.get_all(
        "Subscription",
        filters={"party_type": "Customer", "end_date": ["between", [start, end]]},
        fields=["name", "party", "end_date"]
    )

    # ------------------------------
    # 3) Process each subscription
    # ------------------------------
    for s in subs:
        row = {
            "subscription": s["name"],
            "customer": s["party"],
            "end_date": s["end_date"],
        }

        try:
            # 3a) Find account manager user
            am_user = frappe.db.get_value("Customer", s["party"], account_manager_field)
            row["am_user"] = am_user

            if not am_user or not frappe.db.exists("User", am_user):
                row["skipped"] = "invalid_or_missing_account_manager"
                results.append(row)
                continue

            # 3b) Get AM email
            am_email = frappe.db.get_value("User", am_user, "email")
            row["am_email"] = am_email

            if not am_email:
                row["skipped"] = "account_manager_missing_email"
                results.append(row)
                continue

            # 3c) Build subject + message
            days_left = date_diff(s["end_date"], start)
            subject = (
                f"[Expiry Alert] Subscription {s['name']} "
                f"ends on {s['end_date']}"
            )
            message = (
                f"Subscription: {s['name']}\n"
                f"Customer: {s['party']}\n"
                f"End Date: {s['end_date']}\n"
                f"Days to Expiry: {days_left}\n"
            )

            # 3d) Email (ONLY if outgoing account exists)
            if outgoing_exists:
                try:
                    q = frappe.sendmail(
                        recipients=[am_email],
                        sender = "d.jaziri@ard.ly",
                        subject=subject,
                        message=message,
                        delayed = True
                    )
                    row["email_queued"] = True
                    frappe.db.commit()  # Commit after sending email
                except Exception as mail_err:
                    row["email_error"] = str(mail_err)
                    frappe.log_error(
                        title="send_subscription_expiry_alerts: Email Failure",
                        message=f"{subject}\nError: {mail_err}"
                    )
                    # Continue to create notification even if mail fails
            else:
                row["email_queued"] = False
                row["email_skipped_no_outgoing"] = True

            # 3e) Notification Log (ALWAYS CREATED)
            try:
                nlog = frappe.get_doc({
                    "doctype": "Notification Log",
                    "for_user": am_user,
                    "type": "Alert",
                    "subject": subject,
                    "email_content": message,
                    "document_type": "Subscription",
                    "document_name": s["name"],
                }).insert(ignore_permissions=True)

                row["notification_log"] = nlog.name

            except Exception as nlog_err:
                row["notification_log_error"] = str(nlog_err)
                frappe.log_error(
                    title="send_subscription_expiry_alerts: Notification Log Failure",
                    message=f"Subscription={s['name']}\nError={nlog_err}"
                )

            results.append(row)

        except Exception as e:
            # 3f) Catch-all fail-safe
            frappe.log_error(
                title="send_subscription_expiry_alerts: Fatal Failure",
                message=f"Subscription={s['name']} Error={e}"
            )
            row["error"] = str(e)
            results.append(row)

    # ------------------------------
    # 4) Return results if requested
    # ------------------------------
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