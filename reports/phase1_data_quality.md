# Phase 1 data quality report: MO, cost report file 2024

135 cost reports for 134 hospitals (CCNs). 116 matched to Hospital General Information; 135 matched to raw HCRIS, of which 96 are the same version of the report.

## Raw HCRIS: fields added (4)

Three candidate interest measures are pulled; none has been chosen yet. A blank means the hospital reported nothing in that cell.

| field                    |   missing |   pct_missing |
|:-------------------------|----------:|--------------:|
| accumulated_depreciation |         9 |           6.7 |
| interest_ws_a            |        86 |          63.7 |
| interest_a7_booked       |       116 |          85.9 |
| interest_a7_allowable    |        71 |          52.6 |

## Raw HCRIS: agreement with the public file on shared cells (46)

Same-version rows prove the parsing. Different-version rows show how much a report changed between the two CMS snapshots; for those reports the HCRIS value is used.

| version                 | field                  |   compared |   agree |   differ |
|:------------------------|:-----------------------|-----------:|--------:|---------:|
| different record number | cash                   |         37 |      36 |        1 |
| different record number | temp_investments       |          6 |       6 |        0 |
| different record number | total_fixed_assets     |         39 |      38 |        1 |
| different record number | total_assets           |         39 |      38 |        1 |
| different record number | notes_loans_short_term |         21 |      21 |        0 |
| different record number | mortgage_payable       |          5 |       4 |        1 |
| different record number | notes_payable          |         16 |      16 |        0 |
| different record number | unsecured_loans        |          3 |       3 |        0 |
| different record number | other_lt_liabilities   |         30 |      29 |        1 |
| different record number | total_lt_liabilities   |         37 |      36 |        1 |
| different record number | total_fund_balances    |         39 |      38 |        1 |
| different record number | total_patient_revenue  |         39 |      39 |        0 |
| different record number | net_patient_revenue    |         39 |      38 |        1 |
| different record number | operating_expense      |         39 |      37 |        2 |
| different record number | other_income           |         39 |      38 |        1 |
| different record number | other_expenses         |         23 |      22 |        1 |
| different record number | net_income             |         39 |      37 |        2 |
| different record number | depreciation           |         39 |      37 |        2 |
| different record number | salaries               |         39 |      38 |        1 |
| different record number | days_medicare          |         39 |      30 |        9 |
| different record number | days_medicaid          |         39 |      37 |        2 |
| different record number | days_total             |         39 |      38 |        1 |
| different record number | medicaid_net_revenue   |         37 |      37 |        0 |
| same record number      | cash                   |         77 |      77 |        0 |
| same record number      | temp_investments       |         13 |      13 |        0 |
| same record number      | total_fixed_assets     |         87 |      87 |        0 |
| same record number      | total_assets           |         87 |      87 |        0 |
| same record number      | notes_loans_short_term |         34 |      34 |        0 |
| same record number      | mortgage_payable       |          9 |       9 |        0 |
| same record number      | notes_payable          |         30 |      30 |        0 |
| same record number      | unsecured_loans        |          5 |       5 |        0 |
| same record number      | other_lt_liabilities   |         63 |      63 |        0 |
| same record number      | total_lt_liabilities   |         74 |      74 |        0 |
| same record number      | total_fund_balances    |         87 |      87 |        0 |
| same record number      | total_patient_revenue  |         92 |      92 |        0 |
| same record number      | net_patient_revenue    |         92 |      92 |        0 |
| same record number      | operating_expense      |         92 |      92 |        0 |
| same record number      | other_income           |         92 |      92 |        0 |
| same record number      | other_expenses         |         29 |      29 |        0 |
| same record number      | net_income             |         92 |      92 |        0 |
| same record number      | depreciation           |         92 |      92 |        0 |
| same record number      | salaries               |         92 |      92 |        0 |
| same record number      | days_medicare          |         90 |      90 |        0 |
| same record number      | days_medicaid          |         91 |      91 |        0 |
| same record number      | days_total             |         91 |      91 |        0 |
| same record number      | medicaid_net_revenue   |         63 |      63 |        0 |

## Raw HCRIS: fixed-asset roll-up failures (0)

Gross fixed assets minus accumulated depreciation should equal Worksheet G line 30.

_None found._

## Raw HCRIS: no matching record (0)



_None found._

## Missing values in Phase 2 fields (22)

Blank cells are left blank. A blank may mean zero or may mean not reported; the file does not say which.

| field                  |   missing |   pct_missing |
|:-----------------------|----------:|--------------:|
| net_patient_revenue    |         4 |           3   |
| operating_expense      |         4 |           3   |
| other_income           |         4 |           3   |
| other_expenses         |        84 |          62.2 |
| net_income             |         4 |           3   |
| depreciation           |         4 |           3   |
| cash                   |        21 |          15.6 |
| temp_investments       |       116 |          85.9 |
| salaries               |         4 |           3   |
| mortgage_payable       |       121 |          89.6 |
| notes_payable          |        89 |          65.9 |
| unsecured_loans        |       127 |          94.1 |
| other_lt_liabilities   |        42 |          31.1 |
| total_lt_liabilities   |        24 |          17.8 |
| notes_loans_short_term |        80 |          59.3 |
| total_fund_balances    |         9 |           6.7 |
| days_medicare          |         6 |           4.4 |
| days_medicaid          |         5 |           3.7 |
| days_total             |         5 |           3.7 |
| medicaid_net_revenue   |        35 |          25.9 |
| star_rating            |        58 |          43   |
| hospital_type          |        19 |          14.1 |

## Negative values where none should exist (53)



|    ccn | hospital_name                        | ccn_facility_type   | field                  |             value |
|-------:|:-------------------------------------|:--------------------|:-----------------------|------------------:|
| 260048 | UNIVERSITY HEALTH TRUMAN MED CENTER  | STH                 | cash                   |      -1.05895e+06 |
| 260057 | CAMERON REGIONAL MEDICAL CENTER      | STH                 | cash                   | -773926           |
| 260078 | OZARKS MEDICAL CENTER                | STH                 | cash                   |      -1.01543e+06 |
| 260095 | CENTERPOINT MEDICAL CENTER           | STH                 | cash                   |   -5666           |
| 260102 | UNIVERSITY HEALTH LAKEWOOD MED CTR   | STH                 | cash                   |   -7368           |
| 260104 | SSM HEALTH DEPAUL HOSPITAL           | STH                 | cash                   |      -1.46395e+07 |
| 260108 | MISSOURI BAPTIST MEDICAL CENTER      | STH                 | cash                   |  -49685           |
| 262020 | LANDMARK HOSPITAL OF COLUMBIA  LLC   | LTCH                | cash                   |  -60111           |
| 264012 | CENTERPOINTE HOSPITAL                | PH                  | cash                   | -272995           |
| 264024 | LAKELAND REGIONAL HOSPITAL           | PH                  | cash                   | -132666           |
| 264030 | SIGNATURE PSYCH HOSPITAL             | PH                  | cash                   |  -15309           |
| 264032 | CENTERPOINTE HOSPITAL OF COLUMBIA    | PH                  | cash                   |  -41916           |
| 264034 | SOUTHEAST BEHAVIORAL HOSPITAL        | PH                  | cash                   |  -81152           |
| 260024 | TEXAS COUNTY MEMORIAL HOSPITAL       | STH                 | interest_a7_allowable  | -542914           |
| 260048 | UNIVERSITY HEALTH TRUMAN MED CENTER  | STH                 | interest_a7_allowable  |  -72909           |
| 260062 | SAINT LUKES NORTH HOSPITAL           | STH                 | interest_a7_allowable  |  -82838           |
| 260078 | OZARKS MEDICAL CENTER                | STH                 | interest_a7_allowable  |      -4.30803e+06 |
| 260085 | ST JOSEPH MEDICAL CENTER             | STH                 | interest_a7_allowable  |      -1.25923e+06 |
| 260176 | ST. LUKES DES PERES HOSPITAL         | STH                 | interest_a7_allowable  | -234166           |
| 260179 | ST. LUKES HOSPITAL                   | STH                 | interest_a7_allowable  | -199521           |
| 260195 | CITIZENS MEMORIAL HOSPITAL DISTRICT  | STH                 | interest_a7_allowable  |      -4.08264e+06 |
| 261305 | PUTNAM COUNTY MEMORIAL HOSPITAL      | CAH                 | interest_a7_allowable  |  -10049           |
| 261308 | WASHINGTON COUNTY MEMORIAL HOSPITAL  | CAH                 | interest_a7_allowable  |   -3768           |
| 261328 | NORTHWEST MEDICAL CENTER             | CAH                 | interest_a7_allowable  |      -1           |
| 261333 | PIKE COUNTY MEMORIAL HOSPITAL        | CAH                 | interest_a7_allowable  |  -36425           |
| 261336 | IRON COUNTY HOSPITAL                 | CAH                 | interest_a7_allowable  | -180351           |
| 262017 | SSH - SPRINGFIELD INC.               | LTCH                | interest_a7_allowable  |  -31786           |
| 260005 | SSM HEALTH ST. JOSEPH HOSPITAL - SC  | STH                 | interest_a7_booked     | -637076           |
| 260022 | NORTHEAST REGIONAL MEDICAL CENTER    | STH                 | interest_a7_booked     |  -19926           |
| 260091 | SSM HEALTH ST. MARYS HOSPITAL - STL  | STH                 | interest_a7_booked     | -696406           |
| 260104 | SSM HEALTH DEPAUL HOSPITAL           | STH                 | interest_a7_booked     |   -6753           |
| 260105 | SSM SAINT LOUIS UNIVERSITY HOSPITAL  | STH                 | interest_a7_booked     |  -71998           |
| 261308 | WASHINGTON COUNTY MEMORIAL HOSPITAL  | CAH                 | interest_ws_a          |   -3768           |
| 260176 | ST. LUKES DES PERES HOSPITAL         | STH                 | medicaid_net_revenue   |      -5.02528e+06 |
| 260022 | NORTHEAST REGIONAL MEDICAL CENTER    | STH                 | notes_loans_short_term | -174654           |
| 260091 | SSM HEALTH ST. MARYS HOSPITAL - STL  | STH                 | notes_loans_short_term |    -279           |
| 261303 | COMMUNITY HOSPITAL ASSOCIATION  INC. | CAH                 | notes_payable          | -131491           |
| 260141 | UNIV OF MISSOURI HEALTH CARE         | STH                 | temp_investments       |   -1306           |
| 262019 | HEARTLAND LONG TERM ACUTE CARE HOSPI | LTCH                | total_assets           |      -1.22627e+07 |
| 264035 | MARYLAND HEIGHTS CENTER FOR BH       | PH                  | total_assets           |      -1.59797e+06 |
| 260005 | SSM HEALTH ST. JOSEPH HOSPITAL - SC  | STH                 | total_lt_liabilities   |      -7.30569e+08 |
| 260011 | SSM HEALTH-ST. MARYS-JEFFERSON CITY  | STH                 | total_lt_liabilities   |      -4.43816e+08 |
| 260081 | SSM HEALTH ST CLARE HOSPITAL         | STH                 | total_lt_liabilities   |      -4.5521e+09  |
| 260091 | SSM HEALTH ST. MARYS HOSPITAL - STL  | STH                 | total_lt_liabilities   |      -1.37255e+09 |
| 260095 | CENTERPOINT MEDICAL CENTER           | STH                 | total_lt_liabilities   |      -2.06763e+08 |
| 260104 | SSM HEALTH DEPAUL HOSPITAL           | STH                 | total_lt_liabilities   |      -1.39867e+09 |
| 260105 | SSM SAINT LOUIS UNIVERSITY HOSPITAL  | STH                 | total_lt_liabilities   |      -2.17077e+08 |
| 260200 | SSM HEALTH ST. JOSEPH HOSPITAL - LSL | STH                 | total_lt_liabilities   |      -6.00318e+08 |
| 260214 | BELTON REGIONAL MEDICAL CENTER       | STH                 | total_lt_liabilities   |      -7.59108e+07 |
| 264033 | SPRINGFIELD BEHAVIORAL HOSPITAL      | PH                  | total_lt_liabilities   |      -1.22763e+07 |
| 260095 | CENTERPOINT MEDICAL CENTER           | STH                 | unsecured_loans        |      -2.11521e+08 |
| 260105 | SSM SAINT LOUIS UNIVERSITY HOSPITAL  | STH                 | unsecured_loans        |      -2.17077e+08 |
| 260214 | BELTON REGIONAL MEDICAL CENTER       | STH                 | unsecured_loans        |      -7.69756e+07 |

## Failed consistency checks (42)



|    ccn | hospital_name                        | ccn_facility_type   | check                               |
|-------:|:-------------------------------------|:--------------------|:------------------------------------|
| 260141 | UNIV OF MISSOURI HEALTH CARE         | STH                 | balance sheet does not balance      |
| 261333 | PIKE COUNTY MEMORIAL HOSPITAL        | CAH                 | balance sheet does not balance      |
| 260061 | NEVADA REGIONAL MEDICAL CENTER       | STH                 | balance sheet does not balance      |
| 263304 | SHRINERS HOSPITALS FOR CHILDREN      | CH                  | no balance sheet reported           |
| 264020 | ROYAL OAKS HOSPITAL                  | PH                  | no balance sheet reported           |
| 264028 | HAWTHORN CHILDRENS PSYCH. CTR.       | PH                  | no balance sheet reported           |
| 263303 | RANKEN JORDAN                        | CH                  | no balance sheet reported           |
| 264004 | FULTON STATE HOSPITAL                | PH                  | no balance sheet reported           |
| 264005 | SMMHC                                | PH                  | no balance sheet reported           |
| 264007 | N.W. MO PSYCHIATRIC REHAB CTR        | PH                  | no balance sheet reported           |
| 264008 | CENTER FOR BEHAVIORAL MEDICINE       | PH                  | no balance sheet reported           |
| 264010 | ST. LOUIS FORENSIC TREATMENT CENTER  | PH                  | no balance sheet reported           |
| 263304 | SHRINERS HOSPITALS FOR CHILDREN      | CH                  | net patient revenue missing or zero |
| 264020 | ROYAL OAKS HOSPITAL                  | PH                  | net patient revenue missing or zero |
| 264028 | HAWTHORN CHILDRENS PSYCH. CTR.       | PH                  | net patient revenue missing or zero |
| 263303 | RANKEN JORDAN                        | CH                  | net patient revenue missing or zero |
| 264030 | SIGNATURE PSYCH HOSPITAL             | PH                  | negative net assets (fund balance)  |
| 260105 | SSM SAINT LOUIS UNIVERSITY HOSPITAL  | STH                 | negative net assets (fund balance)  |
| 260011 | SSM HEALTH-ST. MARYS-JEFFERSON CITY  | STH                 | negative net assets (fund balance)  |
| 260160 | MERCY HOSPITAL STODDARD              | STH                 | negative net assets (fund balance)  |
| 264035 | MARYLAND HEIGHTS CENTER FOR BH       | PH                  | negative net assets (fund balance)  |
| 262018 | KINDRED HOSPITAL NORTHLAND           | LTCH                | negative net assets (fund balance)  |
| 261310 | SCOTLAND COUNTY MEMORIAL HOSPITAL    | CAH                 | negative net assets (fund balance)  |
| 262019 | HEARTLAND LONG TERM ACUTE CARE HOSPI | LTCH                | negative net assets (fund balance)  |
| 260102 | UNIVERSITY HEALTH LAKEWOOD MED CTR   | STH                 | negative net assets (fund balance)  |
| 264034 | SOUTHEAST BEHAVIORAL HOSPITAL        | PH                  | negative net assets (fund balance)  |
| 262013 | SSH - ST LOUIS INC.                  | LTCH                | negative net assets (fund balance)  |
| 264012 | CENTERPOINTE HOSPITAL                | PH                  | negative net assets (fund balance)  |
| 262010 | KINDRED HOSPITAL ST. ANTHONY         | LTCH                | negative net assets (fund balance)  |
| 262020 | LANDMARK HOSPITAL OF COLUMBIA  LLC   | LTCH                | negative net assets (fund balance)  |
| 260027 | AM 1 RESEARCH MED CTR                | STH                 | negative net assets (fund balance)  |
| 261314 | HERMANN AREA DISTRICT HOSPITAL       | CAH                 | negative net assets (fund balance)  |
| 262016 | LANDMARK HOSPITAL OF JOPLIN  LLC     | LTCH                | negative net assets (fund balance)  |
| 260085 | ST JOSEPH MEDICAL CENTER             | STH                 | negative net assets (fund balance)  |
| 262017 | SSH - SPRINGFIELD INC.               | LTCH                | negative net assets (fund balance)  |
| 260005 | SSM HEALTH ST. JOSEPH HOSPITAL - SC  | STH                 | negative net assets (fund balance)  |
| 261320 | LAFAYETTE REGIONAL HEALTH CENTER     | CAH                 | negative net assets (fund balance)  |
| 260779 | PARKLAND HLTH CTR - BONNE TERRE      | STH                 | zero or missing total patient days  |
| 263304 | SHRINERS HOSPITALS FOR CHILDREN      | CH                  | zero or missing total patient days  |
| 264020 | ROYAL OAKS HOSPITAL                  | PH                  | zero or missing total patient days  |
| 264028 | HAWTHORN CHILDRENS PSYCH. CTR.       | PH                  | zero or missing total patient days  |
| 263303 | RANKEN JORDAN                        | CH                  | zero or missing total patient days  |

## Partial-year or odd-length reports (5)

Outside 360-371 days.

|    ccn | hospital_name                     | ccn_facility_type   | fy_begin            | fy_end              |   period_days |   reports_for_ccn |
|-------:|:----------------------------------|:--------------------|:--------------------|:--------------------|--------------:|------------------:|
| 260050 | MOSAIC MEDICAL CENTER - MARYVILLE | STH                 | 2024-07-01 00:00:00 | 2024-08-12 00:00:00 |            43 |                 1 |
| 264030 | SIGNATURE PSYCH HOSPITAL          | PH                  | 2024-01-01 00:00:00 | 2024-09-30 00:00:00 |           274 |                 1 |
| 261311 | MERCY HOSPITAL PERRY COUNTY       | CAH                 | 2023-10-01 00:00:00 | 2024-06-30 00:00:00 |           274 |                 2 |
| 261340 | MOSAIC MEDICAL CENTER - MARYVILLE | CAH                 | 2024-08-13 00:00:00 | 2025-06-30 00:00:00 |           322 |                 1 |
| 260176 | ST. LUKES DES PERES HOSPITAL      | STH                 | 2024-07-01 00:00:00 | 2025-07-30 00:00:00 |           395 |                 1 |

## Hospitals with more than one report (2)



|    ccn | hospital_name               | ccn_facility_type   | fy_begin            | fy_end              |   period_days | is_latest_for_ccn   |
|-------:|:----------------------------|:--------------------|:--------------------|:--------------------|--------------:|:--------------------|
| 261311 | MERCY HOSPITAL PERRY COUNTY | CAH                 | 2023-10-01 00:00:00 | 2024-06-30 00:00:00 |           274 | False               |
| 261311 | MERCY HOSPITAL PERRY COUNTY | CAH                 | 2024-07-01 00:00:00 | 2025-06-30 00:00:00 |           365 | True                |

## No match in Hospital General Information (19)

These have no hospital type, star rating, or Care Compare address.

|    ccn | hospital_name                        | ccn_facility_type   |
|-------:|:-------------------------------------|:--------------------|
| 260050 | MOSAIC MEDICAL CENTER - MARYVILLE    | STH                 |
| 260176 | ST. LUKES DES PERES HOSPITAL         | STH                 |
| 262010 | KINDRED HOSPITAL ST. ANTHONY         | LTCH                |
| 262013 | SSH - ST LOUIS INC.                  | LTCH                |
| 262015 | LANDMARK HOSPITAL OF CAPE GIRARDEAU  | LTCH                |
| 262016 | LANDMARK HOSPITAL OF JOPLIN  LLC     | LTCH                |
| 262017 | SSH - SPRINGFIELD INC.               | LTCH                |
| 262018 | KINDRED HOSPITAL NORTHLAND           | LTCH                |
| 262019 | HEARTLAND LONG TERM ACUTE CARE HOSPI | LTCH                |
| 262020 | LANDMARK HOSPITAL OF COLUMBIA  LLC   | LTCH                |
| 263027 | RUSK REHABILITATION HOSPITAL  AN AFF | RH                  |
| 263028 | THE REHABILITATION INSTITUTE OF ST.  | RH                  |
| 263029 | MERCY REHABILITATION HOSPITAL ST. LO | RH                  |
| 263030 | ST. LUKES REHAB HOSPITAL             | RH                  |
| 263031 | SSM SELECT REHAB ST LOUIS  LLC       | RH                  |
| 263032 | MERCY REHABILITATION HOSPITAL SPRING | RH                  |
| 263034 | MERCY REHABILITATION HOSPITAL ST. LO | RH                  |
| 264028 | HAWTHORN CHILDRENS PSYCH. CTR.       | PH                  |
| 264030 | SIGNATURE PSYCH HOSPITAL             | PH                  |
