"""
Week 2-3: Mortgage Rate Enrichment (FRED API)
IDX Exchange Internship - Alan Adams

This script:
1. Fetches the FRED MORTGAGE30US weekly series
2. Resamples it to monthly averages
3. Merges it onto the structured Sold and Listings datasets via a year_month key
4. Validates that no rows are missing a rate after the merge
5. Saves both enriched datasets as new CSVs
"""

import pandas as pd
import os

# ---------------------------------------------------------
# STEP 0: File paths - EDIT THIS if your folder is different
# ---------------------------------------------------------
OUTPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"

sold_path = os.path.join(OUTPUT_DIR, "structured_sold.csv")
listings_path = os.path.join(OUTPUT_DIR, "structured_listings.csv")

sold = pd.read_csv(sold_path, low_memory=False)
listings = pd.read_csv(listings_path, low_memory=False)

# ---------------------------------------------------------
# STEP 1: Fetch mortgage rate data from FRED
# ---------------------------------------------------------
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=["observation_date"])
mortgage.columns = ["date", "rate_30yr_fixed"]

print("=" * 60)
print("STEP 1: RAW FRED DATA (first 5 rows)")
print("=" * 60)
print(mortgage.head())

# ---------------------------------------------------------
# STEP 2: Resample weekly rates to monthly averages
# ---------------------------------------------------------
mortgage["year_month"] = mortgage["date"].dt.to_period("M")
mortgage_monthly = (
    mortgage.groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .reset_index()
)

print("\n" + "=" * 60)
print("STEP 2: MONTHLY AVERAGE RATES (first 5 rows)")
print("=" * 60)
print(mortgage_monthly.head())

# ---------------------------------------------------------
# STEP 3: Create matching year_month key on MLS datasets
# ---------------------------------------------------------
sold["year_month"] = pd.to_datetime(sold["CloseDate"], errors="coerce").dt.to_period("M")
listings["year_month"] = pd.to_datetime(
    listings["ListingContractDate"], errors="coerce"
).dt.to_period("M")

# ---------------------------------------------------------
# STEP 4: Merge
# ---------------------------------------------------------
sold_with_rates = sold.merge(mortgage_monthly, on="year_month", how="left")
listings_with_rates = listings.merge(mortgage_monthly, on="year_month", how="left")

# ---------------------------------------------------------
# STEP 5: Validate the merge
# ---------------------------------------------------------
sold_nulls = sold_with_rates["rate_30yr_fixed"].isnull().sum()
listings_nulls = listings_with_rates["rate_30yr_fixed"].isnull().sum()

print("\n" + "=" * 60)
print("STEP 5: VALIDATION - NULL RATE CHECK")
print("=" * 60)
print(f"Sold rows with missing rate_30yr_fixed:     {sold_nulls}")
print(f"Listings rows with missing rate_30yr_fixed: {listings_nulls}")

if sold_nulls > 0:
    missing_months = sold_with_rates.loc[
        sold_with_rates["rate_30yr_fixed"].isnull(), "year_month"
    ].unique()
    print(f"Sold - months with no matching rate: {missing_months}")

if listings_nulls > 0:
    missing_months = listings_with_rates.loc[
        listings_with_rates["rate_30yr_fixed"].isnull(), "year_month"
    ].unique()
    print(f"Listings - months with no matching rate: {missing_months}")

# ---------------------------------------------------------
# STEP 6: Preview
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 6: PREVIEW - SOLD WITH RATES")
print("=" * 60)
preview_cols = [c for c in ["CloseDate", "year_month", "ClosePrice", "rate_30yr_fixed"] if c in sold_with_rates.columns]
print(sold_with_rates[preview_cols].head())

# ---------------------------------------------------------
# STEP 7: Save enriched datasets
# ---------------------------------------------------------
sold_out = os.path.join(OUTPUT_DIR, "sold_with_mortgage_rates.csv")
listings_out = os.path.join(OUTPUT_DIR, "listings_with_mortgage_rates.csv")

sold_with_rates.to_csv(sold_out, index=False)
listings_with_rates.to_csv(listings_out, index=False)

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print(f"Saved: {sold_out}")
print(f"Saved: {listings_out}")