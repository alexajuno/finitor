import click
from datetime import datetime
from typing import Optional
from ..core.database import FinanceDB
from ..core.currency import parse_amount, format_amount
from .utils import print_transaction_table
import json

@click.group()
def cli():
    """Personal Finance Manager CLI"""
    pass

@cli.command()
@click.argument('amount')
@click.argument('description')
@click.option('--category', help='Transaction category')
@click.option('--source', help='Transaction source')
@click.option('--date', help='Transaction date (YYYY-MM-DD)')
@click.option('--recurring', is_flag=True, help='Make this a recurring transaction')
@click.option('--frequency', help='Recurring frequency (daily/weekly/monthly/yearly)')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--notes', help='Additional notes')
def add(amount: str, description: str, category: Optional[str],
        source: Optional[str], date: Optional[str], recurring: bool,
        frequency: Optional[str], tags: Optional[str], notes: Optional[str]):
    """Add a new transaction"""
    db = FinanceDB()
    
    # Parse amount with VND shortcuts
    try:
        parsed_amount = parse_amount(amount)
    except ValueError:
        click.echo("Error: Invalid amount format. Use numbers with k (thousands), m (millions), or b (billions)")
        click.echo("Examples: 30k, 1.5m, 2.5k, 100")
        return
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(',')] if tags else None
    
    transaction_id = db.add_transaction(
        amount=parsed_amount,
        description=description,
        category=category,
        source=source,
        date=date or datetime.now().strftime('%Y-%m-%d'),
        is_recurring=recurring,
        recurring_frequency=frequency if recurring else None,
        tags=tag_list,
        notes=notes
    )
    
    click.echo(f"Transaction added successfully with ID: {transaction_id}")

@cli.command()
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--id', type=int, help='View specific transaction by ID')
@click.option('--search', help='Search transactions by description, category, or source')
def view(start_date: Optional[str], end_date: Optional[str],
         id: Optional[int], search: Optional[str]):
    """View transactions"""
    db = FinanceDB()
    
    if id:
        transaction = db.get_transaction(id)
        if transaction:
            click.echo("\n=== Transaction Details ===")
            click.echo(f"ID: {transaction[0]}")
            click.echo(f"Amount: {format_amount(transaction[1])}")
            click.echo(f"Description: {transaction[2]}")
            click.echo(f"Category: {transaction[3] or 'N/A'}")
            click.echo(f"Source: {transaction[4] or 'N/A'}")
            click.echo(f"Date: {transaction[5]}")
            click.echo(f"Created at: {transaction[6]}")
            if transaction[7]:  # is_recurring
                click.echo(f"Recurring: Yes ({transaction[8]})")
                click.echo(f"Next: {transaction[9]}")
            if transaction[10]:  # tags
                click.echo(f"Tags: {', '.join(transaction[10])}")
            if transaction[11]:  # notes
                click.echo(f"Notes: {transaction[11]}")
        else:
            click.echo("Transaction not found.")
    elif search:
        transactions = db.search_transactions(search)
        print_transaction_table(transactions)
    else:
        transactions = db.get_all_transactions()
        if start_date and end_date:
            transactions = db.get_transactions_by_date_range(start_date, end_date)
        print_transaction_table(transactions)

@cli.command()
@click.argument('transaction_id', type=int)
@click.option('--amount', help='New amount (can use k, m, b suffixes)')
@click.option('--description', help='New description')
@click.option('--category', help='New category')
@click.option('--source', help='New source')
@click.option('--date', help='New date (YYYY-MM-DD)')
@click.option('--recurring', is_flag=True, help='Make this a recurring transaction')
@click.option('--frequency', help='Recurring frequency (daily/weekly/monthly/yearly)')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--notes', help='Additional notes')
def update(transaction_id: int, amount: Optional[str], description: Optional[str],
          category: Optional[str], source: Optional[str], date: Optional[str],
          recurring: bool, frequency: Optional[str], tags: Optional[str],
          notes: Optional[str]):
    """Update a transaction"""
    db = FinanceDB()
    
    # Parse amount if provided
    parsed_amount = None
    if amount:
        try:
            parsed_amount = parse_amount(amount)
        except ValueError:
            click.echo("Error: Invalid amount format. Use numbers with k (thousands), m (millions), or b (billions)")
            click.echo("Examples: 30k, 1.5m, 2.5k, 100")
            return
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(',')] if tags else None
    
    if db.update_transaction(
        transaction_id=transaction_id,
        amount=parsed_amount,
        description=description,
        category=category,
        source=source,
        date=date,
        is_recurring=recurring if recurring else None,
        recurring_frequency=frequency if recurring else None,
        tags=tag_list,
        notes=notes
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
def balance():
    """View current balance"""
    db = FinanceDB()
    balance = db.get_balance()
    click.echo(f"\nCurrent Balance: {format_amount(balance)}")

@cli.command()
@click.option('--type', type=click.Choice(['category', 'source']), help='Summary type')
@click.option('--month', type=int, help='Month (1-12)')
@click.option('--year', type=int, help='Year (YYYY)')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
def summary(type: Optional[str], month: Optional[int], year: Optional[int],
           start_date: Optional[str], end_date: Optional[str]):
    """View transaction summaries"""
    db = FinanceDB()
    
    if type == 'category':
        summary = db.get_category_summary(start_date, end_date)
        click.echo("\nCategory Summary:")
        for category, amount in summary.items():
            click.echo(f"{category}: {format_amount(amount)}")
    elif type == 'source':
        summary = db.get_source_summary(start_date, end_date)
        click.echo("\nSource Summary:")
        for source, amount in summary.items():
            click.echo(f"{source}: {format_amount(amount)}")
    elif month and year:
        summary = db.get_monthly_summary(year, month)
        click.echo(f"\nSummary for {year}-{month:02d}:")
        click.echo(f"Total: {format_amount(summary['total'])}")
        click.echo(f"Income: {format_amount(summary['income'])}")
        click.echo(f"Expenses: {format_amount(summary['expenses'])}")

@cli.command()
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
def export(start_date: Optional[str], end_date: Optional[str]):
    """Export transactions to JSON"""
    db = FinanceDB()
    transactions = db.export_transactions(start_date, end_date)
    
    filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)
    
    click.echo(f"Transactions exported to {filename}")

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