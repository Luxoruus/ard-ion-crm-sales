import frappe
from ion_crm_sales.technical_survey import load_template_fields


@frappe.whitelist()
def save_survey(survey_data):
    print("############################")
    print("SHIIIIIIIIIIIIIIIIIIIIIIIIIIT")
    print("############################")
    # Validate and process the survey data
    if not survey_data.get("opportunity"):
        frappe.throw("Opportunity is required")

    if not survey_data.get("template"):
        frappe.throw("Template is required")

    if not survey_data.get("answers"):
        frappe.throw("Answers are required")

    # To change later, to accomodate all the types of opportunities
    opportunity = frappe.get_doc("Opportunity", survey_data.get("opportunity"))

    survey = None

    if not opportunity.custom_technical_survey:
        survey = frappe.new_doc("Technical Survey")
        survey.title = "Test Survey"
        survey.survey_template = survey_data.get("template")
        survey.save()
        survey.reload()
        load_template_fields(survey_data.get("template"), survey.name)
        survey.reload()
        opportunity.custom_technical_survey = survey.name
        opportunity.save()
    else:
        survey = frappe.get_doc("Technical Survey", opportunity.custom_technical_survey)


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