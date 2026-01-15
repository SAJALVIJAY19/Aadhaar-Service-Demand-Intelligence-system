import pandas as pd
import numpy as np
import warnings
from sklearn.preprocessing import MinMaxScaler
warnings.filterwarnings('ignore')

print("Starting Pipeline...")

# --- 02 ---
print("Running 02...")
try:
    df_enroll = pd.read_csv('district_monthly_enrollment.csv')
    df_bio = pd.read_csv('district_monthly_biometric.csv')
    df_demo = pd.read_csv('district_monthly_demographic.csv')

    def agg(df, name):
        return df.groupby(['state', 'district'])['total'].sum().reset_index().rename(columns={'total': f'{name}_vol'})

    a_en = agg(df_enroll, 'enrollment')
    a_bi = agg(df_bio, 'biometric')
    a_de = agg(df_demo, 'demographic')
    master = a_en.merge(a_bi, on=['state','district']).merge(a_de, on=['state','district'])
    master['total_volume'] = master['enrollment_vol'] + master['biometric_vol'] + master['demographic_vol']

    master['enrollment_ratio'] = master['enrollment_vol'] / master['total_volume']
    master['biometric_ratio'] = master['biometric_vol'] / master['total_volume']
    master['demographic_ratio'] = master['demographic_vol'] / master['total_volume']
    master['dominance_score'] = master[['enrollment_ratio', 'biometric_ratio', 'demographic_ratio']].max(axis=1)

    def classify(row):
        s = row['dominance_score']
        if row['enrollment_ratio'] == s: t = 'Enrollment'
        elif row['biometric_ratio'] == s: t = 'Biometric'
        else: t = 'Demographic'
        if s >= 0.6: st = 'Strong Dominant'
        elif s >= 0.4: st = 'Mixed Demand'
        else: st = 'Balanced Demand'
        return pd.Series([t, st])

    master[['dominant_type', 'dominance_strength']] = master.apply(classify, axis=1)

    def op_meaning(row):
        if row['dominance_strength'] == 'Strong Dominant':
            if row['dominant_type'] == 'Enrollment': return 'New Population Entry'
            if row['dominant_type'] == 'Biometric': return 'Maintenance Burden'
        return 'General Service Load'
    master['operational_meaning'] = master.apply(op_meaning, axis=1)

    final_02 = master[['state', 'district', 'enrollment_ratio', 'biometric_ratio', 'demographic_ratio', 'dominant_type', 'dominance_score', 'dominance_strength', 'operational_meaning']].copy()
    final_02.round(3).to_csv('02_output.csv', index=False)
    print("Saved 02_output.csv")
except Exception as e:
    print(f"Error in 02: {e}")

# --- 03 ---
print("Running 03...")
try:
    df_all = pd.concat([df_enroll, df_bio, df_demo])
    district_monthly = df_all.groupby(['state', 'district', 'month'])['total'].sum().reset_index()

    metrics = district_monthly.groupby(['state', 'district'])['total'].agg(total_volume='sum', volatility='std').reset_index()

    def get_growth(x):
        if len(x) < 2: return 0
        return x['total'].pct_change().mean()

    growth = district_monthly.groupby(['state', 'district']).apply(get_growth).reset_index(name='monthly_growth_rate')
    metrics = metrics.merge(growth, on=['state', 'district'])
    metrics['monthly_growth_rate'] = metrics['monthly_growth_rate'].fillna(0)

    scaler = MinMaxScaler()
    cols = ['total_volume', 'monthly_growth_rate', 'volatility']
    norm_cols = [f'norm_{c}' for c in cols]
    metrics[norm_cols] = scaler.fit_transform(metrics[cols].fillna(0))

    metrics['pressure_index'] = 0.5 * metrics['norm_total_volume'] + 0.3 * metrics['norm_monthly_growth_rate'] + 0.2 * metrics['norm_volatility']

    def classify_pressure(x):
        if x >= 0.75: return 'Critical Infrastructure Stress'
        if x >= 0.55: return 'High Stress'
        if x >= 0.35: return 'Moderate Stress'
        return 'Stable'

    metrics['pressure_tier'] = metrics['pressure_index'].apply(classify_pressure)
    out_03 = metrics[['state', 'district', 'pressure_index', 'pressure_tier', 'total_volume', 'monthly_growth_rate', 'volatility']]
    out_03.round(3).to_csv('03_output.csv', index=False)
    print("Saved 03_output.csv")
except Exception as e:
    print(f"Error in 03: {e}")

# --- 04 ---
print("Running 04...")
try:
    age_sum = df_all.groupby(['state', 'district'])[['age_0_5', 'age_5_17', 'age_18_plus', 'total']].sum().reset_index()
    combined = age_sum.merge(metrics[['state', 'district', 'pressure_tier']], on=['state', 'district'])
    combined = combined.merge(metrics[['state', 'district', 'volatility']], on=['state', 'district']) 
    combined = combined.merge(master[['state', 'district', 'dominant_type']], on=['state', 'district'])

    combined['child_pressure'] = combined['age_0_5'] + combined['age_5_17']
    combined['adult_pressure'] = combined['age_18_plus']
    combined['child_ratio'] = combined['child_pressure'] / combined['total']
    combined['adult_ratio'] = combined['adult_pressure'] / combined['total']

    def get_typology(row):
        tier = row['pressure_tier']
        c_ratio = row['child_ratio']
        a_ratio = row['adult_ratio']
        is_high_crit = tier in ['High Stress', 'Critical Infrastructure Stress']
        
        if c_ratio > 0.6 and is_high_crit:
            return 'School-linked Surge Zone'
        if a_ratio > 0.7 and is_high_crit:
            return 'Correctional Overload Zone'
        if row['dominant_type'] == 'Biometric' and row['volatility'] > 100: 
            return 'Migration Impact Zone'
        return 'Population Expansion Zone'

    combined['typology'] = combined.apply(get_typology, axis=1)
    out_04 = combined[['state', 'district', 'typology', 'child_ratio', 'adult_ratio', 'pressure_tier']]
    out_04.round(3).to_csv('04_output.csv', index=False)
    print("Saved 04_output.csv")
except Exception as e:
    print(f"Error in 04: {e}")

# --- 05 ---
print("Running 05...")
try:
    results = []
    for (state, dist), group in district_monthly.groupby(['state', 'district']):
        mean = group['total'].mean()
        std = group['total'].std()
        if std == 0: continue
        spikes = group[group['total'] > mean + 2*std]
        
        spike_months = spikes['month'].tolist()
        spike_type = 'Irregular/Migration'
        if len(spike_months) > 1:
            spike_type = 'Seasonal Pattern'
        
        if len(spike_months) > 0:
            results.append({
                'state': state,
                'district': dist,
                'spike_months': str(spike_months),
                'spike_type': spike_type,
                'volatility': std
            })
    out_05 = pd.DataFrame(results)
    if not out_05.empty:
        out_05.round(3).to_csv('05_output.csv', index=False)
        print("Saved 05_output.csv")
    else:
        print("No spikes detected.")
except Exception as e:
    print(f"Error in 05: {e}")

# --- 06 ---
print("Running 06...")
try:
    merged = out_04.merge(metrics[['state', 'district', 'volatility']], on=['state', 'district']) 
    merged = merged.merge(master[['state', 'district', 'dominance_strength', 'dominant_type']], on=['state', 'district'])

    def recommend(row):
        tier = row['pressure_tier']
        typo = row['typology']
        dtype = row['dominant_type']
        
        action = "Deploy mobile enrollment vans"
        rationale = "High adult correction load + volatility indicates migrant churn."
        
        if typo == 'School-linked Surge Zone':
            action = "Launch school-based biometric drives"
            rationale = "High child ratio indicates school admission season pressure."
        elif typo == 'Correctional Overload Zone':
            action = "Set up temporary camps"
            rationale = "Adult dominance suggests high demand for updates."
        elif tier == 'Critical Infrastructure Stress':
            action = "Set up temporary camps"
            rationale = "Critical stress levels require immediate capacity expansion."
        elif row['dominance_strength'] == 'Strong Dominant':
            if dtype == 'Biometric':
                 action = "Increase biometric operators"
                 rationale = "Biometric heavy load requires specialized operators."
            
        return pd.Series([action, rationale])

    merged[['recommended_action', 'rationale']] = merged.apply(recommend, axis=1)
    
    # FIX: Select 'typology' then rename
    out_06 = merged[['state', 'district', 'typology', 'pressure_tier', 'recommended_action', 'rationale']]
    out_06.rename(columns={'typology': 'classification'}, inplace=True)
    out_06.to_csv('06_output.csv', index=False)
    print("Saved 06_output.csv")
except Exception as e:
    print(f"Error in 06: {e}")
