import pandas as pd

def load_transaction_data(path):
    """
    Load transaction data fron the csv dawnloaded from scalabel
    """
    data = pd.read_csv(path, sep=";").drop(columns='reference')
    data = data[data['status'] == 'Executed']
    return data

def get_unique_isin(df):
    """
    Return the unique ISIN list
    """
    unique_isin = df['isin'].dropna().unique()
    return unique_isin

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

def get_positions(df):
    
    df = df.dropna(subset=['isin'])
    df['type'] = df['type'].replace('Savings plan', 'Buy')
    df['shares'] = df['shares'].str.replace(',', '.').astype(float)
    df['price'] = df['price'].str.replace(',', '.').astype(float)
    df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    isins = get_unique_isin(df)
    isin_dict = isin_to_description(df)
    positions = pd.DataFrame(columns=['ISIN', 'Description', 'Total Shares', 'Avg Price'])
    
    for isin in isins:
        subDataFrame = df[df['isin'] == isin]
        total_shares = subDataFrame.apply(lambda row: row['shares'] if row['type'] == 'Buy' else -row['shares'], axis=1).sum()
        total_amount = (subDataFrame['shares'] * subDataFrame['price']).sum()
        
        avg_price = total_amount / total_shares if total_shares != 0 else 0
        
        description = isin_dict.get(isin, "ISIN non trovato")
        newLine = {'ISIN':isin, 'Description':description, 'Total Shares':total_shares, 'Avg Price':avg_price}
        positions = pd.concat([positions, pd.DataFrame([newLine])], ignore_index=True)
        
    positions = positions[abs(positions['Total Shares']) >= 0.001]
    
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