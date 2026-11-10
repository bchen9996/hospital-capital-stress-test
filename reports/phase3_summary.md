# Phase 3 stress test summary

99 hospitals in scope; 74 have every input needed.

## Headroom (extra annual payment the hospital could carry)

| measure      |   hospitals with a value |   negative |   median ($M) |   25th pct ($M) |   75th pct ($M) |
|:-------------|-------------------------:|-----------:|--------------:|----------------:|----------------:|
| baseline     |                       74 |         24 |          4.08 |           -0.94 |           15.59 |
| medicaid_cut |                       74 |         26 |          3.43 |           -1.1  |           14.5  |
| volume_drop  |                       74 |         37 |         -0.2  |           -3.24 |            8.1  |
| labor_shock  |                       74 |         29 |          2.38 |           -1.76 |           13.33 |
| combined     |                       74 |         42 |         -1.23 |           -7.11 |            4.13 |
| stressed     |                       74 |         42 |         -1.23 |           -7.11 |            4.13 |

## Which case sets stressed headroom

| lowest-headroom case   |   hospitals |
|:-----------------------|------------:|
| combined               |          74 |

## Affordable principal at stressed headroom

Rates and terms are PLACEHOLDERS from config.yaml, not official program terms.

| capital type                                        |   rate |   term (years) |   median principal, hospitals with positive stressed headroom ($M) |
|:----------------------------------------------------|-------:|---------------:|-------------------------------------------------------------------:|
| USDA Community Facilities loan                      |  0.04  |             35 |                                                               90.2 |
| CDFI / New Markets Tax Credit loan                  |  0.05  |             20 |                                                               60.2 |
| HUD Section 242 insured mortgage                    |  0.055 |             25 |                                                               64.8 |
| Bank loan                                           |  0.07  |             10 |                                                               33.9 |
| Tax-exempt municipal bonds                          |  0.045 |             30 |                                                               78.7 |
| Sale-leaseback / REIT (rent treated as the payment) |  0.075 |             20 |                                                               49.3 |