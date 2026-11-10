# Phase 2 metrics summary

99 hospitals in scope.

## Coverage and spread

|                        |   hospitals with a value |          min |       25% |              50% |          75% |           max |
|:-----------------------|-------------------------:|-------------:|----------:|-----------------:|-------------:|--------------:|
| operating_margin       |                       99 | -0.511       |    -0.125 |     -0.047       |  0.049       |   0.713       |
| ebida                  |                       74 | -3.08617e+07 | 78471.5   |      6.00387e+06 |  2.10871e+07 |   3.87246e+08 |
| days_cash_on_hand      |                       99 | -9.05        |     0.094 |      9.179       | 28.801       | 283.398       |
| avg_age_of_plant       |                       99 |  0.392       |    11.521 |     14.555       | 20.862       | 346.04        |
| debt_to_capitalization |                       91 |  0           |     0     |      0.008       |  0.264       |  25.794       |
| existing_debt_service  |                       74 |  0           |     0     | 535719           |  2.4315e+06  |   3.57103e+07 |
| medicaid_share_days    |                       98 |  0.001       |     0.033 |      0.058       |  0.093       |   0.329       |
| medicare_share_days    |                       98 |  0.075       |     0.22  |      0.281       |  0.398       |   0.781       |

## Flags

| flag                                                            |   hospitals |
|:----------------------------------------------------------------|------------:|
| values taken from newer HCRIS version                           |          37 |
| interest assumed zero (none reported, no debt on balance sheet) |          20 |
| interest not reported, debt present or unknown                  |          19 |
| negative net assets                                             |          10 |
| negative cash                                                   |           7 |
| interest negative, unusable                                     |           6 |
| long-term debt unusable (negative component)                    |           4 |
| short-term notes negative, unusable                             |           2 |
| partial year scaled to 12 months                                |           2 |
| no patient days reported                                        |           1 |