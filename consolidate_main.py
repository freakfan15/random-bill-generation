import pandas as pd
import numpy as np

from data import ledgers_data as ledgers

# Load the CSV file
file_path = 'detailed_billsa1.csv'  # Replace with the path to your CSV file
ledger_data = pd.read_csv(file_path)


# Function to redistribute sales while preserving total quantity
def redistribute_exact_quantities(df, date_range):
    np.random.seed(0)  # Seed for reproducibility
    output = []
    for _, row in df.iterrows():
        total_quantity = row['quantity']
        quantities = np.zeros(len(date_range), dtype=int)
        indices = np.random.choice(len(date_range), total_quantity, replace=True)
        quantities += np.bincount(indices, minlength=len(date_range))
        for quantity, date in zip(quantities, date_range):
            if quantity > 0:  # Only include days where sales occurred
                output.append({
                    'ledger_name': row['ledger_name'],
                    'date': date.strftime('%Y-%m-%d'),
                    'item_name': row['item_name'],
                    'quantity': quantity,
                    'rate': row['rate'],
                    'total_sales': quantity * row['rate']
                })
    return pd.DataFrame(output)

# Function to consolidate entries
def consolidate_entries(df):
    return df.groupby(['ledger_name', 'date', 'item_name', 'rate'], as_index=False).sum()

# Function to process all ledgers
def process_ledgers(ledger_data, ledgers):
    consolidated_data = pd.DataFrame()
    for ledger in ledgers:
        ledger_df = ledger_data[ledger_data['ledger_name'] == ledger['name']]
        date_range = pd.date_range(start=ledger['startDate'], end=ledger['endDate'])
        if not ledger_df.empty and not date_range.empty:
            redistributed_ledger_df = redistribute_exact_quantities(ledger_df, date_range)
            consolidated_ledger_df = consolidate_entries(redistributed_ledger_df)
            consolidated_data = pd.concat([consolidated_data, consolidated_ledger_df], ignore_index=True)
    return consolidated_data

# Process the ledgers
processed_ledgers_data = process_ledgers(ledger_data, ledgers)

# Save the processed data to a CSV file
processed_ledgers_data.to_csv('processed_ledgers_data.csv', index=False)

# Path where the CSV file is saved
print('Processed ledgers data saved to processed_ledgers_data.csv')