import random
from datetime import datetime, timedelta
from data import stocks, ledgers

def generate_date_ranges(start_date, end_date):
    # Generate date ranges that cover the entire period from start_date to end_date
    num_days = (end_date - start_date).days + 1
    for n in range(num_days):
        yield start_date + timedelta(days=n)


def shuffle_stocks(stocks):
    """Shuffle the rate quantities for each stock to promote diverse distribution."""
    for stock in stocks:
        random.shuffle(stock['rateQuantities'])

def distribute_stocks_evenly(stocks, ledgers):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    
    shuffle_stocks(stocks)  # Shuffle stocks to ensure varied distribution

    for ledger in ledgers:
        ledger_start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        ledger_end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        # num_days = (ledger_end_date - ledger_start_date).days + 1
        date_range = list(generate_date_ranges(ledger_start_date, ledger_end_date))
        
        for date in date_range:
            daily_allocation = {stock['name']: [] for stock in stocks}
            
            for stock in stocks:
                for rateQuantity in stock['rateQuantities']:
                    if rateQuantity['quantity'] <= 0:
                        continue
                    
                    # Allocate a portion of this rateQuantity to today's bill
                    quantity_to_allocate = min(rateQuantity['quantity'], max(1, rateQuantity['quantity'] // len(date_range)))
                    rateQuantity['quantity'] -= quantity_to_allocate
                    
                    daily_allocation[stock['name']].append({
                        'item_name': stock['name'],
                        'quantity': quantity_to_allocate,
                        'rate': rateQuantity['rate'],
                        'total_sales': quantity_to_allocate * rateQuantity['rate']
                    })
            
            # Create bills for the day
            for stock_name, allocations in daily_allocation.items():
                for allocation in allocations:
                    if allocation['quantity'] > 0:  # Only add to bills if there's a positive allocation
                        detailed_bills.append({
                            'ledger_name': ledger['name'],
                            'date': date.strftime("%Y-%m-%d"),
                            'item_name': allocation['item_name'],
                            'quantity': allocation['quantity'],
                            'rate': allocation['rate'],
                            'total_sales': allocation['total_sales'],
                        })
                        
    return detailed_bills

import random

def adjust_allocations(detailed_bills, ledgers, tolerance=50):
    max_iterations = 1000
    iteration = 0
    adjusted = False

    while iteration < max_iterations and not adjusted:
        adjusted = True
        iteration += 1

        # Step 1: Recalculate total sales for each ledger
        ledger_sales = {ledger['name']: sum(bill['total_sales'] for bill in detailed_bills if bill['ledger_name'] == ledger['name']) for ledger in ledgers}

        # Step 2: Determine over-allocated and under-allocated ledgers
        over_allocated = {ledger['name']: ledger_sales[ledger['name']] - ledger['totalSales'] for ledger in ledgers if ledger_sales[ledger['name']] > ledger['totalSales'] + tolerance}
        under_allocated = {ledger['name']: ledger['totalSales'] - ledger_sales[ledger['name']] for ledger in ledgers if ledger_sales[ledger['name']] < ledger['totalSales'] - tolerance}


        # Redistribution pool for collecting excess stocks
        redistribution_pool = []

        # Step 3: Adjust over-allocated ledgers and collect excess stocks
        for name, excess in over_allocated.items():
            for bill in [b for b in detailed_bills if b['ledger_name'] == name]:
                average_quantity = sum(b['quantity'] for b in detailed_bills if b['ledger_name'] == name) // len([b for b in detailed_bills if b['ledger_name'] == name])
                if bill['quantity'] > average_quantity:
                    excess_quantity = bill['quantity'] - average_quantity
                    bill['quantity'] -= excess_quantity
                    bill['total_sales'] = bill['quantity'] * bill['rate']
                    redistribution_pool.append({'item_name': bill['item_name'], 'quantity': excess_quantity, 'rate': bill['rate']})

        # Step 4: Redistribute excess stocks to under-allocated ledgers
        for stock in redistribution_pool:
            for ledger in ledgers:
                if ledger['name'] in under_allocated and stock['quantity'] > 0:
                    distribute_to_ledger = min(stock['quantity'], under_allocated[ledger['name']] // stock['rate'])
                    detailed_bills.append({
                        'ledger_name': ledger['name'],
                        # Use the distribution logic from distribute_stocks_evenly here
                        'date': datetime.now().strftime('%Y-%m-%d'),  # Placeholder, adjust accordingly
                        'item_name': stock['item_name'],
                        'quantity': distribute_to_ledger,
                        'rate': stock['rate'],
                        'total_sales': distribute_to_ledger * stock['rate'],
                    })
                    stock['quantity'] -= distribute_to_ledger
                    under_allocated[ledger['name']] -= distribute_to_ledger * stock['rate']
                    if under_allocated[ledger['name']] <= tolerance:
                        break  # Move to the next under-allocated ledger if this one is satisfied

        # Check if adjustments have brought all ledgers within tolerance
        for ledger in ledgers:
            total_sales = sum(b['total_sales'] for b in detailed_bills if b['ledger_name'] == ledger['name'])
            if abs(total_sales - ledger['totalSales']) > tolerance:
                adjusted = False
                break  # Additional adjustments needed

        iteration += 1

    return [bill for bill in detailed_bills if bill['quantity'] > 0]  # Clean up any bills with zero quantities



# Now, using the provided stocks and ledgers data, run the function.
# detailed_bills_random = distribute_stocks_evenly(stocks, ledgers)
# adjusted_bills = adjust_allocations(detailed_bills_random, ledgers)


# Assuming stocks and ledgers are populated with your data
detailed_bills_random = distribute_stocks_evenly(stocks, ledgers)
# adjusted_bills = adjust_allocations(detailed_bills_random, ledgers)
# tolerance = 50

# # Verify the result
# for ledger in ledgers:
#     total_sales = sum(bill['total_sales'] for bill in adjusted_bills if bill['ledger_name'] == ledger['name'])
#     print(f"{ledger['name']}: {total_sales}, Target: {ledger['totalSales']}, Difference: {total_sales - ledger['totalSales']} within ±{tolerance}")

# Save each bill to a a single CSV file

import csv
import os

output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

output_file = os.path.join(output_directory, "detailed_billsk1.csv")

with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=detailed_bills_random[0].keys())
    writer.writeheader()
    writer.writerows(detailed_bills_random)
