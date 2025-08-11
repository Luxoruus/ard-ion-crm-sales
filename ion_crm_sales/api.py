import frappe
from ion_crm_sales.technical_survey import load_template_fields


@frappe.whitelist()
def submit_survey(survey_data):
    # Validate and process the survey data
    if not survey_data.get("opportunity"):
        frappe.throw("Opportunity is required")

    if not survey_data.get("template"):
        frappe.throw("Template is required")

    survey = frappe.new_doc("Technical Survey")

    survey.title = "Test Survey"
    survey.survey_template = survey_data.get("template")

    survey.save()


    survey.reload()
    load_template_fields(survey_data.get("template"), survey.name)

    survey.reload()

    for field in survey.survey_fields:
        field.field_value = str(survey_data.get('answers').get(field.field_name))

    survey.save()

    # # Create a new Survey Submission document
    # submission = frappe.get_doc({
    #     "doctype": "Survey Submission",
    #     "opportunity": survey_data["opportunity"],
    #     "responses": survey_data.get("responses", [])
    # })
    # submission.insert()
    return {"status": "success", "message": "Survey submitted successfully"}