# Finitor - Personal Finance Manager

A powerful command-line personal finance manager that helps you track your income and expenses with ease.

## Features

- 💰 Track income and expenses
- 📊 View detailed summaries and reports
- 📅 Filter transactions by date range
- 🏷️ Categorize transactions
- 👥 Track transaction sources
- 📈 Monthly and yearly summaries
- 📤 Export data to JSON
- 🎯 Budget tracking and alerts
- 🔍 Search transactions
- 📱 Mobile-friendly CLI interface
- 🔄 Recurring transactions
- 💳 Multiple currency support (coming soon)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/finitor.git
cd finitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Mode

Add a transaction:
```bash
python -m finitor add 1000 "Lunch" --category "Food" --source "Restaurant" --date "2024-03-30"
```

View transactions:
```bash
# View all transactions
python -m finitor view

# View specific transaction
python -m finitor view --id 1

# View transactions by date range
python -m finitor view --start-date "2024-03-01" --end-date "2024-03-31"

# View transactions for a specific date
python -m finitor view --date "2024-03-15"

# View transactions with full amount values
python -m finitor view --full-amounts
```

View summaries:
```bash
# Category summary
python -m finitor summary --type category

# Source summary
python -m finitor summary --type source

# Monthly summary
python -m finitor summary --month 3 --year 2024
```

View balance:
```bash
# View balance with shortened format (default)
python -m finitor balance

# View full balance without abbreviations
python -m finitor balance --full
```

Export transactions:
```bash
# Export to JSON (default)
python -m finitor export --start-date "2024-03-01" --end-date "2024-03-31"

# Export to CSV
python -m finitor export --start-date "2024-03-01" --end-date "2024-03-31" --format csv

# Export to Excel
python -m finitor export --start-date "2024-03-01" --end-date "2024-03-31" --format excel

# Export to HTML
python -m finitor export --start-date "2024-03-01" --end-date "2024-03-31" --format html

# Export a single day's transactions
python -m finitor export --date "2024-03-15" --format excel

# Export with full amount values
python -m finitor export --date "2024-03-15" --format csv --full-amounts
```

### Interactive Mode

Run the interactive CLI:
```bash
python -m finitor
```

In interactive mode:
- Use number keys to navigate menus
- Press Ctrl+C at any time to cancel current operation
- Press 'q' to quit from any submenu
- Use arrow keys for navigation (coming soon)

## Project Structure

```
finitor/
├── README.md
├── requirements.txt
├── setup.py
└── finitor/
    ├── __init__.py
    ├── cli/
    │   ├── __init__.py
    │   ├── commands.py
    │   ├── interactive.py
    │   └── utils.py
    ├── core/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── models.py
    │   └── services.py
    └── utils/
        ├── __init__.py
        ├── date.py
        ├── currency.py
        └── validators.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by personal finance tracking needs
- Built with Python and SQLite
- Uses Click for CLI interface
- Uses pandas for data manipulation and export
- Uses tabulate for formatted table output 