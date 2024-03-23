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
    stock_sales_values = {stock['name']: sum(rateQuantity['rate'] * rateQuantity['quantity'] for rateQuantity in stock['rateQuantities']) for stock in stocks}
    total_stock_value = sum(stock_sales_values.values())

    for ledger in ledgers:
        ledger_target_sales = ledger['totalSales']
        allocated_sales = 0
        ledger_start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        ledger_end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        date_range = list(generate_date_ranges(ledger_start_date, ledger_end_date))

        random.shuffle(stocks)
        
        for date in date_range:
            daily_sales_allocated = False
            for stock in stocks:
                stock_value_ratio = stock_sales_values[stock['name']] / total_stock_value
                daily_target_sales = ledger_target_sales * stock_value_ratio / len(date_range)
                
                for rateQuantity in stock['rateQuantities']:
                    if rateQuantity['quantity'] <= 0 or allocated_sales >= ledger_target_sales:
                        continue

                    max_quantity_for_target = min(rateQuantity['quantity'], int(daily_target_sales / rateQuantity['rate']))
                    allocated_sales += max_quantity_for_target * rateQuantity['rate']
                    daily_sales_allocated = True
                    
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
                

    return detailed_bills


detailed_bills_random = distribute_stocks_adjusted(stocks, ledgers)

def adjust_and_reallocate_stocks(ledgers, detailed_bills):
    #Helper function to identify unallocated dates for a ledger
    def get_unallocated_dates(ledger, allocated_dates):
        start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        all_dates = {start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)}
        return list(all_dates - set(allocated_dates))

    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    new_detailed_bills = []  # To store adjusted and newly allocated bills

    for ledger in ledgers:
        ledger_bills = [bill for bill in detailed_bills if bill['ledger_name'] == ledger['name']]
        allocated_dates = {datetime.strptime(bill['date'], "%Y-%m-%d") for bill in ledger_bills}
        unallocated_dates = get_unallocated_dates(ledger, allocated_dates)
        # print(f"Unallocated dates for ledger '{ledger['name']}': {unallocated_dates}")
        stock_pool = []

        # Adjustment Phase: Create a pool of stocks by subtracting up to 10% from each allocation
        for bill in ledger_bills:
            subtraction = round(bill['quantity'] * 0.1)  # Subtract up to 10%
            if subtraction > 0:
                bill['quantity'] -= subtraction
                bill['total_sales'] = bill['quantity'] * bill['rate']
                # Add the subtracted stock to the pool
                stock_pool.append({'item_name': bill['item_name'], 'quantity': subtraction, 'rate': bill['rate']})

        # Reallocation Phase: Distribute the pooled stocks to unallocated dates
        for date in unallocated_dates:
            for stock in stock_pool:
                if stock['quantity'] <= 0:
                    continue  # Skip if no quantity left in the pool
                # Allocate from the pool to this unallocated date
                allocated_quantity = min(stock['quantity'], round(stock['rate']))  # Example allocation logic
                stock['quantity'] -= allocated_quantity
                print(f"Allocating {allocated_quantity} of {stock['item_name']} to {ledger['name']} on {date.strftime('%Y-%m-%d')}")
                new_detailed_bills.append({
                    'ledger_name': ledger['name'],
                    'date': date.strftime("%Y-%m-%d"),
                    'item_name': stock['item_name'],
                    'quantity': allocated_quantity,
                    'rate': stock['rate'],
                    'total_sales': allocated_quantity * stock['rate'],
                })

    # Combine original adjusted bills with new allocations
    detailed_bills = [bill for bill in detailed_bills if bill['quantity'] > 0] + new_detailed_bills
    return detailed_bills

# Usage example:
# Assuming 'stocks' and 'ledgers' are defined and 'detailed_bills' have been generated by previous logic
adjusted_detailed_bills = adjust_and_reallocate_stocks(ledgers, detailed_bills_random)


# see which ledgers are allocates how much sales
ledger_sales = {ledger['name']: 0 for ledger in ledgers}
for bill in adjusted_detailed_bills:
    ledger_sales[bill['ledger_name']] += bill['total_sales']

print(ledger_sales)

import csv
import os

output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

output_file = os.path.join(output_directory, "detailed_billsb1.csv")

with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=adjusted_detailed_bills[0].keys())
    writer.writeheader()
    writer.writerows(adjusted_detailed_bills)
