# Hospital capital stress test (Missouri pilot)

Screens each hospital's finances from public CMS data, estimates how much new annual
debt or rent payment it could carry, reruns that under stress, and matches it to a rung
on a capital ladder. Built in phases. **Phase 1 (data ingestion) is done; Phases 2-5 are not built yet.**

Screening and educational tool only. Not financial, investment, or municipal advisory advice.
Based on public data that may be 1-2 years old.

## Run it

```bash
pip install -r requirements.txt
python scripts/phase1.py     # downloads CMS files, builds data/hospitals.duckdb, writes the quality report
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

## Metrics

To be written in Phase 2, one plain-English paragraph per metric.
