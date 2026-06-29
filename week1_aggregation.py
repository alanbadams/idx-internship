import pandas as pd
import glob
import os

# ============================================================
# WEEK 1 – Monthly Dataset Aggregation
# IDX Exchange Internship – Alan Adams
# ============================================================

# Folder where your CSV files live
csv_folder = '/Users/alanadams/Downloads/IDX_Internship/CSV-raw'

# ============================================================
# PART 1 — SOLD FILES
# ============================================================

# Find all Sold CSV files, exclude _filled versions
sold_files = sorted(glob.glob(os.path.join(csv_folder, 'CRMLSSold*.csv')))
sold_files = [f for f in sold_files if '_filled' not in f]

print("=== SOLD FILES FOUND ===")
for f in sold_files:
    print(" ", os.path.basename(f))

# Read each file and combine them all into one
sold_list = []
for f in sold_files:
    df = pd.read_csv(f, low_memory=False)
    sold_list.append(df)

sold = pd.concat(sold_list, ignore_index=True)

# Row count BEFORE filter
print(f"\nSold rows BEFORE Residential filter: {len(sold)}")

# Keep only rows where PropertyType is Residential
sold_residential = sold[sold['PropertyType'] == 'Residential'].copy()

# Row count AFTER filter
print(f"Sold rows AFTER Residential filter:  {len(sold_residential)}")

# Save the result
sold_residential.to_csv(
    os.path.join(csv_folder, 'combined_sold_residential.csv'), index=False
)
print("Saved: combined_sold_residential.csv")

# ============================================================
# PART 2 — LISTING FILES
# ============================================================

# Find all Listing CSV files, exclude _filled versions
listing_files = sorted(glob.glob(os.path.join(csv_folder, 'CRMLSListing*.csv')))
listing_files = [f for f in listing_files if '_filled' not in f]

print("\n=== LISTING FILES FOUND ===")
for f in listing_files:
    print(" ", os.path.basename(f))

# Read each file and combine them all into one
listing_list = []
for f in listing_files:
    df = pd.read_csv(f, low_memory=False)
    listing_list.append(df)

listings = pd.concat(listing_list, ignore_index=True)

# Row count BEFORE filter
print(f"\nListings rows BEFORE Residential filter: {len(listings)}")

# Keep only rows where PropertyType is Residential
listings_residential = listings[listings['PropertyType'] == 'Residential'].copy()

# Row count AFTER filter
print(f"Listings rows AFTER Residential filter:  {len(listings_residential)}")

# Save the result
listings_residential.to_csv(
    os.path.join(csv_folder, 'combined_listings_residential.csv'), index=False
)
print("Saved: combined_listings_residential.csv")

# ============================================================
print("\n✅ WEEK 1 DONE.")