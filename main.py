import sys
import argparse
from datetime import datetime
from db import FinanceDB
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Personal Finance Manager')
    parser.add_argument('--cli', action='store_true', help='Run in interactive CLI mode')
    
    # Add transaction command
    add_parser = argparse.ArgumentParser(description='Add a new transaction')
    add_parser.add_argument('amount', type=float, help='Amount (positive for income, negative for expense)')
    add_parser.add_argument('description', help='Transaction description')
    add_parser.add_argument('--category', help='Transaction category')
    add_parser.add_argument('--source', help='Transaction source')
    add_parser.add_argument('--date', help='Transaction date (YYYY-MM-DD)')
    
    # View transactions command
    view_parser = argparse.ArgumentParser(description='View transactions')
    view_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    view_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    view_parser.add_argument('--id', type=int, help='View specific transaction by ID')
    
    # Export command
    export_parser = argparse.ArgumentParser(description='Export transactions')
    export_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    export_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # Summary commands
    summary_parser = argparse.ArgumentParser(description='View summaries')
    summary_parser.add_argument('--month', type=int, help='Month (1-12)')
    summary_parser.add_argument('--year', type=int, help='Year (YYYY)')
    summary_parser.add_argument('--type', choices=['category', 'source'], help='Summary type')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.add_parser('add', parents=[add_parser])
    subparsers.add_parser('view', parents=[view_parser])
    subparsers.add_parser('export', parents=[export_parser])
    subparsers.add_parser('summary', parents=[summary_parser])
    
    return parser.parse_args()

def handle_cli_command(db: FinanceDB, args):
    if args.command == 'add':
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        transaction_id = db.add_transaction(
            args.amount,
            args.description,
            args.category,
            args.source,
            date
        )
        print(f"Transaction added successfully with ID: {transaction_id}")
    
    elif args.command == 'view':
        if args.id:
            transaction = db.get_transaction(args.id)
            if transaction:
                print("\n=== Transaction Details ===")
                print(f"ID: {transaction[0]}")
                print(f"Amount: {transaction[1]:.2f}")
                print(f"Description: {transaction[2]}")
                print(f"Category: {transaction[3] or 'N/A'}")
                print(f"Source: {transaction[4] or 'N/A'}")
                print(f"Date: {transaction[5]}")
                print(f"Created at: {transaction[6]}")
            else:
                print("Transaction not found.")
        else:
            transactions = db.get_all_transactions()
            if args.start_date and args.end_date:
                transactions = db.get_transactions_by_date_range(args.start_date, args.end_date)
            print_transaction_table(transactions)
    
    elif args.command == 'export':
        transactions = db.export_transactions(args.start_date, args.end_date)
        filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
        print(f"Transactions exported to {filename}")
    
    elif args.command == 'summary':
        if args.type == 'category':
            summary = db.get_category_summary()
            print("\nCategory Summary:")
            for category, amount in summary.items():
                print(f"{category}: {amount:.2f} VND")
        elif args.type == 'source':
            summary = db.get_source_summary()
            print("\nSource Summary:")
            for source, amount in summary.items():
                print(f"{source}: {amount:.2f} VND")
        elif args.month and args.year:
            summary = db.get_monthly_summary(args.year, args.month)
            print(f"\nSummary for {args.year}-{args.month:02d}:")
            print(f"Total: {summary['total']:.2f} VND")
            print(f"Income: {summary['income']:.2f} VND")
            print(f"Expenses: {summary['expenses']:.2f} VND")

def print_menu():
    print("\n=== Personal Finance Manager ===")
    print("1. Add new transaction")
    print("2. View all transactions")
    print("3. View transaction details")
    print("4. Update transaction")
    print("5. Delete transaction")
    print("6. View current balance")
    print("7. View transactions by date range")
    print("8. View category summary")
    print("9. View source summary")
    print("10. View monthly summary")
    print("11. Export transactions")
    print("0. Exit")
    print("=============================")
    print("Press Ctrl+C at any time to return to main menu")

def get_valid_amount() -> float:
    while True:
        try:
            amount = float(input("Enter amount (positive for income, negative for expense): "))
            return amount
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

def get_valid_date() -> str:
    while True:
        try:
            date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
            if not date_str:
                return datetime.now().strftime('%Y-%m-%d')
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

def print_transaction_table(transactions):
    if not transactions:
        print("No transactions found.")
        return
    
    print(f"{'ID':<5} {'Date':<12} {'Amount':<12} {'Source':<15} {'Category':<15} {'Description'}")
    print("-" * 80)
    for t in transactions:
        print(f"{t[0]:<5} {t[5]:<12} {t[1]:<12.2f} {t[4] or 'N/A':<15} {t[3] or 'N/A':<15} {t[2]}")

def add_transaction(db: FinanceDB):
    print("\n=== Add New Transaction ===")
    try:
        amount = get_valid_amount()
        if amount is None:
            return
        
        description = input("Enter description: ").strip()
        category = input("Enter category (optional): ").strip() or None
        source = input("Enter source (optional): ").strip() or None
        date = get_valid_date()
        if date is None:
            return
        
        transaction_id = db.add_transaction(amount, description, category, source, date)
        print(f"Transaction added successfully with ID: {transaction_id}")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def view_transactions(db: FinanceDB):
    print("\n=== All Transactions ===")
    transactions = db.get_all_transactions()
    print_transaction_table(transactions)

def view_transaction_details(db: FinanceDB):
    try:
        transaction_id = int(input("Enter transaction ID: "))
        transaction = db.get_transaction(transaction_id)
        if transaction:
            print("\n=== Transaction Details ===")
            print(f"ID: {transaction[0]}")
            print(f"Amount: {transaction[1]:.2f}")
            print(f"Description: {transaction[2]}")
            print(f"Category: {transaction[3] or 'N/A'}")
            print(f"Source: {transaction[4] or 'N/A'}")
            print(f"Date: {transaction[5]}")
            print(f"Created at: {transaction[6]}")
        else:
            print("Transaction not found.")
    except ValueError:
        print("Please enter a valid transaction ID")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def update_transaction(db: FinanceDB):
    try:
        transaction_id = int(input("Enter transaction ID to update: "))
        transaction = db.get_transaction(transaction_id)
        if not transaction:
            print("Transaction not found.")
            return
        
        print("\n=== Update Transaction ===")
        amount = get_valid_amount()
        if amount is None:
            return
        
        description = input("Enter new description: ").strip()
        category = input("Enter new category (optional): ").strip() or None
        source = input("Enter new source (optional): ").strip() or None
        date = get_valid_date()
        if date is None:
            return
        
        if db.update_transaction(transaction_id, amount, description, category, source, date):
            print("Transaction updated successfully")
        else:
            print("Failed to update transaction")
    except ValueError:
        print("Please enter a valid transaction ID")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def delete_transaction(db: FinanceDB):
    try:
        transaction_id = int(input("Enter transaction ID to delete: "))
        if db.delete_transaction(transaction_id):
            print("Transaction deleted successfully")
        else:
            print("Transaction not found.")
    except ValueError:
        print("Please enter a valid transaction ID")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def view_balance(db: FinanceDB):
    balance = db.get_balance()
    print(f"\nCurrent Balance: {balance:.2f} VND")

def view_transactions_by_date_range(db: FinanceDB):
    print("\n=== View Transactions by Date Range ===")
    try:
        start_date = get_valid_date()
        if start_date is None:
            return
        end_date = get_valid_date()
        if end_date is None:
            return
        
        transactions = db.get_transactions_by_date_range(start_date, end_date)
        print_transaction_table(transactions)
        
        # Show summary
        total = sum(t[1] for t in transactions)
        print(f"\nTotal for period: {total:.2f} VND")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def view_category_summary(db: FinanceDB):
    print("\n=== Category Summary ===")
    try:
        print("Enter date range (optional):")
        start_date = input("Start date (YYYY-MM-DD) or press Enter for all time: ").strip()
        end_date = input("End date (YYYY-MM-DD) or press Enter for all time: ").strip()
        
        if not start_date or not end_date:
            start_date = None
            end_date = None
        
        summary = db.get_category_summary(start_date, end_date)
        if summary:
            print("\nCategory Summary:")
            for category, amount in summary.items():
                print(f"{category}: {amount:.2f} VND")
        else:
            print("No categories found.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def view_source_summary(db: FinanceDB):
    print("\n=== Source Summary ===")
    try:
        print("Enter date range (optional):")
        start_date = input("Start date (YYYY-MM-DD) or press Enter for all time: ").strip()
        end_date = input("End date (YYYY-MM-DD) or press Enter for all time: ").strip()
        
        if not start_date or not end_date:
            start_date = None
            end_date = None
        
        summary = db.get_source_summary(start_date, end_date)
        if summary:
            print("\nSource Summary:")
            for source, amount in summary.items():
                print(f"{source}: {amount:.2f} VND")
        else:
            print("No sources found.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def view_monthly_summary(db: FinanceDB):
    print("\n=== Monthly Summary ===")
    try:
        year = int(input("Enter year (YYYY): "))
        month = int(input("Enter month (1-12): "))
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        
        summary = db.get_monthly_summary(year, month)
        print(f"\nSummary for {year}-{month:02d}:")
        print(f"Total: {summary['total']:.2f} VND")
        print(f"Income: {summary['income']:.2f} VND")
        print(f"Expenses: {summary['expenses']:.2f} VND")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def export_transactions(db: FinanceDB):
    print("\n=== Export Transactions ===")
    try:
        print("Enter date range (optional):")
        start_date = input("Start date (YYYY-MM-DD) or press Enter for all time: ").strip()
        end_date = input("End date (YYYY-MM-DD) or press Enter for all time: ").strip()
        
        if not start_date or not end_date:
            start_date = None
            end_date = None
        
        transactions = db.export_transactions(start_date, end_date)
        
        # Export to JSON file
        filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
        
        print(f"\nTransactions exported to {filename}")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

def main():
    args = parse_args()
    db = FinanceDB()
    
    # Handle command-line mode
    if args.command:
        handle_cli_command(db, args)
        return
    
    # Interactive mode
    while True:
        try:
            print_menu()
            choice = input("Enter your choice (0-11): ").strip()
            
            if choice == "1":
                add_transaction(db)
            elif choice == "2":
                view_transactions(db)
            elif choice == "3":
                view_transaction_details(db)
            elif choice == "4":
                update_transaction(db)
            elif choice == "5":
                delete_transaction(db)
            elif choice == "6":
                view_balance(db)
            elif choice == "7":
                view_transactions_by_date_range(db)
            elif choice == "8":
                view_category_summary(db)
            elif choice == "9":
                view_source_summary(db)
            elif choice == "10":
                view_monthly_summary(db)
            elif choice == "11":
                export_transactions(db)
            elif choice == "0":
                print("Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            continue

if __name__ == "__main__":
    main() 