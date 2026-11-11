# Hospital capital stress test (Missouri pilot)

Screens each hospital's finances from public CMS data, estimates how much new annual
debt or rent payment it could carry, reruns that under stress, and matches it to a rung
on a capital ladder. Built in phases. All five phases are built: data ingestion, financial metrics, stress test, capital matcher and dashboard. Missouri only so far.

Screening and educational tool only. Not financial, investment, or municipal advisory advice.
Based on public data that may be 1-2 years old.

## Run it

```bash
pip install -r requirements.txt
python scripts/phase1.py     # downloads CMS files, builds data/hospitals.duckdb, writes the quality report
python scripts/phase2.py     # computes metrics; writes reports/phase2_metrics.csv and phase2_summary.md
python scripts/phase3.py     # headroom, stress scenarios, affordable principal
python scripts/phase4.py     # geocodes addresses (Census Bureau, then OpenStreetMap), matches hospitals to the capital ladder
streamlit run app.py         # the dashboard
pytest
```

## Layout

| Path | What it is |
|---|---|
| `config.yaml` | Every data source, threshold, rate and scenario assumption |
| `src/hcap/columns.py` | CMS column names as verified in the downloaded files, mapped to short names |
| `src/hcap/ingest.py` | Download, filter to state, join, write DuckDB |
| `src/hcap/hcris.py` | Read interest and accumulated depreciation from raw HCRIS |
| `src/hcap/quality.py` | Data quality checks (report only; nothing is corrected) |
| `scripts/phase1.py` | Runs Phase 1 end to end |
| `reports/phase1_data_quality.md` | The data quality report |
| `data/hospitals.duckdb` | Tables `cost_report_raw`, `hgi_raw`, `hospitals` (Missouri, joined) |

## Data sources

- **CMS Hospital Provider Cost Report, 2024 file** (data.cms.gov). A CMS-curated extract of
  117 fields from Form CMS-2552-10. The "2024" file holds reports whose fiscal year *begins*
  in federal fiscal year 2024 (October 2023 to September 2024), so year-ends run from
  mid-2024 to August 2025.
- **CMS Hospital General Information** (Care Compare): hospital type, ownership, star rating, address.

Joined on CCN (the 6-digit CMS Certification Number).

- **Raw HCRIS, federal FY 2024** (`HOSP10FY2024.ZIP`, downloads.cms.gov): the full cost report,
  one row per cell. Used only for fields the extract leaves out. Matched on CCN + reporting
  period, not record number, because 39 of the 135 Missouri reports were amended or settled
  between the two CMS snapshots and carry a new record number in HCRIS.

## Fields pulled from raw HCRIS

| Field | Cells | Coverage (of 135) |
|---|---|---|
| `accumulated_depreciation` | Worksheet G lines 14, 16, 18, 20, 22, 24, 26, 28, all fund columns, sign flipped | 126 |
| `interest_ws_a` | Worksheet A line 113 "Interest expense", column 2 (as booked) | 49 |
| `interest_a7_booked` | A-7 Part II line 3 column 11 (capital interest booked in the capital cost centres) | 19 |
| `interest_a7_allowable` | A-7 Part III line 3 column 11 (after reclassifications and Medicare adjustments; can be negative) | 64 |

How the cells were verified: five cells that exist in both sources (cash, total fixed assets,
depreciation, net income, net patient revenue) agree exactly on every same-version report, the
alpha file labels Worksheet A line 113 "INTEREST EXPENSE", and gross fixed assets minus
accumulated depreciation equals Worksheet G line 30 for every report.

## Known gaps

- **Interest expense has no single clean source.** Which of the three measures to use (or how
  to combine them) is an open methodology decision. Hospitals owned by health systems often
  carry debt and interest at the parent, so their cost report shows little or none.
- **Current portion of long-term debt is not a line on the form.** The nearest proxy is
  Worksheet G line 40, "Notes and loans payable (short term)", which is in the extract.
- No values are guessed for either.

## Metrics (Phase 2)

Formulas are in `src/hcap/metrics.py`; the rules that prepare their inputs are in
`src/hcap/prepare.py`. Every switch mentioned below is in `config.yaml`.

**Operating margin** = (operating revenue − operating expenses) / operating revenue.
How many cents of each revenue dollar are left after running the hospital. Operating revenue
is net patient revenue only by default, which makes hospitals that rely on tax support, grants
or 340B income look worse than they are. Set `operating_revenue_includes_other_income: true`
to add other income.

**EBIDA** = net income + interest expense + depreciation.
Roughly the cash the hospital generates in a year before paying lenders. It is the pool that
debt payments come out of.

**Days cash on hand** = (cash + short-term investments) / ((total expenses − depreciation) / 365).
How many days the hospital could keep paying its bills if revenue stopped. Hospitals owned by
a health system often sweep cash to the parent every night, so a near-zero figure for a system
hospital says little about the system's liquidity. Long-term investments are not counted.

**Average age of plant** = accumulated depreciation / annual depreciation expense, in years.
How run-down the buildings and equipment are. Higher means older and a bigger capital need.
Depreciation here is the capital-related figure from Worksheet A-7; where a hospital reports
very little of it, the result is implausibly high.

**Debt-to-capitalization** = long-term debt / (long-term debt + net assets).
How much of the hospital's long-term funding is borrowed. Long-term debt is mortgages + notes
+ unsecured loans. It is left blank where any of those is negative (health-system intercompany
balances) or where debt plus net assets is not positive.

**Existing debt service** ≈ interest expense + current portion of long-term debt.
**This is an approximation.** The cost report has no principal-payment line and no
"current portion" line, so short-term notes and loans payable (Worksheet G line 40) stands in.
It can overstate (line 40 includes lines of credit) or understate (system-level debt).

**Medicaid share and Medicare share of days** = that payer's inpatient days / total inpatient days.
A stand-in for payer mix. These day counts are believed to exclude managed-care (HMO) days,
which would understate both shares, Medicaid especially in Missouri. Not yet confirmed.

### Rules applied before the formulas

- **Scope:** short-term acute and critical access hospitals only (`scope.facility_types`).
- **One report per hospital:** the latest. Reports under 180 days are dropped.
- **Partial years:** revenue, expense and other flow amounts are scaled to 365 days.
- **Blanks:** a blank line counts as zero only if the hospital filed that statement.
- **Interest expense:** Worksheet A line 113 + A-7 Part II capital interest. If neither is
  reported, or the total is negative, interest is left blank, and so are EBIDA and debt service.
- **Report version:** where raw HCRIS holds a newer version of a report than the public file,
  all overlapping fields come from HCRIS.

- **Zero interest:** a hospital that reports no interest and shows no debt on its balance
  sheet is assumed to pay none (`assume_zero_interest_when_no_debt`).

Each hospital carries a `flags` column listing which of these caveats apply to it.

## Stress test (Phase 3)

Formulas are in `src/hcap/stress.py`. Every parameter is under `stress:` in `config.yaml`
and is an assumption to tune, not a forecast.

**Headroom** = (EBIDA / target DSCR) − existing debt service.
The extra annual debt or rent payment the hospital could take on and still keep EBIDA at
1.25 times its total payments. Negative means it is already below that cushion.

**Scenarios.** Each one recomputes EBIDA, then headroom. Debt service does not change.

| Scenario | What happens | Default |
|---|---|---|
| Medicaid cut | Medicaid net revenue falls; no expense falls with it | 10% |
| Volume drop | Net patient revenue falls; only the variable share of cash operating expenses falls with it | 10% drop, 40% variable |
| Labor shock | Salary expense rises | 5% |
| Combined | All three, compounding | as above |

- Medicaid revenue is the figure reported on Worksheet S-10 where it is positive and no larger
  than net patient revenue; otherwise Medicaid's share of inpatient days times net patient revenue.
- Cash operating expenses = operating expenses − depreciation − interest.
- Salaries are from Worksheet A and exclude benefits and contract labor, so the labor shock
  is on the light side.

**Stressed headroom** is the lowest of the baseline and the four scenarios.

**Affordable principal** converts stressed headroom to a loan amount for each capital type with
the level-payment annuity formula, principal = payment × (1 − (1 + r)^−n) / r. The rates and
terms under `capital_types:` are **placeholders**, not official program terms or market quotes.

## Capital ladder (Phase 4)

Rules are in `src/hcap/matcher.py`, one small function per rung. No machine learning.
**Every threshold under `capital_ladder:` in `config.yaml` is a placeholder invented for
screening. None is an official eligibility rule of any program, lender or investor.**

| Rung | Screening rule used here |
|---|---|
| 1. Grants / affiliation / Rural Emergency Hospital conversion | Baseline headroom is negative. Also the fallback when headroom is positive but no other rung fits. |
| 2. USDA Community Facilities loan | Baseline headroom is not negative, and the town has 20,000 people or fewer |
| 3. CDFI / New Markets Tax Credits | Baseline headroom is not negative, and the census tract is on the CDFI Fund's NMTC low-income list |
| 4. HUD Section 242 / bank loan | Baseline headroom is at least 2% of patient revenue and stressed headroom stays above zero |
| 5. Tax-exempt municipal bonds | Stressed headroom is at least 3% of patient revenue and net patient revenue is at least $75M |
| 6. Sale-leaseback / REIT capital | Combined-scenario EBIDA covers existing debt service plus an estimated rent at least 2.0 times. Always shown with a warning; never the primary match. |

- **Primary match** is the highest rung a hospital qualifies for. **Alternates** are the other
  rungs it qualifies for. Each rung, met or not, gets a plain-English reason in `match_details`.
- **Cannot assess:** hospitals with no headroom figure (missing interest) get no match.
- **Estimated rent** for rung 6 = 7.5% of the net book value of fixed assets. This is a
  construction of this tool, not how a real lease would be priced.

### Location data

- **Coordinates and census tract:** U.S. Census Bureau geocoder, from the street address.
  The 14 addresses it cannot place are sent to OpenStreetMap's geocoder, which finds 13;
  their tract then comes from a Census coordinate lookup. One hospital (St. Luke's East,
  Lee's Summit) is still unlocated, so its NMTC status is unknown and it is not on the map.
- **Town population:** the incorporated place the address falls in, from the Census Bureau's
  city and town file (April 2020 base). Where the address lies outside town limits or was
  not located, the mailing city's name is matched instead.
- **NMTC low-income tracts:** the CDFI Fund's eligibility dataset (2016-2020 ACS, 2020 tracts).
- A town of 20,000 or fewer is not the same as USDA-eligible: small suburbs of large metro
  areas pass this screen. USDA's own eligibility map is the real test.
- The CMS rural/urban flag in the cost report is not used. It marks Barnes-Jewish Hospital in
  St. Louis as rural, so it is not trusted here.

## Dashboard (Phase 5)

```bash
streamlit run app.py
```

- **Map:** one dot per hospital, coloured by stressed headroom as a share of net patient
  revenue (red = negative, blue = positive, grey = cannot assess). The colour bands are
  `dashboard.headroom_margin_bands` in `config.yaml`.
- **Click a dot** (or use the dropdown under the map) to see that hospital's metrics, its
  headroom under each scenario, what that payment could borrow, and its capital matches
  with the reason for every rung.
- **Sliders** in the left sidebar change the target coverage ratio, the three shock sizes
  and the variable cost share. The stress test and the capital matches are recalculated on
  every change; the Phase 2 metrics are not affected.
- **Table:** every hospital, sortable by clicking a column heading, with a CSV download.
- The page logic lives in `app.py`; everything it calculates is in `src/hcap/dashboard.py`.

### What the stress test cannot see

- Hospitals owned by a health system often show no debt and no interest of their own, because
  the parent borrows. Their debt service reads as zero and their headroom is overstated.
- 25 of the 99 hospitals have no usable interest figure and get no headroom at all.
