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
        var doc = frm.doc;

        // frm.fields_dict['items'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
        //     return {
        //         filters: {
        //             'customer': frm.doc.party_name // filter by parent field
        //         }
        //     }
        // }

        if (!frm.is_new() && doc.status !== "Lost") {
            // if (doc.items) {
            //     frm.add_custom_button(
            //         __("Supplier Quotation"),
            //         function () {
            //             frm.trigger("make_supplier_quotation");
            //         },
            //         __("Create")
            //     );

            //     frm.add_custom_button(
            //         __("Request For Quotation"),
            //         function () {
            //             frm.trigger("make_request_for_quotation");
            //         },
            //         __("Create")
            //     );
            // }

            if (frm.doc.hotspot_for != "Customer") {
                frm.add_custom_button(
                    __("Customer"),
                    function () {
                        frm.trigger("make_customer");
                    },
                    __("Create")
                );
            }

            // frm.add_custom_button(
            //     __("Quotation"),
            //     function () {
            //         frm.trigger("create_quotation");
            //     },
            //     __("Create")
            // );

            let company_currency = erpnext.get_currency(frm.doc.company);
            if (company_currency != frm.doc.currency) {
                frm.add_custom_button(__("Fetch Latest Exchange Rate"), function () {
                    frm.trigger("currency");
                });
            }
        }
    },

    make_supplier_quotation: function (frm) {
		frappe.model.open_mapped_doc({
			method: "ion_crm_sales.ion_crm_sales.doctype.hotspot.hotspot.make_supplier_quotation",
			frm: frm,
		});
	},

	make_request_for_quotation: function (frm) {
		frappe.model.open_mapped_doc({
			method: "ion_crm_sales.ion_crm_sales.doctype.hotspot.hotspot.make_request_for_quotation",
			frm: frm,
		});
	},

    create_quotation() {
		frappe.model.open_mapped_doc({
			method: "ion_crm_sales.ion_crm_sales.doctype.hotspot.hotspot.make_quotation",
			frm: cur_frm,
		});
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