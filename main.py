from utils import load_transaction_data, get_unique_isin, get_positions, format_table, compute_total_portfolio
import utils
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

dataFile = os.path.join(base_dir, "data", "Transactions.csv")
dataTable = load_transaction_data(dataFile)
isins = get_unique_isin(dataTable)

positions = get_positions(dataTable)
total = compute_total_portfolio(positions)
positions = format_table(positions)

print(positions)
print('Valore totale: ', total)
