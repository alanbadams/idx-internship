# IDX Exchange Data Analyst Internship — Alan Adams

## Project Overview
This repository contains my work for the IDX Exchange Data Analyst Internship (Summer 2026, Team DA34). The project analyzes CRMLS (California Regional Multiple Listing Service) residential real estate transaction data — Sold and active Listing records from January 2024 through June 2026 — and builds it into a clean, analysis-ready pipeline feeding two published Tableau dashboards.

**Final deliverable:** A Market Intelligence Report comparing three Riverside County ZIP codes — Murrieta (92562) as a suburban commuter market versus La Quinta (92253) and Rancho Mirage (92270) as a luxury desert resort corridor.

## Dashboards
- **Market Analysis:** [Market Analysis on Tableau Public](https://public.tableau.com/views/market_analysis_17865599253950/MarketAnalysis) — monthly median close price, average days on market, close-to-original-list ratio, new listings, and closed sales, filterable by city/county/ZIP and property subtype
- **Competitive Analysis:** [Competitive Analysis on Tableau Public](https://public.tableau.com/views/competetive_analysis/CompetitiveAnalysis) — top 100 listing agents and offices by volume/units, and ZIP-code heat maps of median close price and homes sold

## Resume
A copy of my resume is available at [github.com/alanbadams/resume](https://github.com/alanbadams/resume).

## Objectives
- Aggregate monthly MLS CSV exports into unified Sold and Listings datasets
- Validate and clean the data (structure, missing values, outliers, date consistency, geographic accuracy)
- Enrich the data with the national 30-year fixed mortgage rate (FRED) to add economic context to price and volume trends
- Engineer key market metrics (price ratio, price per sq ft, days on market, etc.)
- Detect and flag statistical outliers (IQR method) to produce analysis-ready filtered datasets
- Build Tableau dashboards summarizing market activity and competitive brokerage/agent performance
- Deliver a 1-page market intelligence report and a final presentation

## Repository Structure
```
idx-internship/
├── README.md
├── .gitignore
├── week1_aggregation.py
├── week2_3_structuring.py
├── week2_3_mortgage_enrichment.py
├── week4_5_cleaning.py
├── week6_feature_engineering.py
└── week7_outlier_detection.py
```
Note: raw and processed CSV data files are not included in this repository. All MLS transaction data is confidential per IDX Exchange internship policy and is kept locally only. See "Data" section below.

## Scripts

**week1_aggregation.py**
Loads all monthly `CRMLSSold*.csv` and `CRMLSListing*.csv` files, concatenates them into two combined datasets, and filters both down to `PropertyType == 'Residential'`. Outputs `combined_sold_residential.csv` and `combined_listings_residential.csv`.

**week2_3_structuring.py**
Loads the Week 1 outputs and:
- Reviews dataset shape, column types, and confirms the Residential filter
- Runs a missing value analysis and flags any column above 90% missing
- Produces numeric distribution summaries (min/percentiles/mean/max) plus histograms and boxplots for ClosePrice, ListPrice, OriginalListPrice, LivingArea, LotSizeAcres, BedroomsTotal, BathroomsTotalInteger, DaysOnMarket, and YearBuilt
- Answers baseline EDA questions (median/average close price, % sold above list, date-order issues, top counties by price)
- Saves `structured_sold.csv` and `structured_listings.csv`

**week2_3_mortgage_enrichment.py**
Loads the structured datasets from the script above and:
- Pulls the FRED `MORTGAGE30US` weekly mortgage rate series
- Resamples it to a monthly average
- Merges the monthly rate onto both datasets using a `year_month` key (derived from CloseDate for Sold, ListingContractDate for Listings)
- Validates that no rows are missing a rate after the merge
- Saves `sold_with_mortgage_rates.csv` and `listings_with_mortgage_rates.csv`

**week4_5_cleaning.py**
Loads the mortgage-enriched datasets and:
- Converts date fields to proper datetime type and coerces numeric fields
- Flags (does not delete) invalid numeric values — ClosePrice <= 0, LivingArea <= 0, DaysOnMarket < 0, negative bed/bath counts
- Flags date-order inconsistencies across ListingContractDate, PurchaseContractDate, and CloseDate
- Flags geographic data quality issues using a California bounding box (missing coordinates, 0/0 sentinel values, longitude sign errors)
- Saves `cleaned_sold.csv` and `cleaned_listings.csv`, with all original rows preserved

**week6_feature_engineering.py**
Loads the cleaned datasets and:
- Engineers price ratio, close-to-original-list ratio, and price per square foot
- Calculates listing-to-contract days and contract-to-close days
- Derives Year / Month / YrMo fields from CloseDate for time-series analysis
- Performs a GeoPandas spatial join against 2025–26 CA Unified School District boundaries to map each property to its district
- Produces segment summaries by PropertyType/PropertySubType, CountyOrParish/MLSAreaMajor, and ListOfficeName/BuyerOfficeName
- Saves `featured_sold.csv` and `featured_listings.csv`

**week7_outlier_detection.py**
Loads the featured datasets and:
- Applies the IQR method to ClosePrice, LivingArea, and DaysOnMarket to identify statistical outliers
- Adds per-field boolean outlier flag columns plus a combined `any_outlier_flag` — no rows are deleted from the flagged output
- Saves full flagged datasets (`sold_outliers_flagged.csv`, `listings_outliers_flagged.csv`) with every row preserved
- Builds and saves separate, analysis-ready filtered datasets with outlier rows excluded (`sold_filtered.csv`, `listings_filtered.csv`)
- Reports median values before vs. after filtering for comparison

## Data
This project uses CRMLS Sold and Listing data provided through the IDX Exchange internship's FTP server and extraction scripts. Raw and processed data files are confidential and are excluded from this repository (see `.gitignore`). To run these scripts yourself, you'll need your own local copy of the source CSVs, placed in a `CSV-raw/` folder as described below.

## How to Run

**Requirements**
- Python 3
- pandas
- matplotlib
- geopandas

Install dependencies:
```
pip install pandas matplotlib geopandas --break-system-packages
```

**Folder setup**
These scripts expect the following local folder structure (adjust the `DATA_DIR` / `OUTPUT_DIR` paths at the top of each script if yours is different):
```
IDX_Internship/
├── CSV-raw/       (place source CSVs here — not tracked in git)
└── CSV-output/    (script outputs are written here — not tracked in git)
```

**Run order**
The scripts must be run in this order, since each one depends on the output of the previous:
```
python3 week1_aggregation.py
python3 week2_3_structuring.py
python3 week2_3_mortgage_enrichment.py
python3 week4_5_cleaning.py
python3 week6_feature_engineering.py
python3 week7_outlier_detection.py
```
Each script prints its progress step by step to the terminal (STEP 0, STEP 1, etc.) and writes its outputs to `CSV-output/`.

## Team
**Team DA34**
- Alan Adams — Team Lead
- Charith Dasari
- Claire Liu
- Yue Gao

Coach/Mentors: Justin Ha, Yoora Choi, Yoshika Ino
Program Manager: Aidan Nguyen

## Status
- [x] Week 1 — Monthly dataset aggregation
- [x] Weeks 2–3 — Dataset structuring and validation
- [x] Weeks 2–3 — Mortgage rate enrichment
- [x] Weeks 4–5 — Data cleaning and preparation
- [x] Week 6 — Feature engineering and market metrics
- [x] Week 7 — Outlier detection (IQR)
- [x] Weeks 8–10 — Tableau dashboard development
- [x] Weeks 11–12 — Final presentation and market intelligence report
