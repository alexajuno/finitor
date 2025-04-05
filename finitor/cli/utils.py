from typing import List, Tuple, Optional
from tabulate import tabulate
from ..core.currency import format_amount, convert_currency
from ..core.database import FinanceDB

def print_transaction_table(transactions: List[Tuple], full_amounts: bool = False, 
                           display_currency: Optional[str] = None):
    """
    Print transactions in a formatted table
    
    Parameters:
    transactions (List[Tuple]): The list of transactions to display
    full_amounts (bool): If True, display the full amount without abbreviations
    display_currency (Optional[str]): If provided, convert all amounts to this currency
    """
    if not transactions:
        print("No transactions found.")
        return
    
    # Initialize DB for currency conversion if needed
    db = None
    if display_currency:
        db = FinanceDB()
    
    # Prepare table data
    table_data = []
    for t in transactions:
        amount = t[1]
        currency = t[6]  # Currency is stored at index 6
        
        # Convert amount if display_currency is specified
        if display_currency and display_currency != currency:
            amount = db._convert_currency_func(amount, currency, display_currency)
            display_amt = format_amount(amount, display_currency, full=full_amounts)
        else:
            display_amt = format_amount(amount, currency, full=full_amounts)
        
        table_data.append([
            t[0],  # ID
            display_amt,  # Amount
            t[2],  # Description
            t[3] or 'N/A',  # Category
            t[4] or 'N/A',  # Source
            t[5],  # Date
            t[6]  # Currency
        ])
    
    # Define headers
    headers = [
        'ID', 'Amount', 'Description', 'Category', 'Source',
        'Date', 'Currency'
    ]
    
    # Print table
    print(tabulate(
        table_data,
        headers=headers,
        tablefmt='grid',
        numalign='right',
        stralign='left'
    ))

def format_currency_list(currencies: List[dict]) -> str:
    """
    Format a list of currencies for display
    
    Parameters:
    currencies (List[dict]): List of currency dictionaries
    
    Returns:
    str: Formatted currency list
    """
    if not currencies:
        return "No currencies available."
    
    table_data = []
    for c in currencies:
        table_data.append([
            c['code'],
            c['name'],
            f"{c['exchange_rate']:.6f}",
            c['last_updated']
        ])
    
    headers = ['Code', 'Name', 'Exchange Rate', 'Last Updated']
    
    return tabulate(
        table_data,
        headers=headers,
        tablefmt='grid',
        numalign='right',
        stralign='left'
    ) 