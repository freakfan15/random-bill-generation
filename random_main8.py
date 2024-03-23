import random
from datetime import datetime, timedelta
from data import stocks, ledgers

def generate_date_ranges(start_date, end_date):
    num_days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=n) for n in range(num_days)]

def shuffle_stocks(stocks):
    for stock in stocks:
        random.shuffle(stock['rateQuantities'])

def distribute_stocks_evenly(stocks, ledgers):
    detailed_bills = []
    global_start_date = datetime.strptime("2024-03-19", "%Y-%m-%d")
    shuffled_stocks = random.sample(stocks, len(stocks))

    for ledger in ledgers:
        ledger_start_date = global_start_date if ledger['beforeOrExact'] == 'Before' else datetime.strptime(ledger['date'], "%Y-%m-%d")
        ledger_end_date = datetime.strptime(ledger['date'], "%Y-%m-%d")
        date_range = generate_date_ranges(ledger_start_date, ledger_end_date)
        ledger_remaining_sales = ledger['totalSales']

        for date in date_range:
            if ledger_remaining_sales <= 0:
                break

            daily_sales_target = ledger_remaining_sales / (len(date_range) - date_range.index(date))
            daily_sales_distributed = 0

            for stock in shuffled_stocks:
                for rateQuantity in stock['rateQuantities']:
                    if rateQuantity['quantity'] <= 0 or daily_sales_distributed >= daily_sales_target:
                        continue

                    max_quantity_for_day = min(rateQuantity['quantity'], int((daily_sales_target - daily_sales_distributed) / rateQuantity['rate']))
                    daily_sales_distributed += max_quantity_for_day * rateQuantity['rate']
                    rateQuantity['quantity'] -= max_quantity_for_day
                    ledger_remaining_sales -= max_quantity_for_day * rateQuantity['rate']

                    detailed_bills.append({
                        'ledger_name': ledger['name'],
                        'date': date.strftime("%Y-%m-%d"),
                        'item_name': stock['name'],
                        'quantity': max_quantity_for_day,
                        'rate': rateQuantity['rate'],
                        'total_sales': max_quantity_for_day * rateQuantity['rate'],
                    })

    return detailed_bills


detailed_bills_random = distribute_stocks_evenly(stocks, ledgers)

# see which ledgers are allocates how much sales
ledger_sales = {ledger['name']: 0 for ledger in ledgers}
for bill in detailed_bills_random:
    ledger_sales[bill['ledger_name']] += bill['total_sales']

print(ledger_sales)

import csv
import os

output_directory = "detailed_bills"
os.makedirs(output_directory, exist_ok=True)

output_file = os.path.join(output_directory, "detailed_billsc1.csv")

with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=detailed_bills_random[0].keys())
    writer.writeheader()
    writer.writerows(detailed_bills_random)
