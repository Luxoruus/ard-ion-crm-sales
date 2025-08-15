// Copyright (c) 2025, ard.ly and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Hotspot", {
// 	refresh(frm) {

// 	},
// });


frappe.provide("erpnext.crm");
erpnext.pre_sales.set_as_lost("Hotspot");
erpnext.sales_common.setup_selling_controller();


frappe.ui.form.on("Hotspot", {
    refresh: function (frm) {
        frm.trigger("handle_fields");

        var doc = frm.doc;

        if (!frm.is_new() && doc.status !== "Lost") {
            if (frm.doc.hotspot_for != "Customer") {
                frm.add_custom_button(
                    __("Customer"),
                    function () {
                        frm.trigger("make_customer");
                    },
                    __("Create")
                );
            }

            let company_currency = erpnext.get_currency(frm.doc.company);
            if (company_currency != frm.doc.currency) {
                frm.add_custom_button(__("Fetch Latest Exchange Rate"), function () {
                    frm.trigger("currency");
                });
            }
        }


        frm.set_df_property('party_name', 'label', String(frm.doc.hotspot_for))

        if (['Requirements Gathering', 'Closed'].includes(frm.doc.workflow_state)) {
            frm.set_df_property('requirements', 'hidden', false)
        } else {
            frm.set_df_property('requirements', 'hidden', true)
        }


        if (frm.doc.workflow_state == 'Qualifying') {
            frm.$wrapper.find(".actions-btn-group").hide()
        } else {
            frm.$wrapper.find(".actions-btn-group").show()
        }
    },

    hotspot_for(frm) {
        if (frm.doc.hotspot_for)
            frm.set_df_property('party_name', 'label', String(frm.doc.hotspot_for))
    },

    validate(frm) {
        frm.trigger("handle_fields");
    },

    make_customer() {
        frappe.model.open_mapped_doc({
            method: "ion_crm_sales.ion_crm_sales.doctype.hotspot.hotspot.make_customer",
            frm: cur_frm,
        });
    },

    onload_post_render: function (frm) {
        frm.get_field("items").grid.set_multiple_add("item_code", "qty");
    },

    change_grid_labels: function (frm) {
        let company_currency = erpnext.get_currency(frm.doc.company);
        frm.set_currency_labels(["base_rate", "base_amount"], company_currency, "items");
        frm.set_currency_labels(["rate", "amount"], frm.doc.currency, "items");

        let item_grid = frm.fields_dict.items.grid;
        $.each(["base_rate", "base_amount"], function (i, fname) {
            if (frappe.meta.get_docfield(item_grid.doctype, fname))
                item_grid.set_column_disp(fname, frm.doc.currency != company_currency);
        });
        frm.refresh_fields();
    },

    calculate_total: function (frm) {
        let total = 0;
        frm.doc.items.forEach((item) => {
            total += item.amount;
        });

        frm.set_value({
            total: flt(total),
        });
    },

    handle_fields: function (frm) {
        frm.$wrapper.find("[data-fieldname='proposal_tab']").hide();
        frm.$wrapper.find("[data-fieldname='survey_tab']").hide();
        frm.$wrapper.find("[data-fieldname='technical_tab']").hide();

        if (frm.doc.request && frm.doc.type == 'Reach'){
            frm.$wrapper.find("[data-fieldname='proposal_tab']").show();
        }


        if (!['Qualifying', 'Proposed'].includes(frm.doc.workflow_state)){
            frm.$wrapper.find("[data-fieldname='survey_tab']").show();
        }


        if ((frm.doc.workflow_state == "Qualifying" && frm.doc.request)) {
            switch (frm.doc.type) {
                case 'Reach':
                    if (frm.doc.description && frm.doc.items.length > 0) {
                        frm.doc.workflow_state = 'Proposed'
                    }
                    break;
                case 'Received':
                    // Do received
                    break;
                case 'Custom':
                    // Do custom
                    break;
                default:
                    break;
            }
        }

        if ((frm.doc.workflow_state == 'Qualifying' && frm.doc.type == "Reach") || ['Surveying'].includes(frm.doc.workflow_state)) {
            frm.$wrapper.find(".actions-btn-group").hide()
        } else {
            frm.$wrapper.find(".actions-btn-group").show()
        }
    },
});


frappe.ui.form.on("Hotspot Item", {
    calculate: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
        frm.trigger("calculate_total");
        // frappe.db.get_doc('Item Price', row.item).then((item_price) => {
        //     frappe.model.set_value(cdt, cdn, "rate", flt(item_price.price_list_rate));
        //     frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(item_price.price_list_rate));
        //     // frappe.model.set_value(cdt, cdn, "base_rate", flt(frm.doc.conversion_rate) * flt(row.rate));
        //     // frappe.model.set_value(cdt, cdn, "base_amount", flt(frm.doc.conversion_rate) * flt(row.amount));
        //     frm.trigger("calculate_total");
        // });
    },
    qty: function (frm, cdt, cdn) {
        frm.trigger("calculate", cdt, cdn);
    },
    rate: function (frm, cdt, cdn) {
        frm.trigger("calculate", cdt, cdn);
    },
});