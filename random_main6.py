import random
from datetime import datetime, timedelta
from data import stocks, ledgers

def generate_date_ranges(start_date, end_date):
    num_days = (end_date - start_date).days + 1
    for n in range(num_days):
        yield start_date + timedelta(days=n)

def shuffle_stocks(stocks):
    for stock in stocks:
        random.shuffle(stock['rateQuantities'])

def distribute_stocks_adjusted(stocks, ledgers):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    
    # Calculate the sales value for each stock
    stock_sales_values = {stock['name']: sum(rateQuantity['rate'] * rateQuantity['quantity'] for rateQuantity in stock['rateQuantities']) for stock in stocks}
    total_stock_value = sum(stock_sales_values.values())
    
    # Initial distribution based on ledger's share of total sales
    for ledger in ledgers:
        ledger_target_sales = ledger['totalSales']
        allocated_sales = 0  # Track allocated sales for this ledger
        
        ledger_start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        ledger_end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        date_range = list(generate_date_ranges(ledger_start_date, ledger_end_date))

        # Shuffle stocks to ensure varied distribution
        random.shuffle(stocks)

        for date in date_range:
            for stock in stocks:
                stock_value_ratio = stock_sales_values[stock['name']] / total_stock_value
                daily_target_sales = ledger_target_sales * stock_value_ratio / len(date_range)
                
                for rateQuantity in stock['rateQuantities']:
                    if rateQuantity['quantity'] <= 0 or allocated_sales >= ledger_target_sales:
                        continue

                    # Calculate quantity based on daily target sales
                    max_quantity_for_target = min(rateQuantity['quantity'], int(daily_target_sales / rateQuantity['rate']))
                    allocated_sales += max_quantity_for_target * rateQuantity['rate']
                    
                    # Adjust for over-allocation
                    if allocated_sales > ledger_target_sales:
                        over_allocation = allocated_sales - ledger_target_sales
                        reduce_quantity = int(over_allocation / rateQuantity['rate'])
                        max_quantity_for_target -= reduce_quantity
                        allocated_sales -= over_allocation
                    
                    rateQuantity['quantity'] -= max_quantity_for_target
                    
                    if max_quantity_for_target > 0:
                        detailed_bills.append({
                            'ledger_name': ledger['name'],
                            'date': date.strftime("%Y-%m-%d"),
                            'item_name': stock['name'],
                            'quantity': max_quantity_for_target,
                            'rate': rateQuantity['rate'],
                            'total_sales': max_quantity_for_target * rateQuantity['rate'],
                        })
    
    # Any further adjustments to ensure allocations match targets as closely as possible can be done here

    return detailed_bills


detailed_bills_random = distribute_stocks_adjusted(stocks, ledgers)

# see which ledgers are allocates how much sales
ledger_sales = {ledger['name']: 0 for ledger in ledgers}
for bill in detailed_bills_random:
    ledger_sales[bill['ledger_name']] += bill['total_sales']

print(ledger_sales)

import csv
import os

output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

output_file = os.path.join(output_directory, "detailed_billsa1.csv")

with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=detailed_bills_random[0].keys())
    writer.writeheader()
    writer.writerows(detailed_bills_random)
