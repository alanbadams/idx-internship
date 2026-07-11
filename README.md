# IDX Exchange Data Analyst Internship — Alan Adams

## Project Overview

This repository contains my work for the IDX Exchange Data Analyst Internship
(Summer 2026, Team DA34). The project analyzes CRMLS (California Regional
Multiple Listing Service) residential real estate transaction data — Sold and
active Listing records from January 2024 through the most recently completed
month — and builds it into a clean, analysis-ready pipeline that will feed
Tableau dashboards later in the program.

## Objectives

- Aggregate monthly MLS CSV exports into unified Sold and Listings datasets
- Validate and clean the data (structure, missing values, outliers, date
  consistency, geographic accuracy)
- Enrich the data with the national 30-year fixed mortgage rate (FRED) to add
  economic context to price and volume trends
- Engineer key market metrics (price ratio, price per sq ft, days on market,
  etc.)
- Build Tableau dashboards summarizing market activity and competitive
  brokerage/agent performance
- Deliver a 1-page market intelligence report and a final presentation

## Repository Structure

```
idx-internship/
├── README.md
├── .gitignore
├── week1_aggregation.py
├── week2_3_structuring.py
└── week2_3_mortgage_enrichment.py
```

Note: raw and processed CSV data files are **not** included in this repository.
All MLS transaction data is confidential per IDX Exchange internship policy and
is kept locally only. See "Data" section below.

## Scripts

### `week1_aggregation.py`
Loads all monthly `CRMLSSold*.csv` and `CRMLSListing*.csv` files, concatenates
them into two combined datasets, and filters both down to `PropertyType ==
'Residential'`. Outputs `combined_sold_residential.csv` and
`combined_listings_residential.csv`.

### `week2_3_structuring.py`
Loads the Week 1 outputs and:
- Reviews dataset shape, column types, and confirms the Residential filter
- Runs a missing value analysis and flags any column above 90% missing
- Produces numeric distribution summaries (min/percentiles/mean/max) plus
  histograms and boxplots for ClosePrice, ListPrice, OriginalListPrice,
  LivingArea, LotSizeAcres, BedroomsTotal, BathroomsTotalInteger,
  DaysOnMarket, and YearBuilt
- Answers baseline EDA questions (median/average close price, % sold above
  list, date-order issues, top counties by price)
- Saves `structured_sold.csv` and `structured_listings.csv`

### `week2_3_mortgage_enrichment.py`
Loads the structured datasets from the script above and:
- Pulls the FRED `MORTGAGE30US` weekly mortgage rate series
- Resamples it to a monthly average
- Merges the monthly rate onto both datasets using a `year_month` key
  (derived from `CloseDate` for Sold, `ListingContractDate` for Listings)
- Validates that no rows are missing a rate after the merge
- Saves `sold_with_mortgage_rates.csv` and `listings_with_mortgage_rates.csv`

## Data

This project uses CRMLS Sold and Listing data provided through the IDX
Exchange internship's FTP server and extraction scripts. **Raw and processed
data files are confidential and are excluded from this repository** (see
`.gitignore`). To run these scripts yourself, you'll need your own local copy
of the source CSVs, placed in a `CSV-raw/` folder as described below.

## How to Run

### Requirements
- Python 3
- pandas
- matplotlib

Install dependencies:
```bash
pip install pandas matplotlib --break-system-packages
```

### Folder setup
These scripts expect the following local folder structure (adjust the
`DATA_DIR` / `OUTPUT_DIR` paths at the top of each script if yours is
different):
```
IDX_Internship/
├── CSV-raw/        (place source CSVs here — not tracked in git)
└── CSV-output/      (script outputs are written here — not tracked in git)
```

### Run order
The scripts must be run in this order, since each one depends on the output
of the previous:

```bash
python3 week1_aggregation.py
python3 week2_3_structuring.py
python3 week2_3_mortgage_enrichment.py
```

Each script prints its progress step by step to the terminal (STEP 1, STEP 2,
etc.) and writes its outputs to `CSV-output/`.

## Team

**Team DA34**
- Alan Adams — Team Lead
- Anna Cen
- Charith Dasari
- Claire Liu
- Yue Gao

Coach/Mentors: Justin Ha, Yoora Choi, Yoshika Ino
Program Manager: Aidan Nguyen

## Status

- [x] Week 1 — Monthly dataset aggregation
- [x] Weeks 2–3 — Dataset structuring and validation
- [x] Weeks 2–3 — Mortgage rate enrichment
- [ ] Weeks 4–5 — Data cleaning and preparation
- [ ] Week 6 — Feature engineering and market metrics
- [ ] Week 7 — Outlier detection (IQR)
- [ ] Weeks 8–10 — Tableau dashboard development
- [ ] Weeks 11–12 — Final presentation and market intelligence report
