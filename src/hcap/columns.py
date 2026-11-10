"""Verified CMS column names, mapped to short internal names.

Every name on the right-hand side was read from the actual downloaded files
(CostReport_2024_Final.csv and Hospital_General_Information.csv), not assumed.
Ingestion fails loudly if CMS renames any of them.

The trailing comment on each line is the Form CMS-2552-10 source cell given in
the CMS data dictionary.
"""

# --- Hospital Provider Cost Report -------------------------------------------
COST_REPORT_TEXT: dict[str, str] = {
    "rpt_rec_num": "rpt_rec_num",
    "ccn": "Provider CCN",
    "hospital_name": "Hospital Name",
    "street": "Street Address",
    "city": "City",
    "state": "State Code",
    "zip": "Zip Code",
    "county": "County",
    "cbsa": "Medicare CBSA Number",
    "rural_urban": "Rural Versus Urban",  # S-2 Pt I line 26
    "ccn_facility_type": "CCN Facility Type",
    "provider_type": "Provider Type",  # S-2 Pt I line 3 col 4
    "control_type": "Type of Control",  # S-2 Pt I line 21
    "fy_begin": "Fiscal Year Begin Date",
    "fy_end": "Fiscal Year End Date",
}

COST_REPORT_NUMERIC: dict[str, str] = {
    "fte": "FTE - Employees on Payroll",
    "beds": "Number of Beds",
    "days_medicare": "Total Days Title XVIII",  # S-3 Pt I line 14 col 6
    "days_medicaid": "Total Days Title XIX",  # S-3 Pt I line 14 col 7
    "days_total": "Total Days (V + XVIII + XIX + Unknown)",  # S-3 Pt I line 14 col 8
    "salaries": "Total Salaries From Worksheet A",  # A line 200 col 1
    "depreciation": "Depreciation Cost",  # A-7 Pt III line 3 col 9
    "total_costs": "Total Costs",  # C Pt I line 202 col 3
    "cash": "Cash on Hand and in Banks",  # G line 1
    "temp_investments": "Temporary Investments",  # G line 2
    "total_current_assets": "Total Current Assets",
    "total_fixed_assets": "Total Fixed Assets",
    "total_assets": "Total Assets",
    "notes_loans_short_term": "Notes and Loans Payable (Short Term)",  # G line 40
    "total_current_liabilities": "Total Current Liabilities",
    "mortgage_payable": "Mortgage Payable",  # G line 46
    "notes_payable": "Notes Payable",  # G line 47
    "unsecured_loans": "Unsecured Loans",  # G line 48
    "other_lt_liabilities": "Other Long Term Liabilities",  # G line 49
    "total_lt_liabilities": "Total Long Term Liabilities",  # G line 50
    "total_liabilities": "Total Liabilities",
    "total_fund_balances": "Total Fund Balances",  # G line 59
    "total_liab_and_fund": "Total Liabilities and Fund Balances",  # G line 60
    "inpatient_revenue": "Inpatient Revenue",
    "outpatient_revenue": "Outpatient Revenue",
    "total_patient_revenue": "Total Patient Revenue",  # G-3 line 1
    "contractual_allowances": "Less Contractual Allowance and Discounts on Patients' Accounts",  # G-3 line 2
    "net_patient_revenue": "Net Patient Revenue",  # G-3 line 3
    "operating_expense": "Less Total Operating Expense",  # G-3 line 4
    "net_income_patient_services": "Net Income from Service to Patients",  # G-3 line 5
    "other_income": "Total Other Income",  # G-3 line 25
    "total_income": "Total Income",  # G-3 line 26
    "other_expenses": "Total Other Expenses",  # G-3 line 28
    "net_income": "Net Income",  # G-3 line 29
    "medicaid_net_revenue": "Net Revenue from Medicaid",  # S-10 line 2
    "medicaid_charges": "Medicaid Charges",  # S-10 line 6
}

# --- Hospital General Information --------------------------------------------
HGI: dict[str, str] = {
    "ccn": "Facility ID",
    "hgi_name": "Facility Name",
    "hgi_address": "Address",
    "hgi_city": "City/Town",
    "hgi_state": "State",
    "hgi_zip": "ZIP Code",
    "hgi_county": "County/Parish",
    "hospital_type": "Hospital Type",
    "ownership": "Hospital Ownership",
    "emergency_services": "Emergency Services",
    "star_rating": "Hospital overall rating",
}

# Interest expense and accumulated depreciation are not in the public-use file.
# They are read from raw HCRIS; the cell definitions live in hcris.py.
