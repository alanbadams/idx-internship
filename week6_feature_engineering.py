"""
IDX Exchange Internship — Week 6: Feature Engineering and Market Metrics
Team: DA34 | Team Lead: Alan Adams

Builds on Weeks 4-5 outputs: cleaned_sold.csv and cleaned_listings.csv
Produces: featured_sold.csv and featured_listings.csv

Nothing is dropped from the cleaned datasets in this step. We are ADDING
engineered columns on top of the existing flag columns from Weeks 4-5.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

INPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"
RAW_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-raw"
OUTPUT_DIR = "/Users/alanadams/Downloads/IDX_Internship/CSV-output"

SOLD_IN = f"{INPUT_DIR}/cleaned_sold.csv"
LISTINGS_IN = f"{INPUT_DIR}/cleaned_listings.csv"
SOLD_OUT = f"{OUTPUT_DIR}/featured_sold.csv"
LISTINGS_OUT = f"{OUTPUT_DIR}/featured_listings.csv"

# Path to the school district boundary file. Aidan's 7/17 message points to the
# 2025-26 vintage (the handbook itself links the older 2024-25 file, but we're
# following the most recent guidance from the channel).
# Download the GeoJSON manually from:
# https://data.ca.gov/dataset/california-school-district-areas-2025-26
# and save it here:
SCHOOL_DISTRICT_GEOJSON = f"{RAW_DIR}/california_school_districts_2025_26.geojson"


def print_header(step_name):
    print("\n" + "=" * 70)
    print(step_name)
    print("=" * 70)


# ============================================================
# STEP 0 - LOAD CLEANED DATASETS
# ============================================================
print_header("STEP 0: LOADING CLEANED DATASETS")

sold = pd.read_csv(SOLD_IN, low_memory=False)
listings = pd.read_csv(LISTINGS_IN, low_memory=False)

print(f"Loaded cleaned_sold.csv       -> {len(sold):,} rows, {sold.shape[1]} columns")
print(f"Loaded cleaned_listings.csv   -> {len(listings):,} rows, {listings.shape[1]} columns")

# Re-parse date columns as datetime. Weeks 4-5 already converted these, but
# CSV round-trips always write dates back out as plain strings, so every
# script that reads a CSV needs to re-parse dates itself.
for col in ["CloseDate", "PurchaseContractDate", "ListingContractDate"]:
    if col in sold.columns:
        sold[col] = pd.to_datetime(sold[col], errors="coerce")
    if col in listings.columns:
        listings[col] = pd.to_datetime(listings[col], errors="coerce")


# ============================================================
# STEP 1 - MARKET METRICS (SOLD DATASET ONLY)
# ============================================================
print_header("STEP 1: ENGINEERING MARKET METRICS (SOLD DATASET)")

# Why sold-only: every metric below needs ClosePrice, CloseDate, and/or
# PurchaseContractDate. Active listings never populate these fields (see the
# primer, Section 2, Stage 4) so these metrics are structurally undefined for
# the listings dataset. Running them there would just produce all-null columns.

before_rows = len(sold)

# --- Price Ratio / Close-to-Original-List Ratio ---
# The handbook lists these as two separate metrics with the identical formula
# (ClosePrice / OriginalListPrice). Rather than create two identical columns,
# we compute it once as `close_to_orig_list_ratio` and treat "price ratio" as
# the same number used two ways: (a) per-transaction negotiation strength,
# and (b) aggregated by ZIP/time period as a market-momentum proxy (see
# primer Section 3). Guard against OriginalListPrice <= 0 to avoid inf/NaN
# blowups instead of just dividing blindly.
sold["close_to_orig_list_ratio"] = np.where(
    sold["OriginalListPrice"] > 0,
    sold["ClosePrice"] / sold["OriginalListPrice"],
    np.nan
)

# --- Price Per Sq Ft (PPSF) ---
# Guard LivingArea <= 0 the same way. This should already be flagged from
# Weeks 4-5 cleaning, but we don't rely on that flag having removed rows
# (nothing gets deleted in this pipeline) -- we just guard here directly.
sold["price_per_sqft"] = np.where(
    sold["LivingArea"] > 0,
    sold["ClosePrice"] / sold["LivingArea"],
    np.nan
)

# --- Days on Market ---
# Handbook says to use the raw DaysOnMarket field as-is. We don't recompute
# it, since the MLS-provided figure already accounts for platform-specific
# DOM rules that vary by status history (see primer Section 8 on DOM vs
# CDOM) -- recalculating it ourselves risks silently disagreeing with the
# MLS's own methodology.
if "DaysOnMarket" not in sold.columns:
    print("WARNING: 'DaysOnMarket' column not found in cleaned_sold.csv - check column name.")

# --- Year / Month / YrMo (derived from CloseDate) ---
sold["close_year"] = sold["CloseDate"].dt.year
sold["close_month"] = sold["CloseDate"].dt.month
sold["close_yrmo"] = sold["CloseDate"].dt.to_period("M").astype(str)

# --- Listing-to-Contract Days ---
# Time from listing to accepted offer. Negative values here would mean a
# purchase contract was signed before the listing date -- already flagged
# as purchase_after_close_flag / negative_timeline_flag territory in Weeks
# 4-5, so we don't re-flag, just compute the raw day count.
sold["listing_to_contract_days"] = (
    sold["PurchaseContractDate"] - sold["ListingContractDate"]
).dt.days

# --- Contract-to-Close Days ---
# Escrow/closing period duration.
sold["contract_to_close_days"] = (
    sold["CloseDate"] - sold["PurchaseContractDate"]
).dt.days

after_rows = len(sold)
print(f"Row count before feature engineering: {before_rows:,}")
print(f"Row count after feature engineering:  {after_rows:,}  (unchanged, confirms no rows dropped)")

print("\nSample of engineered columns:")
sample_cols = [
    "ClosePrice", "OriginalListPrice", "close_to_orig_list_ratio",
    "price_per_sqft", "close_yrmo",
    "listing_to_contract_days", "contract_to_close_days"
]
sample_cols = [c for c in sample_cols if c in sold.columns]
print(sold[sample_cols].head(10))

print("\nEngineered metric summary stats (sold dataset):")
print(sold[[c for c in [
    "close_to_orig_list_ratio", "price_per_sqft",
    "listing_to_contract_days", "contract_to_close_days"
] if c in sold.columns]].describe())


# ============================================================
# STEP 2 - SCHOOL DISTRICT MAPPING (BOTH DATASETS)
# ============================================================
print_header("STEP 2: SCHOOL DISTRICT MAPPING (GEOPANDAS SPATIAL JOIN)")

# Per Aidan's 7/17 message in #data-analyst-summer-2026:
# 1. Download the CA School District boundary GeoJSON (2025-26 vintage)
# 2. pip install geopandas
# 3. Read it into a GeoDataFrame
# 4. Filter to DistrictType == "Unified" only
# 5. Convert each property's Lat/Long into a geographic point
# 6. Spatial join (gpd.sjoin) to find which polygon contains each property
# 7. Add the result as a DistrictName column
# 8. Save and use going forward

def add_school_district(df, dataset_label):
    """Adds a DistrictName column to df using a spatial join against the
    CA Unified School District boundaries. Applied to both sold and listings
    since it only needs Latitude/Longitude, which both datasets have."""

    print(f"\n--- Mapping school districts for {dataset_label} ---")

    geo_before = len(df)

    # Load district boundaries
    districts = gpd.read_file(SCHOOL_DISTRICT_GEOJSON)

    # Step 4: keep only Unified districts, per Aidan's instruction
    unified_count_before = len(districts)
    districts = districts[districts["DistrictType"] == "Unified"].copy()
    print(f"School district polygons: {unified_count_before:,} total -> "
          f"{len(districts):,} after filtering to DistrictType == 'Unified'")

    # Step 5: convert each property's Lat/Long into a geographic point
    # Drop rows with missing/invalid coordinates for the join itself (they
    # were already flagged, not removed, back in Weeks 4-5). We keep the
    # full dataframe and just leave DistrictName null for these rows.
    has_coords = df["Latitude"].notna() & df["Longitude"].notna()
    geometry = [
        Point(xy) if valid else None
        for xy, valid in zip(zip(df["Longitude"], df["Latitude"]), has_coords)
    ]
    gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")

    # Match CRS between the two layers before joining
    if districts.crs is not None and districts.crs != gdf.crs:
        districts = districts.to_crs(gdf.crs)

    # Step 6: spatial join
    joined = gpd.sjoin(gdf, districts[["DistrictName", "geometry"]],
                        how="left", predicate="within")

    # A property can occasionally land on a shared boundary and match more
    # than one polygon. Keep the first match per row and drop sjoin's index
    # bookkeeping column so we return a clean, same-row-count dataframe.
    joined = joined[~joined.index.duplicated(keep="first")]
    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")

    matched = joined["DistrictName"].notna().sum()
    print(f"Rows with coordinates:        {has_coords.sum():,} / {geo_before:,}")
    print(f"Rows matched to a district:   {matched:,} / {geo_before:,}")

    return pd.DataFrame(joined)


try:
    sold = add_school_district(sold, "sold dataset")
    listings = add_school_district(listings, "listings dataset")
except FileNotFoundError:
    print(f"\nSCHOOL DISTRICT FILE NOT FOUND at {SCHOOL_DISTRICT_GEOJSON}")
    print("Download it from https://data.ca.gov/dataset/california-school-district-areas-2025-26")
    print("and save it to that exact path, then re-run this script.")
    print("Continuing without DistrictName for now so the rest of the script still runs.")


# ============================================================
# STEP 3 - SEGMENT ANALYSIS (SOLD DATASET)
# ============================================================
print_header("STEP 3: SEGMENT ANALYSIS")

# Segment by PropertyType / PropertySubType
if "PropertySubType" in sold.columns:
    print("\n-- Segment: PropertyType / PropertySubType --")
    seg_type = sold.groupby(["PropertyType", "PropertySubType"]).agg(
        n_sales=("ClosePrice", "count"),
        median_close_price=("ClosePrice", "median"),
        median_ppsf=("price_per_sqft", "median"),
        median_close_to_list_ratio=("close_to_orig_list_ratio", "median"),
    ).reset_index()
    print(seg_type)

# Segment by County
if "CountyOrParish" in sold.columns:
    print("\n-- Segment: CountyOrParish --")
    seg_county = sold.groupby("CountyOrParish").agg(
        n_sales=("ClosePrice", "count"),
        median_close_price=("ClosePrice", "median"),
        median_ppsf=("price_per_sqft", "median"),
        median_dom=("DaysOnMarket", "median") if "DaysOnMarket" in sold.columns else ("ClosePrice", "count"),
    ).reset_index().sort_values("median_close_price", ascending=False)
    print(seg_county.head(15))

# Segment by listing office (competitive intelligence, feeds Week 8-10 dashboards)
if "ListOfficeName" in sold.columns:
    print("\n-- Segment: Top 10 Listing Offices by Volume --")
    seg_office = sold.groupby("ListOfficeName").agg(
        n_sales=("ClosePrice", "count"),
        total_volume=("ClosePrice", "sum"),
        median_close_to_list_ratio=("close_to_orig_list_ratio", "median"),
    ).reset_index().sort_values("total_volume", ascending=False)
    print(seg_office.head(10))


# ============================================================
# STEP 4 - SAVE OUTPUTS
# ============================================================
print_header("STEP 4: SAVING FEATURED DATASETS")

sold.to_csv(SOLD_OUT, index=False)
listings.to_csv(LISTINGS_OUT, index=False)

print(f"Saved: {SOLD_OUT}  ({len(sold):,} rows, {sold.shape[1]} columns)")
print(f"Saved: {LISTINGS_OUT}  ({len(listings):,} rows, {listings.shape[1]} columns)")
print("\nWeek 6 feature engineering complete.")