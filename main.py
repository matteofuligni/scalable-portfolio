from utils import load_transaction_data, get_unique_isin, get_positions, format_table, compute_total_portfolio, load_isin_ticker_data, TwoWayDict
from utils import get_data_from_yahoo
import utils
import os
from dotenv import load_dotenv

load_dotenv()
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")

base_dir = os.path.dirname(os.path.abspath(__file__))

transaction_file = os.path.join(base_dir, "data", "Transactions.csv")
isin_ticker_file = os.path.join(base_dir, "data", "ISINdatabase.csv")

transaction_data = load_transaction_data(transaction_file)
isin_ticker_data = load_isin_ticker_data(isin_ticker_file)
#print(df)
isins = get_unique_isin(transaction_data)

positions = get_positions(transaction_data)
#total = compute_total_portfolio(positions)
#print(positions['Avg Price'].sum())
#positions = format_table(positions)

print(positions)
print(isin_ticker_data.head())

isin_ticker_dict = TwoWayDict()
isin_ticker_dict.populate_dict(isin_ticker_data, isins)

for isin in isins:
    print(isin_ticker_dict.get(isin))
    dat = get_data_from_yahoo(isin, period='1mo')
    print(dat)

