import pandas as pd
import numpy as np
import requests
import os
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def load_transaction_data(path):
    """
    Load transaction data fron the csv dawnloaded from scalabel
    """
    data = pd.read_csv(path, sep=";", thousands='.', decimal=',').drop(columns='reference')
    data = data[data['status'] == 'Executed']
    return data

def load_isin_ticker_data(path):
    """
    Load ISIN-Ticker table fron the csv dawnloaded from from the Xetra Exchange 
    """
    data = pd.read_csv(path, sep=";", usecols=['isin', 'ticker'])
    return data

def get_unique_isin(df):
    """
    Return the unique ISINs list
    """
    unique_isin = df['isin'].dropna().unique()
    return unique_isin

def get_ticker_From_isin(df, isin):
    return

def isin_to_description(df):
    """
    Crea un dizionario che associa gli 'isin' unici alle rispettive 'description'.

    Parameters:
    df (pd.DataFrame): DataFrame contenente le colonne 'isin' e 'description'.

    Returns:
    dict: Dizionario con gli 'isin' come chiavi e le rispettive 'description' come valori.
    """

    filtered_df = df[['isin', 'description']].dropna(subset=['isin', 'description'])
    unique_isin = filtered_df.drop_duplicates(subset='isin')

    isin_dict = dict(zip(unique_isin['isin'], unique_isin['description']))

    return isin_dict

class TwoWayDict:
    def __init__(self):
        self.forward = {}
        self.reverse = {}

    def add(self, ticker, isin):
        # Evita duplicati o valori vuoti
        if ticker and isin:
            self.forward[ticker] = isin
            self.reverse[isin] = ticker

    def populate_dict(self, df, isins):
        for isin in isins:
            # Trova il ticker corrispondente
            result = df.loc[df['isin'] == isin, 'ticker']
            if not result.empty:
                ticker = result.iloc[0]  # Recupera il primo valore trovato
                self.add(ticker, isin)
            else:
                print(f"ISIN {isin} non trovato nel DataFrame.")

    def get(self, key):
        # Cerca nei dizionari forward e reverse
        return self.forward.get(key) or self.reverse.get(key)



def get_positions(df, isin_dict, data):
    df = df.dropna(subset=['isin'])
    df.loc[:, 'type'] = df['type'].replace('Savings plan', 'Buy')
    isins = get_unique_isin(df)
    isin_dict = isin_to_description(df)
    positions = pd.DataFrame(columns=['ISIN', 'Ticker', 'Description', 'Total Shares', 'Last Price', 'Avg Buy Price', 'Avg Sell Price', 'Status', 'Profit'])

    for isin in isins:
        subDataFrame = df[df['isin'] == isin]
        total_shares = 0
        total_buy_shares = 0
        total_buy_amount = 0
        total_sell_shares = 0
        total_sell_amount = 0

        for _, row in subDataFrame.iterrows():
            if row['type'] == 'Buy':
                total_buy_shares += row['shares']
                total_buy_amount += row['amount']
            elif row['type'] == 'Sell':
                total_sell_shares += row['shares']
                total_sell_amount += row['amount']
            else:
                raise ValueError('There is a problem in the "type" column')

        avg_buy_price = -total_buy_amount/total_buy_shares
        avg_sell_price = total_sell_amount/total_sell_shares if total_sell_shares != 0 else 0
        total_shares = total_buy_shares - total_sell_shares
        ticker = isin_dict.get(isin)

        # Ensure the last price is a scalar
        last_price = get_last_price(price_dict=data, ticker=ticker)
        if last_price == 0.0:
            print(f"Warning: No valid last price for ticker {ticker}. Setting to 0.")

        # Calculate profit
        if total_shares <= 0.1:
            profit = abs(total_buy_amount + total_sell_amount)
            status = 'Sold'
        else:
            profit = last_price * total_shares - abs(total_buy_amount + total_sell_amount)
            status = 'Hodl'

        newLine = {
            'ISIN': isin,
            'Ticker': ticker,
            'Description': isin_dict.get(isin, "ISIN non trovato"),
            'Total Shares': round(total_shares, 2),
            'Last Price': round(last_price, 2),
            'Avg Buy Price': round(avg_buy_price, 2),
            'Avg Sell Price': round(avg_sell_price, 2),
            'Status': status,
            'Profit': round(profit, 2)
        }

        positions = pd.concat([positions, pd.DataFrame([newLine])], ignore_index=True)
    return positions

def get_last_price(price_dict, ticker):
    """
    Get the last adjusted closing price for a given ticker from the price dictionary.
    """
    try:
        return float(price_dict[ticker]['Adj Close'].iloc[-1])
    except KeyError:
        print(f"No data found for ticker: {ticker}")
        return 0.0
    except IndexError:
        print(f"No valid price data for ticker: {ticker}")
        return 0.0
    
def format_table(df):
    # Formatta i numeri con separatori per migliaia e due cifre decimali
    formatted_df = df.copy()
    formatted_df['Total Shares'] = formatted_df['Total Shares'].apply(lambda x: f"{x:,.3f}")
    formatted_df['Avg Price'] = formatted_df['Avg Price'].apply(lambda x: f"{x:,.3f}")
    return formatted_df

def compute_total_portfolio(df):
    """_summary_

    Args:
        df (_type_): _description_

    Returns:
        _type_: _description_
    """
    total_position = (df['Total Shares']*df['Avg Price']).sum()
    return total_position 

def get_data_from_yahoo(check, ticker, interval='1d', period='1y'):
    """
    Check if the data is already present in the csv file, if not download the data from yahoo fiance and save it in the csv file.
    If present, download only the missing data from the last date presenti in the csv file.

    Args:
        isin (str): _description_
        interval (str): _description_
        period (str): _description_
    
    Returns:
        dataFrame: _description_
    """
    if check:
        path = os.path.join('data', 'historic_data', ticker, interval)
        print(f'Downloading data for {ticker}...')
        existing_data = load_data_from_csv(path)
        today_date = datetime.today().strftime('%Y-%m-%d')
        last_date = pd.to_datetime(existing_data['Date']).max()
        if today_date > last_date:
            delta = datetime.today() - last_date
            delta = delta.days
            if delta//30 > 0 and delta//365 == 0:
                period = '1y'
            elif delta//365 > 0 and delta//365*10 == 0:
                period = '10y'
            elif delta//365*10 > 0:
                period = '20y'
            else:
                period = '30y'
            new_data = yf.download(ticker, interval=interval, period=period)
            if new_data.empty:
                raise ValueError(f"Nessun dato trovato per {ticker}")
        new_data = new_data[new_data.index > last_date]
        if not new_data.empty:
            return pd.concat([existing_data, new_data])
        else:
            return existing_data
    else:
        new_data = yf.download(ticker, interval=interval, period=period)
        if new_data.empty:
            raise ValueError(f"Nessun dato trovato per {ticker}")
        return new_data
    
def download_and_store_data(tickers):
    """
    Downloads historical data for a list of tickers and stores it in a dictionary.

    Args:
        tickers: A list of stock/ETF tickers.

    Returns:
        A dictionary where keys are tickers and values are corresponding DataFrames.
    """
    data_dict = {}
    for ticker in tickers:
        try:
            data = yf.download(ticker, start="2000-01-01", end="2024-12-01")
            if not data.empty:
                data_dict[ticker] = data
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Error downloading data for {ticker}: {e}")
        return data_dict

def save_data_to_csv(df, path):
    """
    Aggiungere il controllo dei dati presenti e fino a che data.
    Se si stanno scaricando dati giornalieri, controllare se i dati sono già presenti e scaricare solo i dati mancanti più recenti a partire dall'ultimo giorno presente.
    Stessa cosa per i dati mensili e annuali.
    
    Args:
        df (pd.DataFrame): DataFrame contenente i dati storici.
        interval (str): Intervallo di tempo dei dati (es. '1d', '1mo', '1y').
        path (str): Percorso del file CSV dove salvare i dati.
    """
    
    df.to_csv(path, sep=';', decimal=',', index=False)


def check_if_path_exists(path):
    """_summary_
    check if path exists, if not create it
    
    Args: path (str): directory path
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f'Path {path} created')
    else:
        print(f'Path {path} already exists')
    
def load_data_from_csv(path):
    """_summary_
    
    Args:
        path (_type_): _description_
    
    Returns:
        _type_: _description_
    """
    return pd.read_csv(path, sep=';', decimal=',')
    
    
def download_data(tickers, interval, period):
    """_summary_
    
    Args:
        tickers (arr): _description_
        interval (str): _description_
        period (str): _description_
    
    Returns:
        _type_: _description_
    """
    def process_ticker(ticker):
        path = os.path.join('data', 'historic_data', ticker, interval)
        check_if_path_exists(path)
        check = check_if_data_exists(ticker, interval)
        data = get_data_from_yahoo(check, ticker, interval, period)
        save_data_to_csv(data, path)

    with ThreadPoolExecutor() as executor:
        executor.map(process_ticker, tickers)
    
    return 

def check_if_data_exists(ticker, interval):
    """_summary_
    
    Args:
        tickers (str): _description_
        interval (str): _description_
    
    Returns:
        bool: _description_
    """

    path = os.path.join('data', 'historic_data', ticker, interval, f"{ticker}.csv")
    if not os.path.exists(path):
        return False
    return True