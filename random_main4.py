import random
# Import necessary libraries
from datetime import datetime, timedelta
from data import stocks, ledgers

# Step 1 and Step 2 are already outlined. Let's focus on completing Step 3 with detailed functionality.


def generate_date_ranges(start_date, end_date, num_days):
    # Generate date ranges that cover the entire period from start_date to end_date
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
        num_days = (ledger_end_date - ledger_start_date).days + 1
        date_range = list(generate_date_ranges(ledger_start_date, ledger_end_date, num_days))
        
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

# Assuming total_sales_amount and allocated_sales are already calculated as before
# detailed_bills_random = distribute_stock_items_randomly(allocated_sales, stocks, allocated_sales)

detailed_bills_random = distribute_stocks_evenly(stocks, ledgers)

def redistribute_quantities(detailed_bills, ledgers, tolerance=50):
    max_iterations = 1000
    iteration = 0
    has_changed = True

    while has_changed and iteration < max_iterations:
        has_changed = False
        iteration += 1

        # Calculate the current total sales for each ledger
        ledger_totals = {ledger['name']: 0 for ledger in ledgers}
        for bill in detailed_bills:
            ledger_totals[bill['ledger_name']] += bill['total_sales']

        # Determine over and under allocated ledgers
        over_allocated = {ledger['name']: ledger_totals[ledger['name']] - ledger['totalSales'] 
                          for ledger in ledgers if ledger_totals[ledger['name']] > ledger['totalSales'] + tolerance}
        under_allocated = {ledger['name']: ledger['totalSales'] - ledger_totals[ledger['name']] 
                           for ledger in ledgers if ledger_totals[ledger['name']] < ledger['totalSales'] - tolerance}

        # Function to redistribute stock from over-allocated to under-allocated ledgers
        # Function to redistribute stock from over-allocated to under-allocated ledgers
        def redistribute_stock(ledger_name, excess_stock):
            # Loop over the bills for the over-allocated ledger
            for bill in detailed_bills:
                if bill['ledger_name'] == ledger_name:
                    # Calculate how much can be taken from this bill without going below the threshold
                    potential_reduction = min(bill['quantity'] * bill['rate'], excess_stock)
                    reduction_quantity = int(potential_reduction / bill['rate'])
                    if bill['quantity'] - reduction_quantity <= 0:
                        # Skip if the reduction would cause negative or zero quantity
                        continue

                    # Update the bill
                    bill['quantity'] -= reduction_quantity
                    bill['total_sales'] = bill['quantity'] * bill['rate']

                    # Reduce the excess_stock by the amount removed from the bill
                    excess_stock -= reduction_quantity * bill['rate']

                    # Distribute the excess quantity to under-allocated ledgers
                    for under_name, under_amount in under_allocated.items():
                        if under_amount > 0:
                            additional_quantity = min(reduction_quantity, under_amount // bill['rate'])
                            # Find or create a bill to update
                            under_bill = next((b for b in detailed_bills if b['ledger_name'] == under_name and b['item_name'] == bill['item_name']), None)
                            if under_bill:
                                under_bill['quantity'] += additional_quantity
                                under_bill['total_sales'] += additional_quantity * bill['rate']
                            else:
                                detailed_bills.append({
                                    'ledger_name': under_name,
                                    'date': bill['date'],  # Same date, but this can be adjusted if necessary
                                    'item_name': bill['item_name'],
                                    'quantity': additional_quantity,
                                    'rate': bill['rate'],
                                    'total_sales': additional_quantity * bill['rate'],
                                })
                            under_amount -= additional_quantity * bill['rate']
                            reduction_quantity -= additional_quantity

                    # Break out of the loop if no excess stock is left
                    if excess_stock <= 0:
                        break

            return excess_stock

        # Run the redistribution in a loop
        for name, excess_stock in over_allocated.items():
            excess_stock = redistribute_stock(name, excess_stock)

    # Remove any zero-quantity bills that might have resulted from the redistribution
    detailed_bills = [bill for bill in detailed_bills if bill['quantity'] > 0]

    return detailed_bills


# Assume detailed_bills and ledgers are filled with your initial data
# Call the adjust_allocations function to adjust the bill allocations
adjusted_bills = redistribute_quantities(detailed_bills_random, ledgers)


# detailed_bills_random = adjust_ledger_allocations(detailed_bills_random, ledgers)

    #save each bill to different csv
import csv
import os
# Create a directory to store the CSV files
output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

# save to a single csv file
output_file = os.path.join(output_directory, "detailed_bills_randomy5.csv")
with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=adjusted_bills[0].keys())
    writer.writeheader()
    writer.writerows(adjusted_bills)