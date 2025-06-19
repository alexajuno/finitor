import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Dict, defaultdict
import json
from pathlib import Path
from .models import Transaction

class FinanceDB:
    def __init__(self, db_name: str = "finance.db"):
        self.db_name = db_name
        self.default_currency = "VND"
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create transactions table with currency support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    date DATE NOT NULL,
                    currency TEXT DEFAULT 'VND',
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    tags TEXT
                )
            ''')
            
            # Check if currency column exists, add it if not
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'currency' not in columns:
                cursor.execute('ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT "VND"')
            
            # Create currencies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS currencies (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    exchange_rate DECIMAL(10,6) NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default currency if it doesn't exist
            cursor.execute('SELECT code FROM currencies WHERE code = ?', (self.default_currency,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO currencies (code, name, exchange_rate)
                    VALUES (?, ?, ?)
                ''', (self.default_currency, "Vietnamese Dong", 1.0))
            
            conn.commit()
    
    def add_transaction(self, amount: float, description: str, 
                       category: Optional[str] = None, 
                       source: Optional[str] = None,
                       date: Optional[str] = None,
                       currency: Optional[str] = None) -> int:
        """Add a new transaction to the database"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if currency is None:
            currency = self.default_currency
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (amount, description, category, source, date, currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ''', (amount, description, category, source, date, currency))
            conn.commit()
            return cursor.lastrowid
    
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get a transaction by ID"""
        with sqlite3.connect(self.db_name) as conn:
            # Use named access for columns to avoid index mismatches
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, amount, description, category, source, date, currency, created_at, tags '
                'FROM transactions WHERE id = ?', (transaction_id,)
            )
            row = cursor.fetchone()
            if row:
                tags_str = row['tags']
                tags = json.loads(tags_str) if tags_str else []
                # Validate currency code; fall back to default if unrecognized
                raw_currency = row['currency']
                if raw_currency and self.get_currency(raw_currency):
                    currency_code = raw_currency
                else:
                    currency_code = self.default_currency
                return Transaction(
                    id=row['id'], amount=row['amount'], description=row['description'],
                    category=row['category'], source=row['source'], date=row['date'],
                    currency=currency_code, created_at=row['created_at'], tags=tags
                )
            return None
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        with sqlite3.connect(self.db_name) as conn:
            # Use named access to avoid index mismatches
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, amount, description, category, source, date, currency, created_at, tags '
                'FROM transactions ORDER BY date DESC'
            )
            rows = cursor.fetchall()
            transactions: List[Transaction] = []
            for row in rows:
                tags_str = row['tags']
                tags = json.loads(tags_str) if tags_str else []
                transactions.append(Transaction(
                    id=row['id'], amount=row['amount'], description=row['description'],
                    date=row['date'], currency=row['currency'], created_at=row['created_at'],
                    category=row['category'], source=row['source'], tags=tags
                ))
            return transactions
    
    def get_transactions_by_date_range(self, start_date: str, end_date: str) -> List[Transaction]:
        """Get transactions within a date range"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, amount, description, category, source, date, currency, created_at, tags
                   FROM transactions
                   WHERE date BETWEEN ? AND ?
                   ORDER BY date DESC''', (start_date, end_date)
            )
            rows = cursor.fetchall()
            transactions: List[Transaction] = []
            for row in rows:
                tags_str = row['tags']
                tags = json.loads(tags_str) if tags_str else []
                transactions.append(Transaction(
                    id=row['id'], amount=row['amount'], description=row['description'],
                    date=row['date'], currency=row['currency'], created_at=row['created_at'],
                    category=row['category'], source=row['source'], tags=tags
                ))
            return transactions
    
    def search_transactions(self, query: str) -> List[Transaction]:
        """Search transactions by description, category, or source"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, amount, description, category, source, date, currency, created_at, tags
                   FROM transactions
                   WHERE description LIKE ? OR category LIKE ? OR source LIKE ?
                   ORDER BY date DESC''',
                (f'%{query}%', f'%{query}%', f'%{query}%')
            )
            rows = cursor.fetchall()
            transactions: List[Transaction] = []
            for row in rows:
                tags_str = row['tags']
                tags = json.loads(tags_str) if tags_str else []
                transactions.append(Transaction(
                    id=row['id'], amount=row['amount'], description=row['description'],
                    date=row['date'], currency=row['currency'], created_at=row['created_at'],
                    category=row['category'], source=row['source'], tags=tags
                ))
            return transactions
    
    def update_transaction(self, transaction_id: int, amount: float, description: str, 
                         category: Optional[str] = None, 
                         source: Optional[str] = None,
                         date: Optional[str] = None,
                         currency: Optional[str] = None) -> bool:
        """Update an existing transaction"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        # Get existing transaction to preserve currency if not provided
        if currency is None:
            existing = self.get_transaction(transaction_id)
            if existing:
                currency = existing.currency
            else:
                currency = self.default_currency
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET amount = ?, description = ?, category = ?, source = ?, date = ?, currency = ?
                WHERE id = ?
            ''', (amount, description, category, source, date, currency, transaction_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            return cursor.rowcount > 0
    
    def get_balance(self, currency: Optional[str] = None) -> float:
        """
        Calculate current balance
        
        If currency is specified, convert all transactions to that currency
        Otherwise, use the default currency
        """
        if currency is None:
            currency = self.default_currency
            
        with sqlite3.connect(self.db_name) as conn:
            conn.create_function("convert_currency", 3, self._convert_currency_func)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(convert_currency(amount, currency, ?)) 
                FROM transactions
            ''', (currency,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0.0
    
    def _convert_currency_func(self, amount: float, from_currency: str, to_currency: str = None) -> float:
        """Helper function for SQLite to convert between currencies"""
        if to_currency is None:
            to_currency = self.default_currency
            
        if from_currency == to_currency:
            return amount
            
        # Get exchange rates
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT exchange_rate FROM currencies WHERE code = ?', (from_currency,))
            from_rate = cursor.fetchone()
            
            cursor.execute('SELECT exchange_rate FROM currencies WHERE code = ?', (to_currency,))
            to_rate = cursor.fetchone()
            
            if from_rate and to_rate:
                # Convert amount to target currency
                return amount * (to_rate[0] / from_rate[0])
            else:
                # If currency not found, return original amount
                return amount
                
    def add_currency(self, code: str, name: str, exchange_rate: float) -> bool:
        """
        Add or update a currency
        
        Parameters:
        code (str): The currency code (e.g., USD, EUR)
        name (str): The currency name
        exchange_rate (float): Exchange rate relative to the base currency
        
        Returns:
        bool: True if successful
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO currencies (code, name, exchange_rate, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (code, name, exchange_rate))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_currencies(self) -> List[Dict]:
        """Get all available currencies"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM currencies ORDER BY code')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_currency(self, code: str) -> Optional[Dict]:
        """Get a specific currency by code"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM currencies WHERE code = ?', (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_category_summary(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, float]:
        """Get summary of transactions by category"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT category, SUM(amount) FROM transactions'
            params = []
            
            if start_date and end_date:
                query += ' WHERE date BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            
            query += ' GROUP BY category'
            
            cursor.execute(query, params)
            return {row[0] or 'Uncategorized': row[1] for row in cursor.fetchall()}
    
    def get_source_summary(self, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict[str, float]:
        """Get summary of transactions by source"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT source, SUM(amount) FROM transactions'
            params = []
            
            if start_date and end_date:
                query += ' WHERE date BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            
            query += ' GROUP BY source'
            
            cursor.execute(query, params)
            return {row[0] or 'Unspecified': row[1] for row in cursor.fetchall()}
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, float]:
        """Get monthly summary of transactions"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Get total
            cursor.execute('''
                SELECT SUM(amount) FROM transactions
                WHERE strftime('%Y-%m', date) = ?
            ''', (f'{year:04d}-{month:02d}',))
            total = cursor.fetchone()[0] or 0.0
            
            # Get income
            cursor.execute('''
                SELECT SUM(amount) FROM transactions
                WHERE strftime('%Y-%m', date) = ? AND amount > 0
            ''', (f'{year:04d}-{month:02d}',))
            income = cursor.fetchone()[0] or 0.0
            
            # Get expenses
            cursor.execute('''
                SELECT SUM(amount) FROM transactions
                WHERE strftime('%Y-%m', date) = ? AND amount < 0
            ''', (f'{year:04d}-{month:02d}',))
            expenses = cursor.fetchone()[0] or 0.0
            
            return {
                'total': total,
                'income': income,
                'expenses': expenses
            }
    
    def export_transactions(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> List[Dict]:
        """Export transactions to a list of dictionaries"""
        if start_date and end_date:
            transactions = self.get_transactions_by_date_range(start_date, end_date)
        else:
            transactions = self.get_all_transactions()
        
        return [
            {
                'id': t.id,
                'amount': t.amount,
                'description': t.description,
                'category': t.category,
                'source': t.source,
                'date': t.date,
                'currency': t.currency,
                'created_at': t.created_at
            }
            for t in transactions
        ]
    
    def add_budget(self, category: str, amount: float, period: str,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> int:
        """Add a new budget"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO budgets (
                    category, amount, period, start_date, end_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                category, amount, period,
                start_date or datetime.now().strftime('%Y-%m-%d'),
                end_date,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            return cursor.lastrowid
    
    def check_budget_alerts(self) -> List[Tuple]:
        """Check for budget alerts"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Get current month's transactions by category
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE strftime('%Y-%m', date) = ?
                GROUP BY category
            ''', (current_month,))
            
            category_totals = {row[0] or 'Uncategorized': row[1] for row in cursor.fetchall()}
            
            # Get active budgets
            cursor.execute('''
                SELECT category, amount, period
                FROM budgets
                WHERE end_date IS NULL OR end_date >= ?
            ''', (datetime.now().strftime('%Y-%m-%d'),))
            
            alerts = []
            for category, budget_amount, period in cursor.fetchall():
                if category in category_totals:
                    total = category_totals[category]
                    if abs(total) >= budget_amount:
                        alerts.append((
                            'budget',
                            category,
                            f"Budget limit of {budget_amount} reached for {category} ({total})"
                        ))
            
            return alerts
    
    def add_alert(self, alert_type: str, message: str) -> int:
        """Add a new alert"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (type, message, created_at)
                VALUES (?, ?, ?)
            ''', (
                alert_type,
                message,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            return cursor.lastrowid
    
    def get_unread_alerts(self) -> List[Tuple]:
        """Get all unread alerts"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, type, message, created_at
                FROM alerts
                WHERE read = 0
                ORDER BY created_at DESC
            ''')
            return cursor.fetchall()
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """Mark an alert as read"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts
                SET read = 1
                WHERE id = ?
            ''', (alert_id,))
            return cursor.rowcount > 0 