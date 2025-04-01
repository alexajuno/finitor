from typing import List, Tuple
from tabulate import tabulate
from ..core.currency import format_amount

def print_transaction_table(transactions: List[Tuple], full_amounts: bool = False):
    """
    Print transactions in a formatted table
    
    Parameters:
    transactions (List[Tuple]): The list of transactions to display
    full_amounts (bool): If True, display the full amount without abbreviations
    """
    if not transactions:
        print("No transactions found.")
        return
    
    # Prepare table data
    table_data = []
    for t in transactions:
        table_data.append([
            t[0],  # ID
            format_amount(t[1], full=full_amounts),  # Amount
            t[2],  # Description
            t[3] or 'N/A',  # Category
            t[4] or 'N/A',  # Source
            t[5],  # Date
            'Yes' if t[7] else 'No',  # Recurring
            t[8] if t[7] else 'N/A',  # Frequency
            t[9] if t[7] else 'N/A',  # Next date
            ', '.join(t[10]) if t[10] else 'N/A'  # Tags
        ])
    
    # Define headers
    headers = [
        'ID', 'Amount', 'Description', 'Category', 'Source',
        'Date', 'Recurring', 'Frequency', 'Next', 'Tags'
    ]
    
    # Print table
    print(tabulate(
        table_data,
        headers=headers,
        tablefmt='grid',
        numalign='right',
        stralign='left'
    )) 