import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import os

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')

if not os.path.exists('visuals'):
    os.makedirs('visuals')

print("Starting Visual Generation...")

# Load Data
try:
    df03 = pd.read_csv('03_output.csv')
    df04 = pd.read_csv('04_output.csv')
    df06 = pd.read_csv('06_output.csv')
    df02 = pd.read_csv('02_output.csv')

    # Merge for comprehensive view
    df_full = df06.merge(df03[['state', 'district', 'total_volume', 'monthly_growth_rate', 'volatility', 'pressure_index']], on=['state', 'district'])
    df_full = df_full.merge(df04[['state', 'district', 'child_ratio', 'adult_ratio']], on=['state', 'district'])
    df_full = df_full.merge(df02[['state', 'district', 'dominance_score', 'dominant_type']], on=['state', 'district'])
    print("Data Loaded Successfully.")
except Exception as e:
    print(f"Data Load Error: {e}")
    exit()

# 1. Crisis Quadrant
try:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_full, x='total_volume', y='monthly_growth_rate', hue='pressure_tier', palette='RdYlGn_r', s=100, alpha=0.7)
    plt.title('CRISIS QUADRANT: Infrastructure Load vs Velocity', fontsize=14, fontweight='bold')
    plt.xlabel('Total Service Volume')
    plt.ylabel('Monthly Growth Rate')
    plt.legend(title='Pressure Tier', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    criticals = df_full[df_full['pressure_tier'] == 'Critical Infrastructure Stress']
    if not criticals.empty:
        for i, row in criticals.head(5).iterrows():
            plt.text(row['total_volume'], row['monthly_growth_rate'], row['district'], fontsize=9)
            
    plt.tight_layout()
    plt.savefig('visuals/01_crisis_quadrant.png')
    print('Saved 01_crisis_quadrant.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 1: {e}")

# 2. Typology Matrix
try:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_full, x='child_ratio', y='adult_ratio', hue='classification', palette='viridis', style='classification', s=120)
    plt.title('TYPOLOGY MATRIX: Demand Source Segregation', fontsize=14, fontweight='bold')
    plt.xlabel('Child Ratio (School Demand)')
    plt.ylabel('Adult Ratio (Correction Demand)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('visuals/02_typology_matrix.png')
    print('Saved 02_typology_matrix.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 2: {e}")

# 3. Pressure Tier Distribution
try:
    plt.figure(figsize=(8, 5))
    tier_counts = df_full['pressure_tier'].value_counts()
    sns.barplot(x=tier_counts.index, y=tier_counts.values, palette='RdYlGn_r')
    plt.title('Infrastructure Pressure Distribution', fontsize=14, fontweight='bold')
    plt.ylabel('Number of Districts')
    plt.xlabel('Pressure Tier')
    plt.tight_layout()
    plt.savefig('visuals/03_pressure_distribution.png')
    print('Saved 03_pressure_distribution.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 3: {e}")

# 4. Volatility Pulse Lines
try:
    raw_all = pd.concat([pd.read_csv(f) for f in ['district_monthly_enrollment.csv', 'district_monthly_biometric.csv', 'district_monthly_demographic.csv']])
    monthly = raw_all.groupby(['district', 'month'])['total'].sum().reset_index()

    top_vol = df03.nlargest(3, 'volatility')['district'].tolist()
    top_stable = df03.nsmallest(3, 'volatility')['district'].tolist()
    targets = top_vol + top_stable
    plot_data = monthly[monthly['district'].isin(targets)]

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=plot_data, x='month', y='total', hue='district', style='district', markers=True, dashes=False)
    plt.title('VOLATILITY PULSE: Migration vs Stable Districts', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('visuals/04_volatility_pulse.png')
    print('Saved 04_volatility_pulse.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 4: {e}")

# 5. Seasonality Heatmap
try:
    top_15_dist = df03.nlargest(15, 'total_volume')['district'].tolist()
    heat_data = monthly[monthly['district'].isin(top_15_dist)]
    
    # Ensure pivot works even if duplicates exist (though group by district/month implies uniqueness)
    pivot = heat_data.pivot_table(index='district', columns='month', values='total', aggfunc='sum')

    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, cmap='YlOrRd', linewidths=0.5)
    plt.title('SEASONALITY HEATMAP: Volume Intensity', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visuals/05_seasonality_heatmap.png')
    print('Saved 05_seasonality_heatmap.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 5: {e}")

# 6. Dominance Spectrum
try:
    sample_districts = df02.sample(min(10, len(df02)), random_state=42)['district'].tolist()
    comp_data = df02[df02['district'].isin(sample_districts)][['district', 'enrollment_ratio', 'biometric_ratio', 'demographic_ratio']]
    comp_data.set_index('district', inplace=True)

    comp_data.plot(kind='bar', stacked=True, figsize=(10, 6), color=['skyblue', 'salmon', 'lightgreen'])
    plt.title('DOMINANCE SPECTRUM: Service Composition', fontsize=14, fontweight='bold')
    plt.ylabel('Ratio')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('visuals/06_dominance_spectrum.png')
    print('Saved 06_dominance_spectrum.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 6: {e}")

# 7. Action Allocation Donut
try:
    action_counts = df06['recommended_action'].value_counts()
    plt.figure(figsize=(7, 7))
    plt.pie(action_counts, labels=action_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('Strategic Resource Allocation Plan', fontsize=14, fontweight='bold')
    plt.savefig('visuals/07_action_allocation.png')
    print('Saved 07_action_allocation.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 7: {e}")

# 8. Risk Density
try:
    plt.figure(figsize=(8, 5))
    sns.kdeplot(df_full['pressure_index'], shade=True, color='r')
    plt.axvline(x=0.75, color='black', linestyle='--', label='Critical Threshold')
    plt.title('Systemic Risk Density', fontsize=14, fontweight='bold')
    plt.xlabel('Pressure Index')
    plt.legend()
    plt.tight_layout()
    plt.savefig('visuals/08_risk_density.png')
    print('Saved 08_risk_density.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 8: {e}")

# 9. Top 10 Critical
try:
    top_10 = df_full.nlargest(10, 'pressure_index')
    plt.figure(figsize=(10, 6))
    sns.barplot(data=top_10, y='district', x='pressure_index', palette='Reds_r')
    plt.title('TOP 10 CRITICAL ZONES', fontsize=14, fontweight='bold')
    plt.axvline(x=0.75, color='black', linestyle='--')
    plt.xlim(0, 1.1)
    plt.tight_layout()
    plt.savefig('visuals/09_top_10_critical.png')
    print('Saved 09_top_10_critical.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 9: {e}")

# 10. Stress by Typology
try:
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_full, x='classification', y='pressure_index', palette='Set2')
    plt.title('Stress Distribution by Operational Zone', fontsize=14, fontweight='bold')
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig('visuals/10_typology_stress.png')
    print('Saved 10_typology_stress.png')
    plt.close()
except Exception as e:
    print(f"Error Plot 10: {e}")

print("Visual Generation Complete.")
