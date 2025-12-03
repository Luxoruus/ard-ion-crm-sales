import frappe
from ion_crm_sales.ion_crm_sales import doctype
from ion_crm_sales.technical_survey import load_template_fields

@frappe.whitelist()
def bookings(data):
    if (len(data.get("client_national_id")) < 12): 
        return


    customer = None

    if (frappe.db.exists("Customer", data.get("client_name"))):
        customer = frappe.get_doc("Customer", data.get("client_name"))
    else:
        customer = frappe.get_doc({
            "doctype" : "Customer",
            "customer_type" : "Individual",
            "customer_name": data.get("client_name")
        })
        customer.insert(ignore_permissions=True)
            

    # customer.customer_name = data.get("client_name")
    # customer.customer_type = "Individual"

    doc = frappe.new_doc("Booking")
    doc.booking_id = "RMT-20250710-0009"
    doc.client_name = customer.customer_name
    doc.client_national_id = data.get("client_national_id")
    doc.client_phone = data.get("client_phone")
    doc.location = data.get("location")
    doc.package_id = data.get("package_id")
    doc.package_price = data.get("package_price")
    doc.payment_method = data.get("payment_method")
    doc.payment_amount = data.get("payment_amount")
    doc.distributor_id = data.get("distributor_id")
    doc.status = "Pending"

    doc.distributor_commission = float(frappe.get_doc('Sales Partner', data.get("distributor_id")).commission_rate) * float(data.get("package_price"))


    if (data.get("payment_amount") > data.get("package_price")):
        doc.client_credit = data.get("payment_amount") - data.get("package_price")

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def bookings_confirm(data):
    doc = frappe.get_doc("Booking", {"booking_id": data.get("booking_id")})
    doc.status = "Confirmed"
    doc.contract_number = data.get("contract_number")
    doc.confirmed_at = frappe.utils.now()
    doc.payment_status = "Received"
    doc.save(ignore_permissions=True)

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": doc.client_name,
        "posting_date": frappe.utils.nowdate(),
        "due_date": frappe.utils.nowdate(),
        "items": [
            {
                "item_code": doc.package_id,
                "rate": doc.package_price,
                "qty": 1
            }
        ],
        # "booking_reference": doc.name
    })

    invoice.insert(ignore_permissions=True)
    invoice.submit()

    payment = frappe.new_doc("Payment Entry")
    payment.payment_type = "Receive"
    payment.party_type = "Customer"
    payment.party = doc.client_name
    payment.posting_date = frappe.utils.nowdate()
    payment.paid_amount = doc.payment_amount
    payment.received_amount = doc.payment_amount
    payment.target_exchange_rate = 1
    payment.source_exchange_rate = 1
    payment.mode_of_payment = doc.payment_method
    payment.paid_to = frappe.db.get_value(
        "Account",
        {"company": invoice.company, "account_type": "Bank"},
        "name"
    )

    payment.paid_to_account_currency = "LYD"
    payment.company = invoice.company

    payment.append("references", {
    "reference_doctype": "Sales Invoice",
    "reference_name": invoice.name,
    })


    payment.set_missing_values()
    # payment.set_party_account_and_balance()
    payment.set_amounts()


    payment.insert(ignore_permissions=True)
    payment.submit()

@frappe.whitelist()
def bookings_cancel(data):
    doc = frappe.get_doc("Booking", {"booking_id": data.get("booking_id")})

    if doc.status == "Pending":
        doc.status = "Cancelled"
        doc.reason = data.get("reason")
        doc.cancelled_at = frappe.utils.now()
    elif doc.status == "Confirmed":
        doc.status = "Failed"
        doc.reason = data.get("reason")
        doc.cancelled_at = frappe.utils.now()
        doc.refund_amount = data.get("refund_amount")
    
    doc.save(ignore_permissions=True)


def create_credit_note_programmatically(sales_invoice_name):
    # Fetch the original Sales Invoice
    original_sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

    # Create a new Sales Invoice document for the Credit Note
    credit_note = frappe.new_doc("Sales Invoice")

    # Set relevant fields from the original invoice
    credit_note.customer = original_sales_invoice.customer
    credit_note.customer_name = original_sales_invoice.customer_name
    credit_note.company = original_sales_invoice.company
    credit_note.posting_date = frappe.utils.today() # Or a specific date
    credit_note.due_date = frappe.utils.today() # Or a specific date

    # Indicate it's a return/credit note
    credit_note.is_return = 1 
    credit_note.return_against = original_sales_invoice.name

    # Add items to the credit note (with negative quantities)
    for item in original_sales_invoice.items:
        credit_note.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": -item.qty,  # Negative quantity for credit note
            "rate": item.rate,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "base_amount": -item.base_amount,
            "amount": -item.amount
        })

    # Save and Submit the Credit Note
    try:
        credit_note.insert()
        credit_note.submit()
        frappe.msgprint(f"Credit Note {credit_note.name} created and submitted successfully.")
        return credit_note.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating Credit Note")
        frappe.msgprint(f"Error creating Credit Note: {e}")
        return None


@frappe.whitelist()
def bookings_get(booking_id):
    doc = frappe.get_doc("Booking", booking_id)
    return doc.as_dict()

@frappe.whitelist()
def save_survey(survey_data):
    # Validate and process the survey data
    if not survey_data.get("opportunity"):
        frappe.throw("Opportunity is required")
    if not survey_data.get("template"):
        frappe.throw("Template is required")
    if not survey_data.get("answers"):
        frappe.throw("Answers are required")

    doctype = survey_data.get("doctype", "Opportunity")
    custom_survey_field = survey_data.get("custom_survey_field", "custom_technical_survey")

    opportunity = frappe.get_doc(doctype, survey_data.get("opportunity"))

    survey = None
    survey_link = getattr(opportunity, custom_survey_field, None)

    if not survey_link:
        survey = frappe.new_doc("Technical Survey")
        survey.title = "Test Survey"
        survey.survey_template = survey_data.get("template")
        survey.save()
        survey.reload()
        load_template_fields(survey_data.get("template"), survey.name)
        survey.reload()
        setattr(opportunity, custom_survey_field, survey.name)
        opportunity.save(ignore_permissions=True)
    else:
        survey = frappe.get_doc("Technical Survey", survey_link)

    for field in survey.survey_fields:
        field.field_value = str(survey_data.get('answers').get(field.field_name))

    survey.save()
    return {"status": "success", "message": "Survey submitted successfully"}

@frappe.whitelist()
def submit_survey(opportunity_data):

    # Validate and process the opportunity data
    if not opportunity_data.get("opportunity"):
        frappe.throw("Opportunity is required")

    if not opportunity_data.get("doctype"):
        frappe.throw("Document Type is required")

    # Save the survey answers before submitting
    from ion_crm_sales.api import save_survey
    save_survey({
        "opportunity": opportunity_data.get("opportunity"),
        "template": opportunity_data.get("template"),
        "answers": opportunity_data.get("answers"),
        "doctype": opportunity_data.get("doctype"),
        "custom_survey_field": opportunity_data.get("custom_survey_field")
    })

    opportunity = frappe.get_doc(opportunity_data.get("doctype"), opportunity_data.get("opportunity"))

    if not opportunity:
        frappe.throw("Invalid Opportunity")
    
    opportunity.workflow_state = "Surveyed"
    opportunity.save(ignore_permissions=True)
    return {"status": "success", "message": "Survey submitted and saved successfully"}