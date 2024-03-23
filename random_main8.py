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

from consolidate_main import process_ledgers

#convert detailed_bills_random to a pd dataframe
import pandas as pd
detailed_bills_random_df = pd.DataFrame(detailed_bills_random)

#from ledgers make a new array that stores ledgers data like this:
# ledgers_data = [
#     {"id": 1, "name": "Darshan Singh & Sons", "startDate": "2024-03-19", "endDate": "2024-03-28"},
#     {"id": 2, "name": "Ganesh Sharma Bricks Field", "startDate": "2024-03-19", "endDate": "2024-03-28"},
#     {"id": 3, "name": "Jai Ambey Brick Field", "startDate": "2024-03-20", "endDate": "2024-03-20"},
#     {"id": 4, "name": "Jai Ambey Bricks Field", "startDate": "2024-03-19", "endDate": "2024-03-31"},
#     {"id": 5, "name": "Raj Enterprises", "startDate": "2024-03-19", "endDate": "2024-03-27"},
#     {"id": 6, "name": "RJY Bricks", "startDate": "2024-03-19", "endDate": "2024-03-29"},
#     {"id": 7, "name": "Srinet Ent Bhatta", "startDate": "2024-03-19", "endDate": "2024-03-30"},
# ]
# where startDate and endDate are the start and end dates of the ledgers respectively
global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
ledgers_data = [{"id": ledger['id'], "name": ledger['name'], 
"startDate": global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d"),
 "endDate": ledger['date']} for ledger in ledgers]

final_data = process_ledgers(detailed_bills_random_df, ledgers_data)

# Save the processed data to a CSV file
final_data.to_csv('processed_ledgers_dataf1.csv', index=False)

# Path where the CSV file is saved
print('Processed ledgers data saved to processed_ledgers_data.csv')