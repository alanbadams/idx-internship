"""
IDX Exchange Internship - Week 7: Outlier Detection and Data Quality
Team: DA34 | Team Lead: Alan Adams

Builds on Week 6 outputs: featured_sold.csv and featured_listings.csv
Produces:
    - sold_outliers_flagged.csv       (ALL rows, nothing removed, flag columns added)
    - listings_outliers_flagged.csv   (ALL rows, nothing removed, flag columns added)
    - sold_filtered.csv               (outlier rows excluded - analysis-ready)
    - listings_filtered.csv           (outlier rows excluded - analysis-ready)

Method: Interquartile Range (IQR) on ClosePrice, LivingArea, DaysOnMarket.
We flag first, then build a SEPARATE filtered dataset. The raw flagged
dataset is preserved in full - consistent with the no-deletion approach
used in Weeks 4-5.

NOTE: DaysOnMarket only exists in a meaningful, populated way on the SOLD
dataset (active listings don't have a completed DOM the same way). We still
check for the column on listings and skip the flag/filter step for it there
if it isn't present or is entirely null, rather than erroring out.
"""

import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

INPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"
OUTPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"

SOLD_IN = f"{INPUT_DIR}/featured_sold.csv"
LISTINGS_IN = f"{INPUT_DIR}/featured_listings.csv"

SOLD_FLAGGED_OUT = f"{OUTPUT_DIR}/sold_outliers_flagged.csv"
LISTINGS_FLAGGED_OUT = f"{OUTPUT_DIR}/listings_outliers_flagged.csv"
SOLD_FILTERED_OUT = f"{OUTPUT_DIR}/sold_filtered.csv"
LISTINGS_FILTERED_OUT = f"{OUTPUT_DIR}/listings_filtered.csv"

# Fields to run IQR outlier detection on, per the handbook
IQR_FIELDS = ["ClosePrice", "LivingArea", "DaysOnMarket"]


def print_header(step_name):
    print("\n" + "=" * 70)
    print(step_name)
    print("=" * 70)


def iqr_bounds(series):
    """Return (lower, upper) IQR bounds for a numeric series, ignoring NaNs."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return lower, upper


def add_iqr_flags(df, fields, dataset_label):
    """
    For each field in `fields` that exists and has usable data in df,
    add a boolean flag column '<field>_outlier_flag'. Rows with NaN in the
    field are NOT flagged as outliers (missingness is a separate issue,
    already handled in Weeks 2-5).

    Returns the modified df and a dict of bounds/counts for reporting.
    """
    report = {}
    for field in fields:
        if field not in df.columns:
            print(f"  [{dataset_label}] Skipping '{field}' - column not present.")
            continue

        non_null_count = df[field].notna().sum()
        if non_null_count == 0:
            print(f"  [{dataset_label}] Skipping '{field}' - column is entirely null.")
            continue

        lower, upper = iqr_bounds(df[field])
        flag_col = f"{field}_outlier_flag"

        # Flag = True only when the value is present AND outside bounds.
        df[flag_col] = df[field].notna() & ((df[field] < lower) | (df[field] > upper))

        flagged_count = df[flag_col].sum()
        report[field] = {
            "lower": lower,
            "upper": upper,
            "flagged_count": int(flagged_count),
            "flagged_pct": round(100 * flagged_count / len(df), 2),
        }

        print(f"  [{dataset_label}] {field}: bounds=({lower:,.2f}, {upper:,.2f}) "
              f"-> {flagged_count:,} flagged ({report[field]['flagged_pct']}%)")

    return df, report


# ============================================================
# STEP 0: LOAD WEEK 6 OUTPUTS
# ============================================================
print_header("STEP 0: LOADING FEATURED DATASETS")

sold = pd.read_csv(SOLD_IN, low_memory=False)
listings = pd.read_csv(LISTINGS_IN, low_memory=False)

print(f"Loaded featured_sold.csv     -> {len(sold):,} rows, {sold.shape[1]} columns")
print(f"Loaded featured_listings.csv -> {len(listings):,} rows, {listings.shape[1]} columns")

# ============================================================
# STEP 1: MEDIANS BEFORE FILTERING (baseline for comparison)
# ============================================================
print_header("STEP 1: BASELINE MEDIANS (BEFORE OUTLIER FILTERING)")

baseline_medians = {}
for label, df in [("sold", sold), ("listings", listings)]:
    baseline_medians[label] = {}
    print(f"\n  {label.upper()}:")
    for field in IQR_FIELDS:
        if field in df.columns and df[field].notna().sum() > 0:
            med = df[field].median()
            baseline_medians[label][field] = med
            print(f"    {field} median: {med:,.2f}")
        else:
            print(f"    {field}: not available")

# ============================================================
# STEP 2: APPLY IQR OUTLIER FLAGGING (SOLD)
# ============================================================
print_header("STEP 2: IQR OUTLIER FLAGGING - SOLD DATASET")

sold, sold_report = add_iqr_flags(sold, IQR_FIELDS, "sold")

# Combined flag: True if a row is an outlier on ANY of the checked fields
sold_flag_cols = [c for c in sold.columns if c.endswith("_outlier_flag")]
sold["any_outlier_flag"] = sold[sold_flag_cols].any(axis=1) if sold_flag_cols else False

print(f"\n  Rows flagged as outlier on at least one field: "
      f"{sold['any_outlier_flag'].sum():,} of {len(sold):,} "
      f"({100 * sold['any_outlier_flag'].mean():.2f}%)")

# ============================================================
# STEP 3: APPLY IQR OUTLIER FLAGGING (LISTINGS)
# ============================================================
print_header("STEP 3: IQR OUTLIER FLAGGING - LISTINGS DATASET")

listings, listings_report = add_iqr_flags(listings, IQR_FIELDS, "listings")

listings_flag_cols = [c for c in listings.columns if c.endswith("_outlier_flag")]
listings["any_outlier_flag"] = listings[listings_flag_cols].any(axis=1) if listings_flag_cols else False

print(f"\n  Rows flagged as outlier on at least one field: "
      f"{listings['any_outlier_flag'].sum():,} of {len(listings):,} "
      f"({100 * listings['any_outlier_flag'].mean():.2f}%)")

# ============================================================
# STEP 4: SAVE FULL FLAGGED DATASETS (NOTHING REMOVED)
# ============================================================
print_header("STEP 4: SAVING FULL FLAGGED DATASETS")

sold.to_csv(SOLD_FLAGGED_OUT, index=False)
listings.to_csv(LISTINGS_FLAGGED_OUT, index=False)

print(f"Saved: {SOLD_FLAGGED_OUT} -> {len(sold):,} rows")
print(f"Saved: {LISTINGS_FLAGGED_OUT} -> {len(listings):,} rows")

# ============================================================
# STEP 5: BUILD FILTERED (ANALYSIS-READY) DATASETS
# ============================================================
print_header("STEP 5: BUILDING FILTERED DATASETS (OUTLIERS EXCLUDED)")

sold_filtered = sold[~sold["any_outlier_flag"]].copy()
listings_filtered = listings[~listings["any_outlier_flag"]].copy()

print(f"  Sold:     {len(sold):,} -> {len(sold_filtered):,} rows "
      f"({len(sold) - len(sold_filtered):,} removed)")
print(f"  Listings: {len(listings):,} -> {len(listings_filtered):,} rows "
      f"({len(listings) - len(listings_filtered):,} removed)")

sold_filtered.to_csv(SOLD_FILTERED_OUT, index=False)
listings_filtered.to_csv(LISTINGS_FILTERED_OUT, index=False)

print(f"\nSaved: {SOLD_FILTERED_OUT} -> {len(sold_filtered):,} rows")
print(f"Saved: {LISTINGS_FILTERED_OUT} -> {len(listings_filtered):,} rows")

# ============================================================
# STEP 6: WRITTEN COMPARISON - BEFORE VS. AFTER
# ============================================================
print_header("STEP 6: MEDIAN COMPARISON - BEFORE VS. AFTER FILTERING")

for label, before_df, after_df in [
    ("sold", sold, sold_filtered),
    ("listings", listings, listings_filtered),
]:
    print(f"\n  {label.upper()}  (n={len(before_df):,} -> n={len(after_df):,})")
    print(f"  {'Field':<15}{'Median Before':>18}{'Median After':>18}{'Change':>12}")
    for field in IQR_FIELDS:
        if field not in before_df.columns or before_df[field].notna().sum() == 0:
            continue
        med_before = before_df[field].median()
        med_after = after_df[field].median() if field in after_df.columns else np.nan
        change = med_after - med_before if pd.notna(med_after) else np.nan
        print(f"  {field:<15}{med_before:>18,.2f}{med_after:>18,.2f}{change:>12,.2f}")

# ============================================================
# STEP 7: SUMMARY
# ============================================================
print_header("STEP 7: SUMMARY")

print("Full flagged datasets (all rows preserved, flags added):")
print(f"  {SOLD_FLAGGED_OUT}")
print(f"  {LISTINGS_FLAGGED_OUT}")
print("\nFiltered analysis-ready datasets (outlier rows excluded):")
print(f"  {SOLD_FILTERED_OUT}")
print(f"  {LISTINGS_FILTERED_OUT}")
print("\nWeek 7 complete.")
