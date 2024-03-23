from datetime import datetime, timedelta

from data import stocks, ledgers
# Helper function to generate date ranges for each ledger
def generate_date_ranges(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

# Main function to distribute stock items across ledgers and dates
def distribute_stock_items(stocks, ledgers):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")

    # Calculate the total sales value from all products
    total_sales_from_products = sum(
        rq['quantity'] * rq['rate'] for stock in stocks for rq in stock['rateQuantities']
    )

    for ledger in ledgers:
        ledger_end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        ledger['allocatedSales'] = 0
        dates = list(generate_date_ranges(global_start_date if ledger['beforeOrExact'] == "Before" else ledger_end_date, ledger_end_date))
        
        for stock in stocks:
            for rateQuantity in stock['rateQuantities']:
                # Distribute each rateQuantity across all dates for the ledger
                for date in dates:
                    # Allocate proportionally based on the ledger's total sales and the stock's rate
                    proportional_quantity = min(rateQuantity['quantity'], max(1, int(ledger['totalSales'] / total_sales_from_products * rateQuantity['quantity'])))
                    rateQuantity['quantity'] -= proportional_quantity
                    
                    # Create a detailed bill
                    detailed_bills.append({
                        'ledger_name': ledger['name'],
                        'date': date.strftime("%Y-%m-%d"),
                        'item_name': stock['name'],
                        'quantity': proportional_quantity,
                        'rate': rateQuantity['rate'],
                        'total_sales': proportional_quantity * rateQuantity['rate']
                    })
                    
                    ledger['allocatedSales'] += proportional_quantity * rateQuantity['rate']
                    
                    # Adjust if we've allocated more than available
                    if rateQuantity['quantity'] < 0:
                        print(f"Over-allocation error with {stock['name']}")

    # Final adjustments if necessary to match total sales
    # This is a simplified adjustment logic. You may need a more complex logic based on your exact requirements.
    total_allocated_sales = sum(bill['total_sales'] for bill in detailed_bills)
    discrepancy = total_sales_from_products - total_allocated_sales

    if discrepancy != 0:
        print(f"Discrepancy detected: {discrepancy}, additional adjustments required.")

    return detailed_bills

#Example of using the function with mock data
detailed_bills = distribute_stock_items(stocks, ledgers)

#For demonstration purposes, let's print the first few bills to verify
for bill in detailed_bills[:10]:
    print(bill)

    #save each bill to different csv
import csv
import os
# Create a directory to store the CSV files
output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

# Write all detailed bills to a single CSV file
output_file = os.path.join(output_directory, "detailed_billsr1.csv")
with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=detailed_bills[0].keys())
    writer.writeheader()
    writer.writerows(detailed_bills)
