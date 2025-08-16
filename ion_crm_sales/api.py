import frappe
from ion_crm_sales.technical_survey import load_template_fields


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
        opportunity.save()
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

    opportunity = frappe.get_doc(opportunity_data.get("doctype"), opportunity_data.get("opportunity"))

    if not opportunity:
        frappe.throw("Invalid Opportunity")
    
    opportunity.workflow_state = "Surveyed"


    opportunity.save(ignore_permissions=True)

    return {"status": "success", "message": "Survey submitted successfully"}