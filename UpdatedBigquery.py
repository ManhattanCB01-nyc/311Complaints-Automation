try:
    from google.colab import drive
    COLAB_ENV = True
    print("Running in Google Colab environment.")
    drive.mount('/content/drive')
except ImportError:
    COLAB_ENV = False
    print("Not running in Google Colab environment.")

# --- Core Imports ---
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from datetime import datetime, timedelta
import time
import io
import ssl

# --- Google API Imports ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Constants for Data Cleaning & Processing ---
COMPLAINT_TYPES_TO_EXCLUDE = [ 'Adopt-A-Basket', 'Advocate - Other', 'Advocate-Co-opCondo Abatement', 'Advocate-Prop Refunds/Credits', 'Animal Facility - No Permit', 'Appliance', 'Beach/Pool/Sauna Complaint', 'Bench', 'Bike Rack', 'Bike Rack Condition', 'Borough Office', 'Building Condition', 'Building Marshals office', 'Bus Stop Shelter Placement', 'Calorie Labeling', 'Collection Truck Noise', 'Construction Safety Enforcement', 'Cooling Tower', 'COVID-19 Non-essential Construction', 'Dept of Investigations', 'Derelict Bicycle', 'Dirty Condition', 'Disorderly Youth', 'Dispatched Taxi Complaint', 'DOF Parking - Tax Exemption', 'DOF Property - Owner Issue', 'DOF Property - Payment Issue', 'DOF Property - Property Value', 'DOF Property - Reduction Issue', 'DOF Property - Request Copy', 'DOF Property - RPIE Issue', 'DOF Property - Update Account', 'DPR Internal', 'DRIE', 'DSNY Internal', 'Dumpster Complaint', 'Executive Inspections', 'Facades', 'Face Covering Violation', 'Ferry Complaint', 'Ferry Inquiry', 'For Hire Vehicle Report', 'Found Property', 'General', 'Green Taxi Complaint', 'Green Taxi Report', 'Harboring Bees/Wasps', 'Heat/Hot Water', 'Highway Condition', 'Highway Sign - Dangling', 'Home Delivered Meal - Missed Delivery', 'Homeless Encampment', 'Homeless Street Condition', 'Housing - Low Income Senior', 'Housing Options', 'Illegal Animal Kept as Pet', 'Illegal Animal Sold', 'Incorrect Data', 'Institution Disposal Complaint', 'Internal Code', 'Lifeguard', 'Literature Request', 'Mass Gathering Complaint', 'Miscellaneous Categories', 'Municipal Parking Facility', 'Noise - House of Worship', 'NonCompliance with Phased Reopening', 'Oil or Gas Spill', 'Other Enforcement', 'OUTSITE BUILDING', 'Overflowing Litter Baskets', 'Paint/Plaster', 'Plant', 'Posting Advertisement', 'Private or Charter School Reopening', 'Private School Vaccine Mandate Non-Compliance', 'Public Payphone Complaint', 'Public Toilet', 'Quality of Life', 'Radioactive Material', 'Recycling Basket Complaint', 'Recycling Enforcement', 'Retailer Complaint', 'SCRIE', 'Seasonal Collection', 'Senior Center Complaint', 'Sewer Maintenance', 'Single Occupancy Bathroom', 'Snow', 'Snow Removal', 'Special Operations', 'Squeegee', 'Storm', 'Sustainability Enforcement', 'Sweeping/Inadequate', 'Sweeping/Missed', 'Tanning', 'Tattooing', 'Taxi Licensee Complaint', 'Taxpayer Advocate Inquiry', 'Unsanitary Animal Facility', 'Unsanitary Animal Pvt Property', 'Uprooted Stump', 'Vacant Lot', 'Vaccine Mandate Non-Compliance', 'Water Leak', 'Water Maintenance', 'Window Guard', 'Wood Pile Remaining', 'X-Ray Machine/Equipment' ]
COMPLAINT_TYPE_MERGE_MAP = { 'Animal-Abuse': 'Animal Abuse', 'Derelict Vehicle': 'Derelict Vehicles', 'Electrical': 'ELECTRIC', 'ELEVATOR': 'Elevator', 'Litter Basket / Request': 'Litter Basket Request', 'PLUMBING': 'Plumbing', 'Smoking': 'Smoking or Vaping' }
CONSUMER_COMPLAINT_DESCRIPTORS_TO_DELETE = [ 'Retail Store', 'Sidewalk Cafe', 'Other', 'False Advertising', 'Exchange/Refund/Return', 'Locksmith', 'Car Wash', 'Department Store or Megastore', 'Barber Shop, Beauty Salon, or Nail Salon', 'Damaged Vehicle', 'Non-Delivery Goods/Services', 'Unlicensed', 'Car Not Available', 'Non-Delivery of Papers', 'Furniture Store', 'Receipt Incomplete/Not Given', 'Home Heating Oil Company', 'Auction House or Auctioneer', 'Scale Dealer/Repairer', 'Smoking, Cigar or Vape Store', 'Moving Company', 'Secondhand Dealer', 'Bail Bond Agent', 'Catering Establishment', 'Home Appliance Store', 'Publishing Company', 'House/Property Damaged', 'Contract Dispute', 'Laundry', 'Wholesale Food Market', 'Jewelry Appraiser', 'Disabled Device Dealer', 'Horse Drawn Carriage', 'Going Out of Business', 'Door Open with Air Conditioning On', 'Laundromat', 'Gaming Cafe', 'Funeral Home', 'Gas Station', 'Bingo Hall', 'Dealer in Products for the Disabled', 'Hardware Store', 'Pet Store', 'High Pressure to Take on Loan/Debt', 'Debt Not Owed', 'Landlord or Real Estate Agent', 'Jewelry Store', 'Billing Dispute', 'Documents/Paperwork Missing', 'Illegal/Unfair Booting', 'Over Capacity', 'Price Not Posted', 'Rates Not Posted', 'Lost Property', 'Mandatory Tip', 'Paid in Advance', 'Scale Inaccurate/Broken', 'Used Goods Dealer', 'Shipping Company', 'Vocational or Trade School', 'Harassment', 'Damaged/Defective Goods', 'Overcharge' ]
CONSUMER_COMPLAINT_DESCRIPTOR_MAP = { 'Bodega/Deli/Supermarket': 'Bodega, Deli, or Convenience Store', 'Garage/Parking Lot': 'Garage or Parking Lot', 'Ticket Broker': 'Ticket Seller', 'Car Dealer - Used': 'Used Car Dealer', 'Hotel': 'Hotel or Motel', 'Immigration Services': 'Immigration Services Provider', 'Mail Order': 'Online or Mail Order', 'Stoop Line': 'Stoop Line Stand', 'Tour Company': 'Tour Guide', 'Tax Preparer': 'Tax Preparation Services', 'For-profit College': 'For-Profit College or University' }
VENDOR_DESCRIPTORS_TO_RECATEGORIZE = ['Vendor', 'General Vendor', 'Street Fair Vendor']
COLUMNS_TO_DELETE = [ 'address_type', 'city', 'facility_type', 'due_date', 'resolution_action_updated_date', 'bbl', 'borough', 'x_coordinate_state_plane', 'y_coordinate_state_plane', 'park_facility_name', 'park_borough', 'vehicle_type', 'taxi_company_borough', 'taxi_pick_up_location', 'bridge_highway_name', 'bridge_highway_direction', 'road_ramp', 'bridge_highway_segment', 'location' ]

# --- Configuration Constants ---
NYC_OPEN_DATA_RESOURCE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
API_LIMIT_PER_REQUEST = 1000
ZIP_CODES_TO_INCLUDE = [10004, 10005, 10006, 10007, 10038, 10280, 10282, 10013, 10002]
DEFAULT_INITIAL_FETCH_DATE = "2018-07-01"

# <<< BIGQUERY CONFIGURATION FOR EXPORT TABLE >>>
GOOGLE_CLOUD_PROJECT_ID = "stable-liberty-426016-d2"
BIGQUERY_EXPORT_TABLE_ID = "nyc_311_data.complaints_export"

# Dynamic path for the service account key
if COLAB_ENV:
    SERVICE_ACCOUNT_KEY_FILE = "/content/drive/Shareddrives/311_Complaint_Data/service_account_key.json"
else:
    SERVICE_ACCOUNT_KEY_FILE = "service_account_key.json"

# --- Helper Functions ---
def process_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df[~((df['complaint_type'] == 'Consumer Complaint') & (df['descriptor'].isin(CONSUMER_COMPLAINT_DESCRIPTORS_TO_DELETE)))]
    df['complaint_type'] = df['complaint_type'].replace(COMPLAINT_TYPE_MERGE_MAP)
    consumer_mask = df['complaint_type'] == 'Consumer Complaint'
    df.loc[consumer_mask, 'descriptor'] = df.loc[consumer_mask, 'descriptor'].replace(CONSUMER_COMPLAINT_DESCRIPTOR_MAP)
    vendor_mask = (df['complaint_type'] == 'Consumer Complaint') & (df['descriptor'].isin(VENDOR_DESCRIPTORS_TO_RECATEGORIZE))
    df.loc[vendor_mask, 'complaint_type'] = 'Vendor Enforcement'
    df.drop(columns=COLUMNS_TO_DELETE, inplace=True, errors='ignore')
    date_cols = ['created_date', 'closed_date', 'resolution_action_updated_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            df[col] = df[col].dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def fetch_nyc_data_incremental(start_date_str: str, end_date_str: str = None) -> pd.DataFrame:
    all_fetched_dfs = []
    offset = 0
    more_data_available = True
    if end_date_str: date_filter = f"created_date >= '{start_date_str}T00:00:00.000' AND created_date <= '{end_date_str}T23:59:59.999'"
    else: date_filter = f"created_date >= '{start_date_str}T00:00:00.000'"
    community_board_filter = "contains(community_board, '01 MANHATTAN')"
    where_clause = f"{date_filter} AND {community_board_filter}"
    session = requests.Session()
    retries = Retry(total=10, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    while more_data_available:
        params = {'$limit': API_LIMIT_PER_REQUEST, '$offset': offset, '$where': where_clause, '$order': 'created_date ASC'}
        try:
            response = session.get(NYC_OPEN_DATA_RESOURCE_URL, params=params, timeout=90)
            response.raise_for_status()
            if not response.text.strip(): more_data_available = False; continue
            page_df = pd.read_csv(io.StringIO(response.text))
            if not page_df.empty:
                all_fetched_dfs.append(page_df)
                offset += len(page_df)
                if len(page_df) < API_LIMIT_PER_REQUEST: more_data_available = False
            else: more_data_available = False
            time.sleep(1)
        except (requests.exceptions.RequestException, pd.errors.EmptyDataError) as e:
            break
    if not all_fetched_dfs: return pd.DataFrame()
    return pd.concat(all_fetched_dfs, ignore_index=True)

# <<< MODIFIED MAIN FUNCTION: CREATE NEW TABLE >>>
def create_bigquery_export_table():
    """Fetches ALL data and creates a NEW table (replacing if exists)."""
    print("--- Starting BigQuery Export Table Creation ---")

    # Authenticate
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]
        )
        print("Authentication successful.")
    except Exception as e:
        print(f"FATAL: Authentication failed: {e}"); return

    # Starts from the default start date to get a full download
    start_date = datetime.strptime(DEFAULT_INITIAL_FETCH_DATE, '%Y-%m-%d')
    end_date = datetime.now()

    print(f"Fetching complete dataset from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

    # Fetch data in yearly chunks
    all_chunks_dfs = []
    for year in range(start_date.year, end_date.year + 1):
        chunk_start_date = max(start_date, datetime(year, 1, 1))
        chunk_end_date = min(end_date, datetime(year, 12, 31))
        if chunk_start_date > chunk_end_date: continue

        print(f"Fetching data for year: {year}...")
        chunk_df = fetch_nyc_data_incremental(
            chunk_start_date.strftime('%Y-%m-%d'), chunk_end_date.strftime('%Y-%m-%d'))
        if not chunk_df.empty: all_chunks_dfs.append(chunk_df)

    if not all_chunks_dfs:
        print("\nNo data found to upload. Process finished."); return

    new_data_df = pd.concat(all_chunks_dfs, ignore_index=True)

    # Filter and clean
    new_data_df['incident_zip'] = pd.to_numeric(new_data_df['incident_zip'], errors='coerce')
    filtered_df = new_data_df[new_data_df['incident_zip'].isin(ZIP_CODES_TO_INCLUDE)].copy()
    filtered_df = filtered_df[~filtered_df['complaint_type'].isin(COMPLAINT_TYPES_TO_EXCLUDE)]

    if filtered_df.empty:
        print("No data remains after filtering. Process finished."); return

    processed_df = process_and_clean_data(filtered_df)

    # De-duplicate
    if 'unique_key' in processed_df.columns:
        processed_df.drop_duplicates(subset=['unique_key'], inplace=True, keep='last')

    # Upload to BigQuery as a NEW table
    print(f"\nUploading {len(processed_df)} rows to NEW table: {BIGQUERY_EXPORT_TABLE_ID}...")
    try:
        processed_df.to_gbq(
            destination_table=BIGQUERY_EXPORT_TABLE_ID,
            project_id=GOOGLE_CLOUD_PROJECT_ID,
            if_exists='replace', # Creates a new table or overwrites it completely
            credentials=creds
        )
        print(f"Successfully created downloadable table: {BIGQUERY_EXPORT_TABLE_ID}")
    except Exception as e:
        print(f"FATAL: Failed to upload data to BigQuery: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    create_bigquery_export_table()
