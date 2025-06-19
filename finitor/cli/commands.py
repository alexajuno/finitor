import click
from datetime import datetime
from typing import Optional, List, Dict
from ..core.database import FinanceDB
from ..core.currency import parse_amount, format_amount, get_exchange_rates, get_common_currencies
from .utils import print_transaction_table
import json
import pandas as pd
import requests
from ..core.models import Transaction

# Load configuration for default settings
import os
CONFIG_PATH = os.path.expanduser('~/.finitor_config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

@click.group()
def cli():
    """Personal Finance Manager CLI"""
    pass

@cli.command()
@click.argument('amount')
@click.argument('description')
@click.option('--type', type=click.Choice(['income', 'expense']), default='expense', 
              help='Transaction type (income or expense)')
@click.option('--category', help='Transaction category')
@click.option('--source', help='Transaction source')
@click.option('--date', help='Transaction date (YYYY-MM-DD)')
@click.option('--currency', help='Currency code (USD, EUR, VND, etc.)')
def add(amount: str, description: str, type: str, category: Optional[str],
        source: Optional[str], date: Optional[str], currency: Optional[str]):
    """Add a new transaction"""
    db = FinanceDB()
    
    # Parse amount with currency shortcuts
    try:
        parsed_amount, detected_currency = parse_amount(amount, currency or db.default_currency)
        
        # Use detected currency if not explicitly specified
        if not currency:
            currency = detected_currency
            
        # Apply sign based on transaction type
        if type == 'expense' and parsed_amount > 0:
            parsed_amount = -parsed_amount
        elif type == 'income' and parsed_amount < 0:
            parsed_amount = abs(parsed_amount)
    except ValueError:
        click.echo("Error: Invalid amount format. Use numbers with k (thousands), m (millions), or b (billions)")
        click.echo("Examples: 30k, 1.5m, 2.5k, 100, $50, 100USD")
        return
    
    transaction_id = db.add_transaction(
        amount=parsed_amount,
        description=description,
        category=category,
        source=source,
        date=date or datetime.now().strftime('%Y-%m-%d'),
        currency=currency
    )
    
    click.echo(f"Transaction added successfully with ID: {transaction_id}")
    click.echo(f"Amount: {format_amount(parsed_amount, currency)}")

@cli.command()
@click.option('--type', 'txn_type', type=click.Choice(['income', 'expense']), help='Filter transactions by type (income or expense)')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--date', help='View transactions for a specific date (YYYY-MM-DD)')
@click.option('--id', type=int, help='View specific transaction by ID')
@click.option('--search', help='Search transactions by description, category, or source')
@click.option('--full-amounts', is_flag=True, help='Display full amount values without abbreviations')
@click.option('--currency', help='Display amounts in specified currency')
@click.option('-a', '--asc', 'order', flag_value='asc', default='asc', help='Sort transactions in ascending order (earliest first)')
@click.option('-d', '--desc', 'order', flag_value='desc', help='Sort transactions in descending order (latest first)')
@click.option('-n', '--limit', type=int, default=config.get('view_limit', 15), help='Limit number of transactions displayed')
@click.option('--all', 'show_all', is_flag=True, help='Show all transactions without limit')
def view(start_date: Optional[str], end_date: Optional[str], date: Optional[str],
         id: Optional[int], search: Optional[str], full_amounts: bool,
         currency: Optional[str], order: str, limit: int, show_all: bool, txn_type: Optional[str]):
    """View transactions"""
    db = FinanceDB()
    
    if id:
        transaction = db.get_transaction(id)
        if transaction:
            click.echo("\n=== Transaction Details ===")
            click.echo(f"ID: {transaction.id}")
            click.echo(f"Amount: {format_amount(transaction.amount, transaction.currency, full=full_amounts)}")
            click.echo(f"Description: {transaction.description}")
            click.echo(f"Category: {transaction.category or 'N/A'}")
            click.echo(f"Source: {transaction.source or 'N/A'}")
            click.echo(f"Date: {transaction.date}")
            click.echo(f"Currency: {transaction.currency}")
            click.echo(f"Created at: {transaction.created_at}")
        else:
            click.echo("Transaction not found.")
    elif search:
        transactions = db.search_transactions(search)
        # Filter transactions by type if specified
        if txn_type:
            if txn_type == 'income':
                transactions = [t for t in transactions if t.amount > 0]
            else:
                transactions = [t for t in transactions if t.amount < 0]
        if order == 'asc':
            transactions.reverse()
        # Apply limit unless full listing requested
        if not show_all:
            transactions = transactions[-limit:]
        print_transaction_table(transactions, full_amounts=full_amounts, display_currency=currency)
    else:
        transactions = db.get_all_transactions()
        if date:
            # If a specific date is provided, use it for both start and end date
            transactions = db.get_transactions_by_date_range(date, date)
        elif start_date and end_date:
            transactions = db.get_transactions_by_date_range(start_date, end_date)
        if order == 'asc':
            transactions.reverse()
        # Filter transactions by type if specified
        if txn_type:
            if txn_type == 'income':
                transactions = [t for t in transactions if t.amount > 0]
            else:
                transactions = [t for t in transactions if t.amount < 0]
        # Apply limit unless full listing requested
        if not show_all:
            transactions = transactions[-limit:]
        print_transaction_table(transactions, full_amounts=full_amounts, display_currency=currency)

@cli.command()
@click.argument('transaction_id', type=int)
@click.option('--amount', help='New amount (can use k, m, b suffixes)')
@click.option('--type', type=click.Choice(['income', 'expense']), help='New transaction type (income or expense)')
@click.option('--description', help='New description')
@click.option('--category', help='New category')
@click.option('--source', help='New source')
@click.option('--date', help='New date (YYYY-MM-DD)')
@click.option('--currency', help='New currency code (USD, EUR, VND, etc.)')
def update(transaction_id: int, amount: Optional[str], type: Optional[str], description: Optional[str],
          category: Optional[str], source: Optional[str], date: Optional[str],
          currency: Optional[str]):
    """Update a transaction"""
    db = FinanceDB()
    
    # Get existing transaction to preserve currency if not provided
    existing = db.get_transaction(transaction_id)
    if not existing:
        click.echo("Transaction not found.")
        return
    
    # Use Transaction dataclass attributes
    existing_currency = existing.currency
    
    # Parse amount if provided
    parsed_amount = None
    final_amount = existing.amount
    
    if amount:
        try:
            parsed_amount, detected_currency = parse_amount(amount, currency or existing_currency)
            
            # Use detected currency if not explicitly specified
            if not currency:
                currency = detected_currency

            # Handle type logic based on amount and existing transaction
            if type:
                # If type is explicitly provided, apply it
                if type == 'expense' and parsed_amount > 0:
                    parsed_amount = -parsed_amount
                elif type == 'income' and parsed_amount < 0:
                    parsed_amount = abs(parsed_amount)
            else:
                # If no type provided, default to expense (negative amount)
                if parsed_amount > 0:
                    parsed_amount = -parsed_amount
            
            final_amount = parsed_amount
        except ValueError:
            click.echo("Error: Invalid amount format. Use numbers with k (thousands), m (millions), or b (billions)")
            click.echo("Examples: 30k, 1.5m, 2.5k, 100, $50, 100USD")
            return
    elif type:
        # If only type is provided without amount, change the sign of existing amount
        if type == 'expense' and existing.amount > 0:
            final_amount = -existing.amount
        elif type == 'income' and existing.amount < 0:
            final_amount = abs(existing.amount)
    
    if db.update_transaction(
        transaction_id=transaction_id,
        amount=final_amount,
        description=description or existing.description,
        category=category or existing.category,
        source=source or existing.source,
        date=date or existing.date,
        currency=currency or existing_currency
    ):
        click.echo("Transaction updated successfully")
    else:
        click.echo("Transaction not found.")

@cli.command()
@click.argument('transaction_id', type=int)
def delete(transaction_id: int):
    """Delete a transaction"""
    db = FinanceDB()
    if db.delete_transaction(transaction_id):
        click.echo("Transaction deleted successfully")
    else:
        click.echo("Transaction not found.")

@cli.command()
@click.option('--full', is_flag=True, help='Display the full balance amount without abbreviations')
@click.option('--currency', help='Display balance in specified currency')
def balance(full: bool, currency: Optional[str]):
    """View current balance"""
    db = FinanceDB()
    balance_amount = db.get_balance(currency)
    
    display_currency = currency or db.default_currency
    click.echo(f"\nCurrent Balance: {format_amount(balance_amount, display_currency, full=full)}")

@cli.command()
@click.option('--type', type=click.Choice(['category', 'source']), help='Summary type')
@click.option('--month', type=int, help='Month (1-12)')
@click.option('--year', type=int, help='Year (YYYY)')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--currency', help='Display summary in specified currency')
def summary(type: Optional[str], month: Optional[int], year: Optional[int],
           start_date: Optional[str], end_date: Optional[str], currency: Optional[str]):
    """View transaction summaries"""
    db = FinanceDB()
    display_currency = currency or db.default_currency
    
    if type == 'category':
        summary = db.get_category_summary(start_date, end_date)
        click.echo("\nCategory Summary:")
        for category, amount in summary.items():
            click.echo(f"{category}: {format_amount(amount, display_currency)}")
    elif type == 'source':
        summary = db.get_source_summary(start_date, end_date)
        click.echo("\nSource Summary:")
        for source, amount in summary.items():
            click.echo(f"{source}: {format_amount(amount, display_currency)}")
    elif month and year:
        summary = db.get_monthly_summary(year, month)
        click.echo(f"\nSummary for {year}-{month:02d}:")
        click.echo(f"Total: {format_amount(summary['total'], display_currency)}")
        click.echo(f"Income: {format_amount(summary['income'], display_currency)}")
        click.echo(f"Expenses: {format_amount(summary['expenses'], display_currency)}")

@cli.command()
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--date', help='Export transactions for a specific date (YYYY-MM-DD)')
@click.option('--format', 'export_format', type=click.Choice(['json', 'csv', 'excel', 'html']), default='json', help='Export format')
@click.option('--full-amounts', is_flag=True, help='Export with full amount values without abbreviations')
@click.option('--currency', help='Display amounts in specified currency')
def export(start_date: Optional[str], end_date: Optional[str], date: Optional[str], export_format: str, full_amounts: bool, currency: Optional[str]):
    """Export transactions to a file in specified format"""
    db = FinanceDB()
    # Determine date range
    if date:
        start_date = end_date = date

    # Validate date range
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            if start_dt > end_dt:
                click.echo("Error: --start-date must be earlier than or equal to --end-date.")
                return
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD.")
            return

    transactions = db.export_transactions(start_date, end_date)

    # Handle no transactions
    if not transactions:
        click.echo("No transactions found for the given criteria.")
        return

    df = pd.DataFrame(transactions)
    display_currency = currency or db.default_currency

    # Format amounts
    df['amount'] = df['amount'].apply(lambda x: format_amount(x, display_currency, full=full_amounts))

    # Determine filename and extension
    ext = 'json' if export_format == 'json' else 'csv' if export_format == 'csv' else 'xlsx' if export_format == 'excel' else 'html'
    filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

    if export_format == 'json':
        records = df.to_dict(orient='records')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    elif export_format == 'csv':
        df.to_csv(filename, index=False)
    elif export_format == 'excel':
        try:
            df.to_excel(filename, index=False)
        except ModuleNotFoundError:
            click.echo("Error: openpyxl is required for Excel export. Please install it using 'pip install openpyxl'.")
            return
    elif export_format == 'html':
        df.to_html(filename, index=False)

    click.echo(f"\nTransactions exported to {filename}")

# Add new currency commands
@cli.command()
def currencies():
    """List all available currencies"""
    db = FinanceDB()
    currencies = db.get_currencies()
    
    if not currencies:
        click.echo("No currencies configured.")
        return
    
    click.echo("\n=== Available Currencies ===")
    click.echo(f"{'Code':<5} {'Name':<25} {'Exchange Rate':<15} {'Last Updated'}")
    click.echo("-" * 60)
    
    for currency in currencies:
        click.echo(f"{currency['code']:<5} {currency['name']:<25} {currency['exchange_rate']:<15.6f} {currency['last_updated']}")

@cli.command()
@click.argument('code')
@click.argument('name')
@click.argument('exchange_rate', type=float)
def add_currency(code: str, name: str, exchange_rate: float):
    """Add or update a currency"""
    db = FinanceDB()
    
    if db.add_currency(code, name, exchange_rate):
        click.echo(f"Currency {code} added/updated successfully")
    else:
        click.echo("Failed to add currency")

@cli.command()
def update_rates():
    """Update currency exchange rates from online source"""
    db = FinanceDB()
    
    click.echo("Fetching latest exchange rates...")
    try:
        rates = get_exchange_rates("USD")
        
        if not rates:
            click.echo("Failed to fetch exchange rates.")
            return
        
        # Update each currency in the database
        updated = 0
        for code, rate in rates.items():
            # Get existing currency data if available
            currency_data = db.get_currency(code)
            name = currency_data["name"] if currency_data else code
            
            if db.add_currency(code, name, rate):
                updated += 1
        
        click.echo(f"Updated exchange rates for {updated} currencies.")
    except Exception as e:
        click.echo(f"Error updating rates: {e}")

@cli.command()
def import_currencies():
    """Import common currencies"""
    db = FinanceDB()
    
    common_currencies = get_common_currencies()
    rates = get_exchange_rates("USD")
    
    if not rates:
        click.echo("Failed to fetch exchange rates. Using default values.")
    
    imported = 0
    for currency in common_currencies:
        code = currency["code"]
        name = currency["name"]
        
        # Use exchange rate from API if available, otherwise use 1.0
        rate = rates.get(code, 1.0)
        
        if db.add_currency(code, name, rate):
            imported += 1
    
    click.echo(f"Imported {imported} common currencies.")

@cli.command()
@click.argument('category')
@click.argument('amount')
@click.argument('period')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
def budget(category: str, amount: str, period: str,
          start_date: Optional[str], end_date: Optional[str]):
    """Add a new budget"""
    db = FinanceDB()
    
    # Parse amount with VND shortcuts
    try:
        parsed_amount = parse_amount(amount)
    except ValueError:
        click.echo("Error: Invalid amount format. Use numbers with k (thousands), m (millions), or b (billions)")
        click.echo("Examples: 30k, 1.5m, 2.5k, 100")
        return
    
    budget_id = db.add_budget(
        category=category,
        amount=parsed_amount,
        period=period,
        start_date=start_date or datetime.now().strftime('%Y-%m-%d'),
        end_date=end_date
    )
    click.echo(f"Budget added successfully with ID: {budget_id}")

@cli.command()
def alerts():
    """View unread alerts"""
    db = FinanceDB()
    alerts = db.get_unread_alerts()
    
    if alerts:
        click.echo("\nUnread Alerts:")
        for alert in alerts:
            click.echo(f"[{alert[0]}] {alert[2]} ({alert[1]})")
    else:
        click.echo("No unread alerts.")

if __name__ == '__main__':
    cli()
    
@cli.command()
@click.option('--view-limit', type=int, help='Set default view limit')
def setting(view_limit: Optional[int]):
    """Configure finitor settings"""
    if view_limit is not None:
        config['view_limit'] = view_limit
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)
        click.echo(f"Default view limit set to {view_limit}")
    else:
        click.echo(f"Current view limit: {config.get('view_limit', 15)}")