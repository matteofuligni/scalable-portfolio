import pandas as pd

def load_transaction_data(path):
    """
    Load transaction data fron the csv dawnloaded from scalabel
    """
    data = pd.read_csv(path)
    return data