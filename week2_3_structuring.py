"""
Week 2-3: Dataset Structuring and Validation
IDX Exchange Internship - Alan Adams

This script:
1. Loads the Week 1 combined + Residential-filtered datasets
2. Reviews structure (rows, columns, dtypes)
3. Runs a missing value analysis (flags >90% null columns)
4. Produces numeric distribution summaries + histograms/boxplots
5. Saves the "structured" dataset as a new CSV
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # lets us save charts without opening a window
import matplotlib.pyplot as plt
import os

# ---------------------------------------------------------
# STEP 0: File paths - EDIT THIS if your folder is different
# ---------------------------------------------------------
DATA_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-raw"
OUTPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

sold_path = os.path.join(DATA_DIR, "combined_sold_residential.csv")
listings_path = os.path.join(DATA_DIR, "combined_listings_residential.csv")

# ---------------------------------------------------------
# STEP 1: Load Week 1 outputs
# ---------------------------------------------------------
sold = pd.read_csv(sold_path, low_memory=False)
listings = pd.read_csv(listings_path, low_memory=False)

print("=" * 60)
print("STEP 1: DATASET SHAPE")
print("=" * 60)
print(f"Sold dataset:     {sold.shape[0]} rows, {sold.shape[1]} columns")
print(f"Listings dataset: {listings.shape[0]} rows, {listings.shape[1]} columns")

# ---------------------------------------------------------
# STEP 2: Column data types
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 2: COLUMN DATA TYPES (Sold dataset)")
print("=" * 60)
print(sold.dtypes)

# ---------------------------------------------------------
# STEP 3: Confirm PropertyType is Residential only (sanity check)
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 3: PROPERTY TYPE CHECK")
print("=" * 60)
print("Unique PropertyType values in Sold:", sold["PropertyType"].unique())
print("Unique PropertyType values in Listings:", listings["PropertyType"].unique())

# ---------------------------------------------------------
# STEP 4: Missing value analysis
# ---------------------------------------------------------
def missing_value_report(df, name):
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df)) * 100
    report = pd.DataFrame({
        "missing_count": missing_count,
        "missing_pct": missing_pct.round(2)
    }).sort_values("missing_pct", ascending=False)

    print(f"\n--- Missing Value Report: {name} ---")
    print(report[report["missing_count"] > 0])

    flagged = report[report["missing_pct"] > 90]
    print(f"\nColumns with >90% missing in {name}:")
    print(flagged if not flagged.empty else "None")

    report.to_csv(os.path.join(OUTPUT_DIR, f"missing_value_report_{name}.csv"))
    return report

print("\n" + "=" * 60)
print("STEP 4: MISSING VALUE ANALYSIS")
print("=" * 60)
sold_missing = missing_value_report(sold, "sold")
listings_missing = missing_value_report(listings, "listings")

# ---------------------------------------------------------
# STEP 5: Numeric distribution review (Sold dataset)
# ---------------------------------------------------------
numeric_fields = [
    "ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
    "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt"
]

# Only keep fields that actually exist in your dataset
numeric_fields = [f for f in numeric_fields if f in sold.columns]

print("\n" + "=" * 60)
print("STEP 5: NUMERIC DISTRIBUTION SUMMARY")
print("=" * 60)

summary_rows = []
for field in numeric_fields:
    col = pd.to_numeric(sold[field], errors="coerce")
    summary_rows.append({
        "field": field,
        "min": col.min(),
        "p25": col.quantile(0.25),
        "median": col.median(),
        "mean": col.mean(),
        "p75": col.quantile(0.75),
        "p95": col.quantile(0.95),
        "max": col.max(),
    })

    # Histogram
    plt.figure(figsize=(6, 4))
    col.dropna().hist(bins=40)
    plt.title(f"Histogram: {field}")
    plt.xlabel(field)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"hist_{field}.png"))
    plt.close()

    # Boxplot
    plt.figure(figsize=(4, 5))
    col.dropna().plot(kind="box")
    plt.title(f"Boxplot: {field}")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"box_{field}.png"))
    plt.close()

dist_summary = pd.DataFrame(summary_rows)
print(dist_summary)
dist_summary.to_csv(os.path.join(OUTPUT_DIR, "numeric_distribution_summary.csv"), index=False)

# ---------------------------------------------------------
# STEP 6: Quick EDA answers (Suggested Intern Questions)
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 6: QUICK EDA ANSWERS")
print("=" * 60)

print(f"Median ClosePrice: {sold['ClosePrice'].median():,.0f}")
print(f"Average ClosePrice: {sold['ClosePrice'].mean():,.0f}")

if "DaysOnMarket" in sold.columns:
    print(f"Median Days on Market: {sold['DaysOnMarket'].median()}")

if "ListPrice" in sold.columns:
    sold["_sold_above_list"] = sold["ClosePrice"] > sold["ListPrice"]
    pct_above = sold["_sold_above_list"].mean() * 100
    print(f"% of homes sold above list price: {pct_above:.1f}%")

if "ListingContractDate" in sold.columns and "CloseDate" in sold.columns:
    listing_dt = pd.to_datetime(sold["ListingContractDate"], errors="coerce")
    close_dt = pd.to_datetime(sold["CloseDate"], errors="coerce")
    date_issue_count = (close_dt < listing_dt).sum()
    print(f"Records where CloseDate is before ListingContractDate: {date_issue_count}")

if "CountyOrParish" in sold.columns:
    top_counties = sold.groupby("CountyOrParish")["ClosePrice"].median().sort_values(ascending=False).head(10)
    print("\nTop 10 counties by median ClosePrice:")
    print(top_counties)

# ---------------------------------------------------------
# STEP 7: Save the structured/validated dataset
# ---------------------------------------------------------
sold_out_path = os.path.join(OUTPUT_DIR, "structured_sold.csv")
listings_out_path = os.path.join(OUTPUT_DIR, "structured_listings.csv")

sold.to_csv(sold_out_path, index=False)
listings.to_csv(listings_out_path, index=False)

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print(f"Saved: {sold_out_path}")
print(f"Saved: {listings_out_path}")
print(f"Charts + reports saved in: {OUTPUT_DIR}")