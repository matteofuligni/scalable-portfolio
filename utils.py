import pandas as pd
import numpy as np
import requests
import os
import yfinance as yf

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
    data = pd.read_csv(path, sep=";", usecols=['ISIN', 'Mnemonic'])
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
            result = df.loc[df['ISIN'] == isin, 'Mnemonic']
            if not result.empty:
                ticker = result.iloc[0]  # Recupera il primo valore trovato
                self.add(ticker, isin)
            else:
                print(f"ISIN {isin} non trovato nel DataFrame.")

    def get(self, key):
        # Cerca nei dizionari forward e reverse
        return self.forward.get(key) or self.reverse.get(key)



def get_positions(df):
    df = df.dropna(subset=['isin'])
    df.loc[:, 'type'] = df['type'].replace('Savings plan', 'Buy')    
    isins = get_unique_isin(df)
    isin_dict = isin_to_description(df)
    positions = pd.DataFrame(columns=['ISIN', 'Description', 'Total Shares', 'Avg Price', 'Status'])
    
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
                raise('There is a problem in the "type" column')
            
        avg_buy_price = -total_buy_amount/total_buy_shares
        avg_sell_price = total_sell_amount/total_sell_shares if total_sell_shares !=0 else 0
        total_shares = total_buy_shares - total_sell_shares
        profit, status = [abs(total_buy_amount + total_sell_amount), 'Sold'] if total_shares <= 0.1 else [0, 'Hodl']     
        
        description = isin_dict.get(isin, "ISIN non trovato")
        newLine = {'ISIN':isin, 'Description':description, 'Total Shares':total_shares, 'Avg Buy Price':avg_buy_price,
                   'Avg Sell Price':avg_sell_price, 'Status':status, 'Profit':profit}
        positions = pd.concat([positions, pd.DataFrame([newLine])], ignore_index=True)
        
    #positions = positions[abs(positions['Total Shares']) >= 0.001]

    return positions
    
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

def get_data_from_yahoo(isin, period):
    return yf.download(isin, period=period)