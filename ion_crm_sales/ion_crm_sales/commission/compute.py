
import frappe
from frappe.utils import flt
from .utils import actual_sales_for_person

def compute_line(line, company, fiscal_year):
    line.actual_sales = flt(actual_sales_for_person(line.sales_person, company, fiscal_year))
    target = flt(line.target_value)
    if not target:
        line.achievement_pct = 0
        line.commission_rate = 0
        line.commission_value = 0
        return

    line.achievement_pct = (line.actual_sales / target) * 100

    if line.department == "Business Accounts":
        if line.actual_sales > target:
            line.commission_rate = 6
            line.commission_value = (line.actual_sales - target) * 0.06
        else:
            line.commission_rate = 0
            line.commission_value = 0
    else:
        if line.achievement_pct < 100:
            rate = 0
        elif line.achievement_pct <= 120:
            rate = 5
        elif line.achievement_pct <= 140:
            rate = 6
        else:
            rate = flt(frappe.db.get_single_value("Commission Policy Settings", "rate_above_140") or 7)
        line.commission_rate = rate
        line.commission_value = line.actual_sales * (rate / 100.0)

    line.achievement_pct = round(line.achievement_pct, 2)
    line.commission_value = round(flt(line.commission_value), 2)

def compute_totals(sheet):
    total_target = total_actual = total_commission = 0.0
    for line in sheet.get("commission_lines") or []:
        compute_line(line, sheet.company, sheet.fiscal_year)
        total_target += flt(line.target_value)
        total_actual += flt(line.actual_sales)
        total_commission += flt(line.commission_value)
    sheet.total_target = round(total_target, 2)
    sheet.total_actual_sales = round(total_actual, 2)
    sheet.total_commission = round(total_commission, 2)
