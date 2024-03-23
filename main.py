# Import necessary libraries
from datetime import datetime, timedelta
from data import stocks, ledgers

# Step 1 and Step 2 are already outlined. Let's focus on completing Step 3 with detailed functionality.

def generate_date_ranges(start_date, end_date, num_days):
    # Generate date ranges that cover the entire period from start_date to end_date
    for n in range(num_days):
        yield start_date + timedelta(days=n)

# Let's fix the distribute_stock_items_adjusted function
def distribute_stock_items_adjusted(allocated_sales, stocks, ledger_details):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    
    for ledger in ledger_details:
        start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        num_days = (end_date - start_date).days + 1
        
        date_ranges = list(generate_date_ranges(start_date, end_date, num_days))
        
        for date in date_ranges:
            bill = {
                'ledger_id': ledger['id'],
                'date': date.strftime("%Y-%m-%d"),
                'items': [],
                'total_sales': 0
            }
            
            remaining_daily_sales = ledger['allocatedSales'] / num_days

            # Distribute sales across stock items for the day
            for stock in stocks:
                for rate_quantity in stock['rateQuantities']:
                    if remaining_daily_sales <= 0:
                        break

                    max_possible_quantity = min(rate_quantity['quantity'], remaining_daily_sales / rate_quantity['rate'])
                    quantity_sold = min(rate_quantity['quantity'], round(max_possible_quantity))
                    
                    if quantity_sold > 0:
                        sales_at_this_rate = quantity_sold * rate_quantity['rate']
                        bill['items'].append({
                            'item_name': stock['name'],
                            'quantity': quantity_sold,
                            'rate': rate_quantity['rate'],
                            'total_sales': sales_at_this_rate
                        })
                        rate_quantity['quantity'] -= quantity_sold
                        remaining_daily_sales -= sales_at_this_rate
                        bill['total_sales'] += sales_at_this_rate
                        
            if bill['total_sales'] > 0:  # Ensure the bill has sales before adding
                detailed_bills.append(bill)
                
            # Adjust the ledger's allocated sales for rounding off in quantities
            ledger['allocatedSales'] -= bill['total_sales']
            num_days -= 1  # Decrement days as one day's bill is processed
            
    return detailed_bills


# Update the `allocated_sales` calculation to include the percentage-based distribution
total_sales_amount = sum(rq['rate'] * rq['quantity'] for stock in stocks for rq in stock['rateQuantities'])
total_requested_sales = sum(ledger['totalSales'] for ledger in ledgers)
ledgers_with_allocated_sales = [{
    **ledger, 'allocatedSales': ledger['totalSales'] / total_requested_sales * total_sales_amount
} for ledger in ledgers]

# Allocate sales and generate detailed bills with adjusted function
allocated_sales = [{**ledger, 'allocatedSales': ledger['totalSales'] / total_requested_sales * total_sales_amount} for ledger in ledgers]
detailed_bills_adjusted = distribute_stock_items_adjusted(allocated_sales, stocks, ledgers_with_allocated_sales)

# For demonstration, print the first few detailed bills
for bill in detailed_bills_adjusted[:5]:
    print(bill)


#save each bill to different csv
import csv
import os
# Create a directory to store the CSV files
output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

# save all to one csv file
with open('detailed_bills.csv', 'w', newline='') as csvfile:
    fieldnames = ['ledger_id', 'date', 'item_name', 'quantity', 'rate', 'total_sales']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for bill in detailed_bills_adjusted:
        for item in bill['items']:
            writer.writerow({**item, 'ledger_id': bill['ledger_id'], 'date': bill['date']})
