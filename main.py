from utils import load_transaction_data, get_unique_isin, get_positions, format_table, compute_total_portfolio, load_isin_ticker_data, TwoWayDict
from utils import download_data, download_and_store_data
import utils
import os


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    transaction_file = os.path.join(base_dir, "data", "Transactions.csv")
    isin_ticker_file = os.path.join(base_dir, "data", "ISINs-Tickers.csv")

    transaction_data = load_transaction_data(transaction_file)
    isin_ticker_data = load_isin_ticker_data(isin_ticker_file)
    isins = get_unique_isin(transaction_data)
    isin_ticker_dict = TwoWayDict()
    isin_ticker_dict.populate_dict(isin_ticker_data, isins)
    tickers = [isin_ticker_dict.get(isin) for isin in isins]
    #tickers = complete_ticker(tickers)

    all_data = download_and_store_data(tickers)
    position = get_positions(transaction_data, isin_ticker_dict, all_data)
    print(position)
 
if __name__ == "__main__":
    main()

