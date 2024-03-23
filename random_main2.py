import random
# Import necessary libraries
from datetime import datetime, timedelta
from data import stocks, ledgers

# Step 1 and Step 2 are already outlined. Let's focus on completing Step 3 with detailed functionality.


def generate_date_ranges(start_date, end_date, num_days):
    # Generate date ranges that cover the entire period from start_date to end_date
    for n in range(num_days):
        yield start_date + timedelta(days=n)

def distribute_stock_items_randomly(allocated_sales, stocks, ledger_details):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    
    for ledger in ledger_details:
        start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        num_days = (end_date - start_date).days + 1
        remaining_sales = ledger['allocatedSales']

        # Generate random daily sales targets, ensuring they sum up to the ledger's allocated sales
        daily_sales_targets = [random.random() for _ in range(num_days)]
        sum_daily_sales_targets = sum(daily_sales_targets)
        daily_sales_targets = [target / sum_daily_sales_targets * remaining_sales for target in daily_sales_targets]

        for i, date in enumerate(generate_date_ranges(start_date, end_date, num_days)):
            bill = {
                'ledger_id': ledger['id'],
                'date': date.strftime("%Y-%m-%d"),
                'items': [],
                'total_sales': 0
            }
            
            daily_sales_target = daily_sales_targets[i]
            remaining_daily_sales = daily_sales_target

            for stock in stocks:
                for rate_quantity in stock['rateQuantities'].copy():
                    if remaining_daily_sales <= 0 or rate_quantity['quantity'] == 0:
                        continue

                    max_possible_quantity = min(rate_quantity['quantity'], remaining_daily_sales / rate_quantity['rate'])
                    quantity_sold = round(max_possible_quantity)
                    
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
                remaining_sales -= bill['total_sales']
                
    # Adjust for any small discrepancies due to rounding in the final bill of each ledger
    if remaining_sales > 0:
        # Simple logic to adjust the last bill's total_sales
        detailed_bills[-1]['total_sales'] += remaining_sales
        # You might want to adjust the quantities of items in the last bill here

    return detailed_bills

# Assuming total_sales_amount and allocated_sales are already calculated as before
# detailed_bills_random = distribute_stock_items_randomly(allocated_sales, stocks, allocated_sales)


# Update the `allocated_sales` calculation to include the percentage-based distribution
total_sales_amount = sum(rq['rate'] * rq['quantity'] for stock in stocks for rq in stock['rateQuantities'])
total_requested_sales = sum(ledger['totalSales'] for ledger in ledgers)
ledgers_with_allocated_sales = [{
    **ledger, 'allocatedSales': ledger['totalSales'] / total_requested_sales * total_sales_amount
} for ledger in ledgers]

# Allocate sales and generate detailed bills with adjusted function
allocated_sales = [{**ledger, 'allocatedSales': ledger['totalSales'] / total_requested_sales * total_sales_amount} for ledger in ledgers]
detailed_bills_random = distribute_stock_items_randomly(allocated_sales, stocks, allocated_sales)

    #save each bill to different csv
import csv
import os
# Create a directory to store the CSV files
output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

# save all to one csv file
with open('detailed_billsp.csv', 'w', newline='') as csvfile:
    fieldnames = ['ledger_id', 'date', 'item_name', 'quantity', 'rate', 'total_sales']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for bill in detailed_bills_random:
        for item in bill['items']:
            writer.writerow({**item, 'ledger_id': bill['ledger_id'], 'date': bill['date']})