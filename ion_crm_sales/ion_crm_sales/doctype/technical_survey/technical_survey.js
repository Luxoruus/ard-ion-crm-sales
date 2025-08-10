frappe.ui.form.on('Technical Survey', {
    refresh: function(frm) {
        // Debug available fields
        console.log("Available fields:", Object.keys(frm.fields_dict));
        
        frm.add_custom_button(__('Reload Template Fields'), function() {
            if (!frm.doc.survey_template) {
                frappe.msgprint(__('Please select a Survey Template first'));
                return;
            }
            
            frappe.call({
                method: 'ion_crm_sales.technical_survey.load_template_fields',
                args: {
                    'template_name': frm.doc.survey_template,
                    'survey_name': frm.doc.name || null
                },
                callback: function(response) {
                    if (response.message && response.message.status === 'success') {
                        const fieldname = response.message.fieldname;
                        
                        if (!frm.fields_dict[fieldname]) {
                            frappe.msgprint(`Field "${fieldname}" not found in the form`);
                            return;
                        }
                        
                        if (frm.doc.__islocal && response.message.fields) {
                            // For new docs, manually update the form
                            frm.clear_table(fieldname);
                            response.message.fields.forEach(field => {
                                let row = frm.add_child(fieldname);
                                row.field_label = field.field_label;
                                row.field_name = field.field_name;
                                row.field_type = field.field_type;
                                row.field_value = field.field_value;
                            });
                            frm.refresh_field(fieldname);
                        } else {
                            // For existing docs, reload
                            frm.reload_doc();
                        }
                        
                        frappe.show_alert({
                            message: response.message.message,
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint(response.message.message || __('Failed to load fields'));
                    }
                }
            });
        });
    },
    
    survey_template: function(frm) {
        if (frm.doc.survey_template && frm.doc.__islocal) {
            // Auto-load template fields when template is selected for new documents
            frm.trigger('reload_template_fields');
        }
    },
    
    reload_template_fields: function(frm) {
        if (!frm.doc.survey_template) return;
        
        frappe.call({
            method: 'ion_crm_sales.technical_survey.load_template_fields',
            args: {
                'template_name': frm.doc.survey_template,
                'survey_name': frm.doc.name || null
            },
            callback: function(response) {
                if (response.message && response.message.status === 'success' && 
                    response.message.fields && response.message.fieldname) {
                    
                    const fieldname = response.message.fieldname;
                    if (!frm.fields_dict[fieldname]) return;
                    
                    frm.clear_table(fieldname);
                    response.message.fields.forEach(field => {
                        let row = frm.add_child(fieldname);
                        row.field_label = field.field_label;
                        row.field_name = field.field_name;
                        row.field_type = field.field_type;
                        row.field_value = field.field_value;
                    });
                    frm.refresh_field(fieldname);
                }
            }
        });
    }
});