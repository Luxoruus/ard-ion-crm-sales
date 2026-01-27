// Copyright (c) 2026
// Accrued Commission Payable (Journal Entry-based)

frappe.query_reports["Accrued Commission Payable"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      reqd: 1
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      reqd: 1,
      default: frappe.datetime.month_start()
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      reqd: 1,
      default: frappe.datetime.month_end()
    },
    // {
    //   fieldname: "sales_person_text",
    //   label: __("Sales Person (from Remark)"),
    //   fieldtype: "Data",
    //   reqd: 0
    // },
    // {
    //   fieldname: "payable_account",
    //   label: __("Commission Payable Account"),
    //   fieldtype: "Link",
    //   options: "Account",
    //   reqd: 0,
    //   description: __("If blank, will use Commission Policy Settings → payable_account")
    // },
    // {
    //   fieldname: "expense_account",
    //   label: __("Commission Expense Account"),
    //   fieldtype: "Link",
    //   options: "Account",
    //   reqd: 0,
    //   description: __("Optional. If blank, will use Commission Policy Settings → expense_account (if any)")
    // }
  ]
};

