import frappe
from frappe import _

@frappe.whitelist()
def load_template_fields(template_name, survey_name=None):
    """Load fields from template into survey"""
    if not template_name:
        return {"status": "error", "message": "No template selected"}
    
    try:
        template = frappe.get_doc("Technical Survey Template", template_name)
        survey_doc = None
        
        # Get the Technical Survey doctype to find the correct field name
        survey_doctype = frappe.get_doc("DocType", "Technical Survey")
        
        # Find the table field that points to Technical Survey Field
        survey_fields_fieldname = None
        for field in survey_doctype.fields:
            if field.fieldtype == "Table" and field.options == "Technical Survey Field":
                survey_fields_fieldname = field.fieldname
                break
                
        if not survey_fields_fieldname:
            return {"status": "error", "message": "Survey fields table not found in DocType"}
            
        # If survey_name is provided and valid, update existing survey
        if survey_name and not survey_name.startswith("new-"):
            survey_doc = frappe.get_doc("Technical Survey", survey_name)
            # Clear existing fields
            survey_doc.set(survey_fields_fieldname, [])
        else:
            # For testing, create a temporary document
            survey_doc = frappe.new_doc("Technical Survey")
            survey_doc.title = "New Survey"
            survey_doc.survey_template = template_name
        
        # Add fields from template
        for field in template.fields:
            survey_doc.append(survey_fields_fieldname, {
                "field_label": field.field_label,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "field_value": field.default_value or ""
            })
        
        # Return the field name and status
        if survey_name and not survey_name.startswith("new-"):
            survey_doc.save()
            return {
                "status": "success", 
                "message": "Fields loaded successfully",
                "fieldname": survey_fields_fieldname
            }
        else:
            return {
                "status": "success", 
                "message": f"{len(template.fields)} fields would be loaded",
                "fieldname": survey_fields_fieldname,
                "fields": [
                    {
                        "field_label": f.field_label,
                        "field_name": f.field_name,
                        "field_type": f.field_type,
                        "field_value": f.default_value or ""
                    } for f in template.fields
                ]
            }
            
    except Exception as e:
        frappe.log_error(f"Failed to load template fields: {str(e)}")
        return {"status": "error", "message": str(e)}