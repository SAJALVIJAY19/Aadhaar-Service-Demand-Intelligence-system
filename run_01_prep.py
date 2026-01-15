import pandas as pd
import os

# CONFIGURATION: Deterministic File Mappings
# Mapping structure: State -> { Category -> Filename }
FILE_MAP = {
    "Delhi": {
        "Enrollment": "Enrollemnt_Delhi.csv",  # Typo in filename
        "Demographic": "Demographic_Delhi.csv",
        "Biometric": "Biometric_Delhi.csv"
    },
    "Maharashtra": {
        "Enrollment": "Enrollment_Maharashtra.csv",
        "Demographic": "Demographic_Maharashtra.csv",
        "Biometric": "Biometric_Maharashtra.csv"
    },
    "Rajasthan": {
        "Enrollment": "Enrollement_Rajasthan.csv", # Typo in filename
        "Demographic": "Demographic_Rajasthan.csv",
        "Biometric": "Biometric_Rajasthan.csv"
    },
    "UP": {
        "Enrollment": "Enrollement_UP.csv", # Typo in filename
        "Demographic": "Demographic_UP.csv",
        "Biometric": "Biometric_UP.csv"
    }
}

# Column Normalization Map  
COL_RENAME_MAP = {
    "age_18_greater": "age_18_plus",
    "age_18+": "age_18_plus",

    "demo_age_5_17": "age_5_17",
    "demo_age_17_": "age_18_plus",

    "bio_age_5_17": "age_5_17",
    "bio_age_17_": "age_18_plus"
}

def process_category(category_name, output_filename):
    print(f"Processing Category: {category_name}...")
    all_data = []
    
    for state, files in FILE_MAP.items():
        filename = files.get(category_name)
        if not filename:
            print(f"  WARNING: No file config for {state} - {category_name}")
            continue
            
        path = os.path.join(state, filename)
        if not os.path.exists(path):
            print(f"  ERROR: File not found: {path}")
            continue
            
        print(f"  Loading {state}: {path}")
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  ERROR reading {path}: {e}")
            continue
        
        # 1. Clean Column Names
        df.columns = [c.strip().lower() for c in df.columns]
        
        # 2. Rename specific columns
        df.rename(columns=COL_RENAME_MAP, inplace=True)
        
        # MANDATORY FIX 2: Base Column Validation
        required_base_cols = ['date', 'district']
        missing_base = False
        for col in required_base_cols:
            if col not in df.columns:
                print(f"ERROR: Missing required column '{col}' in {path}")
                missing_base = True
        if missing_base:
            continue

        # 3. Date Parsing
        try:
            # UIDAI data date format is usually DD-MM-YYYY based on inspection
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            # Drop invalid dates if any
            df = df.dropna(subset=['date'])
            df['month'] = df['date'].dt.strftime('%Y-%m')
        except Exception as e:
            print(f"    Date parse error in {path}: {e}")
            continue
            
        # 4. Standardize State Name (Ensure it matches the key)
        df['state'] = state
        
        # MANDATORY FIX 1: District Name Normalization
        df['district'] = df['district'].astype(str).str.strip().str.title()
        
        # 5. Handle missing columns if any (fill with 0 for summation)
        required_metrics = ['age_0_5', 'age_5_17', 'age_18_plus']
        for col in required_metrics:
            if col not in df.columns:
                df[col] = 0
        
        # MANDATORY FIX 3: Numeric Safety Before Aggregation
        for col in required_metrics:
             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 6. Group By
        # Group by State, District, Month
        grouped = df.groupby(['state', 'district', 'month'], as_index=False)[required_metrics].sum()
        
        # 7. Calculate Total
        grouped['total'] = grouped['age_0_5'] + grouped['age_5_17'] + grouped['age_18_plus']
        
        all_data.append(grouped)
        
    # Combine all states
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Reorder columns
        cols = ['state', 'district', 'month', 'age_0_5', 'age_5_17', 'age_18_plus', 'total']
        final_df = final_df[cols]
        
        final_df.to_csv(output_filename, index=False)
        print(f"  Saved {output_filename} with {len(final_df)} rows.")
    else:
        print(f"  No data found for {category_name}")

if __name__ == "__main__":
    process_category("Enrollment", "district_monthly_enrollment.csv")
    process_category("Demographic", "district_monthly_demographic.csv")
    process_category("Biometric", "district_monthly_biometric.csv")
