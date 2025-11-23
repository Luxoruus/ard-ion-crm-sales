import frappe
from ion_crm_sales.ion_crm_sales import doctype
from ion_crm_sales.technical_survey import load_template_fields

@frappe.whitelist()
def bookings(data):
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
    doc.booking_id = "RMT-20250710-0001"
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

    doc.distributor_commission = frappe.get_doc('Sales Partner', data.get("distributor_id")).commission_rate


    if (data.get("payment_amount") > data.get("package_price")):
        doc.client_credit = data.get("payment_amount") - data.get("package_price")

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def bookings_confirm(data):
    doc = frappe.get_doc("Booking", {"booking_id": data.get("booking_id")})
    doc.status = "Confirmed"
    doc.contract_number = data.get("contract_number")
    doc.confirmed_at = data.get("confirmed_at")
    doc.save(ignore_permissions=True)

@frappe.whitelist()
def bookings_cancel(data):
    doc = frappe.get_doc("Booking", {"booking_id": data.get("booking_id")})

    if doc.status == "Pending":
        doc.status = "Cancelled"
        doc.reason = data.get("reason")
        doc.cancelled_at = data.get("cancelled_at")
    elif doc.status == "Confirmed":
        doc.status = "Failed"
        doc.reason = data.get("reason")
        doc.cancelled_at = data.get("cancelled_at")
        doc.refund_amount = data.get("refund_amount")
    
    doc.save(ignore_permissions=True)

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