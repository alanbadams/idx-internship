"""
Week 4-5: Data Cleaning and Preparation
IDX Exchange Internship - Alan Adams

This script:
1. Loads the mortgage-enriched Sold and Listings datasets (Week 2-3 output)
2. Converts date fields to proper datetime format
3. Ensures numeric fields are properly typed
4. Flags invalid numeric values (does NOT delete records)
5. Flags date-order inconsistencies (listing -> purchase -> close)
6. Flags geographic data quality issues
7. Saves a cleaned, analysis-ready dataset as a new CSV
"""

import pandas as pd
import os

# ---------------------------------------------------------
# STEP 0: File paths - EDIT THIS if your folder is different
# ---------------------------------------------------------
OUTPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"

sold_path = os.path.join(OUTPUT_DIR, "sold_with_mortgage_rates.csv")
listings_path = os.path.join(OUTPUT_DIR, "listings_with_mortgage_rates.csv")

sold = pd.read_csv(sold_path, low_memory=False)
listings = pd.read_csv(listings_path, low_memory=False)

print("=" * 60)
print("STEP 0: STARTING ROW COUNTS")
print("=" * 60)
print(f"Sold dataset:     {sold.shape[0]} rows, {sold.shape[1]} columns")
print(f"Listings dataset: {listings.shape[0]} rows, {listings.shape[1]} columns")

# ---------------------------------------------------------
# STEP 1: Convert date fields to datetime
# ---------------------------------------------------------
date_fields = [
    "ListingContractDate", "PurchaseContractDate",
    "CloseDate", "ContractStatusChangeDate"
]

print("\n" + "=" * 60)
print("STEP 1: DATE FIELD CONVERSION")
print("=" * 60)

for field in date_fields:
    for df, name in [(sold, "sold"), (listings, "listings")]:
        if field in df.columns:
            before_nulls = df[field].isnull().sum()
            df[field] = pd.to_datetime(df[field], errors="coerce")
            after_nulls = df[field].isnull().sum()
            print(f"[{name}] {field}: converted to datetime "
                  f"(nulls before: {before_nulls}, after: {after_nulls})")
        else:
            print(f"[{name}] {field}: not found in columns - skipped")

# ---------------------------------------------------------
# STEP 2: Ensure numeric fields are properly typed
# ---------------------------------------------------------
numeric_fields = [
    "ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
    "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt", "Latitude", "Longitude"
]

print("\n" + "=" * 60)
print("STEP 2: NUMERIC TYPE CONFIRMATION")
print("=" * 60)

for field in numeric_fields:
    for df, name in [(sold, "sold"), (listings, "listings")]:
        if field in df.columns:
            before_dtype = df[field].dtype
            df[field] = pd.to_numeric(df[field], errors="coerce")
            print(f"[{name}] {field}: {before_dtype} -> {df[field].dtype}")

# ---------------------------------------------------------
# STEP 3: Flag invalid numeric values (flag, do not delete)
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 3: INVALID NUMERIC VALUE FLAGS")
print("=" * 60)

def flag_invalid_numeric(df, name):
    if "ClosePrice" in df.columns:
        df["invalid_closeprice_flag"] = df["ClosePrice"] <= 0
    if "LivingArea" in df.columns:
        df["invalid_livingarea_flag"] = df["LivingArea"] <= 0
    if "DaysOnMarket" in df.columns:
        df["invalid_dom_flag"] = df["DaysOnMarket"] < 0
    if "BedroomsTotal" in df.columns:
        df["invalid_bedrooms_flag"] = df["BedroomsTotal"] < 0
    if "BathroomsTotalInteger" in df.columns:
        df["invalid_bathrooms_flag"] = df["BathroomsTotalInteger"] < 0

    flag_cols = [c for c in df.columns if c.startswith("invalid_")]
    print(f"\n--- {name} ---")
    for col in flag_cols:
        print(f"{col}: {df[col].sum()} flagged rows")
    return df

sold = flag_invalid_numeric(sold, "sold")
listings = flag_invalid_numeric(listings, "listings")

# ---------------------------------------------------------
# STEP 4: Date consistency checks
# ---------------------------------------------------------
# Expected order: ListingContractDate -> PurchaseContractDate -> CloseDate
#
# listing_after_close_flag  = ListingContractDate is after CloseDate (impossible)
# purchase_after_close_flag = PurchaseContractDate is after CloseDate (impossible)
# negative_timeline_flag    = ListingContractDate is after PurchaseContractDate
#                             (contract signed before the listing agreement - impossible)
print("\n" + "=" * 60)
print("STEP 4: DATE CONSISTENCY FLAGS")
print("=" * 60)

def flag_date_consistency(df, name):
    has_listing = "ListingContractDate" in df.columns
    has_purchase = "PurchaseContractDate" in df.columns
    has_close = "CloseDate" in df.columns

    if has_listing and has_close:
        df["listing_after_close_flag"] = df["ListingContractDate"] > df["CloseDate"]
    if has_purchase and has_close:
        df["purchase_after_close_flag"] = df["PurchaseContractDate"] > df["CloseDate"]
    if has_listing and has_purchase:
        df["negative_timeline_flag"] = df["ListingContractDate"] > df["PurchaseContractDate"]

    print(f"\n--- {name} ---")
    for col in ["listing_after_close_flag", "purchase_after_close_flag", "negative_timeline_flag"]:
        if col in df.columns:
            print(f"{col}: {df[col].sum()} flagged rows")
        else:
            print(f"{col}: skipped (required date fields not present)")
    return df

sold = flag_date_consistency(sold, "sold")
listings = flag_date_consistency(listings, "listings")

# ---------------------------------------------------------
# STEP 5: Geographic data checks
# ---------------------------------------------------------
# CA bounding box used for the "implausible coordinates" flag:
# Latitude  roughly 32.5 to 42.0
# Longitude roughly -124.5 to -114.0
print("\n" + "=" * 60)
print("STEP 5: GEOGRAPHIC DATA QUALITY FLAGS")
print("=" * 60)

def flag_geo_quality(df, name):
    has_lat = "Latitude" in df.columns
    has_lon = "Longitude" in df.columns

    if has_lat and has_lon:
        df["missing_coords_flag"] = df["Latitude"].isnull() | df["Longitude"].isnull()
        df["zero_coords_flag"] = (df["Latitude"] == 0) | (df["Longitude"] == 0)
        df["positive_longitude_flag"] = df["Longitude"] > 0
        df["implausible_coords_flag"] = (
            (df["Latitude"] < 32.5) | (df["Latitude"] > 42.0) |
            (df["Longitude"] < -124.5) | (df["Longitude"] > -114.0)
        ) & ~df["missing_coords_flag"]

    print(f"\n--- {name} ---")
    for col in ["missing_coords_flag", "zero_coords_flag",
                "positive_longitude_flag", "implausible_coords_flag"]:
        if col in df.columns:
            print(f"{col}: {df[col].sum()} flagged rows")
        else:
            print(f"{col}: skipped (Latitude/Longitude not present)")
    return df

sold = flag_geo_quality(sold, "sold")
listings = flag_geo_quality(listings, "listings")

# ---------------------------------------------------------
# STEP 6: Missing value summary (for core analysis fields only)
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 6: MISSING VALUE SUMMARY (core fields)")
print("=" * 60)

core_fields = [f for f in (numeric_fields + date_fields) if f in sold.columns]
core_missing = sold[core_fields].isnull().sum()
print("--- sold ---")
print(core_missing[core_missing > 0] if core_missing.sum() > 0 else "No missing values in core fields")

# ---------------------------------------------------------
# STEP 7: Save cleaned, analysis-ready datasets
# ---------------------------------------------------------
sold_out_path = os.path.join(OUTPUT_DIR, "cleaned_sold.csv")
listings_out_path = os.path.join(OUTPUT_DIR, "cleaned_listings.csv")

sold.to_csv(sold_out_path, index=False)
listings.to_csv(listings_out_path, index=False)

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print(f"Sold dataset (final):     {sold.shape[0]} rows, {sold.shape[1]} columns")
print(f"Listings dataset (final): {listings.shape[0]} rows, {listings.shape[1]} columns")
print(f"Saved: {sold_out_path}")
print(f"Saved: {listings_out_path}")