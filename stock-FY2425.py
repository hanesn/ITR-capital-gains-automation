import pandas as pd
from datetime import datetime

# data expected format is given in sample csv
df = pd.read_csv('data.csv',usecols=["Stock name","Quantity","Buy date","Buy price","Buy value","Sell date","Sell price","Sell value","Realised P&L"])
df['Buy date'] = pd.to_datetime(df['Buy date'], dayfirst=True, errors='coerce')
df['Sell date'] = pd.to_datetime(df['Sell date'], dayfirst=True, errors='coerce')

# Filter only sold trades (Sell date not NaN)
df = df.dropna(subset=['Sell date'])
df['Holding_Days'] = (df['Sell date'] - df['Buy date']).dt.days

# Tag if STCG or LTCG
df['Type'] = df['Holding_Days'].apply(lambda x: 'STCG' if x < 365 else 'LTCG')

# Split STCG before/after 23 July 2024
split_date = datetime(2024, 7, 23)
def applySplitTag(row:pd.DataFrame):
    if row["Type"]=="STCG" and row["Sell date"]<split_date:
        return "Before_23July"
    elif row["Type"]=="STCG" and row["Sell date"]>=split_date:
        return "After_23July"
    else:
        return None
df['STCG_Period'] = df.apply(applySplitTag,axis=1)

# Summary for Schedule CG main table
summary = {
    'STCG_Before_23July': {
        'Sell_Value': df[df['STCG_Period'] == 'Before_23July']['Sell value'].sum(),
        'Buy_Value': df[df['STCG_Period'] == 'Before_23July']['Buy value'].sum(),
        'Gain': df[df['STCG_Period'] == 'Before_23July']['Realised P&L'].sum()
    },
    'STCG_After_23July': {
        'Sell_Value': df[df['STCG_Period'] == 'After_23July']['Sell value'].sum(),
        'Buy_Value': df[df['STCG_Period'] == 'After_23July']['Buy value'].sum(),
        'Gain': df[df['STCG_Period'] == 'After_23July']['Realised P&L'].sum()
    },
    'LTCG': {
        'Sell_Value': df[df['Type'] == 'LTCG']['Sell value'].sum(),
        'Buy_Value': df[df['Type'] == 'LTCG']['Buy value'].sum(),
        'Gain': df[df['Type'] == 'LTCG']['Realised P&L'].sum()
    }
}

# Table F logic (Advance Tax Quarters) -> **Only Gains**
def get_period(date):
    if date <= datetime(2024, 6, 15):
        return 'Upto 15/6'
    elif date <= datetime(2024, 9, 15):
        return '16/6-15/9'
    elif date <= datetime(2024, 12, 15):
        return '16/9-15/12'
    elif date <= datetime(2025, 3, 15):
        return '16/12-15/3'
    else:
        return '16/3-31/3'

df['Tax_Period'] = df['Sell date'].apply(get_period)

# Group STCG before/after July for Table F (Gains)
tableF_15 = df[df['STCG_Period'] == 'Before_23July'].groupby('Tax_Period')['Realised P&L'].sum().to_dict()
tableF_20 = df[df['STCG_Period'] == 'After_23July'].groupby('Tax_Period')['Realised P&L'].sum().to_dict()

# Final Output
print("\n=== Summary for Schedule CG ===")
print(summary)
print("\n=== Table F (15%) ===")
print(tableF_15)
print("\n=== Table F (20%) ===")
print(tableF_20)

# Totals for BFLA validation
print("\n=== Totals for BFLA ===")
print(f"15% Gain Total: {summary['STCG_Before_23July']['Gain']}")
print(f"20% Gain Total: {summary['STCG_After_23July']['Gain']}")
print(f"LTCG Total: {summary['LTCG']['Gain']}")