import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Dict, defaultdict
import json
from pathlib import Path

class FinanceDB:
    def __init__(self, db_path: str = 'transactions.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_recurring BOOLEAN DEFAULT 0,
                    recurring_frequency TEXT,
                    next_date TEXT,
                    tags TEXT,
                    notes TEXT
                )
            ''')
            
            # Create budgets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    period TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    read BOOLEAN DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def add_transaction(self, amount: float, description: str, category: Optional[str] = None,
                       source: Optional[str] = None, date: Optional[str] = None,
                       is_recurring: bool = False, recurring_frequency: Optional[str] = None,
                       tags: Optional[List[str]] = None, notes: Optional[str] = None) -> int:
        """Add a new transaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate next date for recurring transactions
            next_date = None
            if is_recurring and recurring_frequency:
                next_date = self._calculate_next_date(date or datetime.now().strftime('%Y-%m-%d'),
                                                    recurring_frequency)
            
            cursor.execute('''
                INSERT INTO transactions (
                    amount, description, category, source, date, created_at,
                    is_recurring, recurring_frequency, next_date, tags, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                amount, description, category, source,
                date or datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                is_recurring, recurring_frequency, next_date,
                json.dumps(tags) if tags else None,
                notes
            ))
            
            return cursor.lastrowid
    
    def _calculate_next_date(self, current_date: str, frequency: str) -> str:
        """Calculate the next date for a recurring transaction"""
        current = datetime.strptime(current_date, '%Y-%m-%d')
        
        if frequency == 'daily':
            next_date = current.replace(day=current.day + 1)
        elif frequency == 'weekly':
            next_date = current.replace(day=current.day + 7)
        elif frequency == 'monthly':
            if current.month == 12:
                next_date = current.replace(year=current.year + 1, month=1)
            else:
                next_date = current.replace(month=current.month + 1)
        elif frequency == 'yearly':
            next_date = current.replace(year=current.year + 1)
        else:
            raise ValueError(f"Invalid frequency: {frequency}")
        
        return next_date.strftime('%Y-%m-%d')
    
    def get_transaction(self, transaction_id: int) -> Optional[Tuple]:
        """Get a transaction by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            
            if row:
                # Convert tags from JSON string to list
                row = list(row)
                if row[10]:  # tags column
                    row[10] = json.loads(row[10])
                return tuple(row)
            return None
    
    def get_all_transactions(self) -> List[Tuple]:
        """Get all transactions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions ORDER BY date DESC')
            rows = cursor.fetchall()
            
            # Convert tags from JSON string to list for each row
            for i, row in enumerate(rows):
                row = list(row)
                if row[10]:  # tags column
                    row[10] = json.loads(row[10])
                rows[i] = tuple(row)
            
            return rows
    
    def get_transactions_by_date_range(self, start_date: str, end_date: str) -> List[Tuple]:
        """Get transactions within a date range"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            rows = cursor.fetchall()
            
            # Convert tags from JSON string to list for each row
            for i, row in enumerate(rows):
                row = list(row)
                if row[10]:  # tags column
                    row[10] = json.loads(row[10])
                rows[i] = tuple(row)
            
            return rows
    
    def search_transactions(self, query: str) -> List[Tuple]:
        """Search transactions by description, category, or source"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE description LIKE ? OR category LIKE ? OR source LIKE ?
                ORDER BY date DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            rows = cursor.fetchall()
            
            # Convert tags from JSON string to list for each row
            for i, row in enumerate(rows):
                row = list(row)
                if row[10]:  # tags column
                    row[10] = json.loads(row[10])
                rows[i] = tuple(row)
            
            return rows
    
    def update_transaction(self, transaction_id: int, amount: Optional[float] = None,
                         description: Optional[str] = None, category: Optional[str] = None,
                         source: Optional[str] = None, date: Optional[str] = None,
                         is_recurring: Optional[bool] = None,
                         recurring_frequency: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         notes: Optional[str] = None) -> bool:
        """Update a transaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            updates = []
            values = []
            
            if amount is not None:
                updates.append('amount = ?')
                values.append(amount)
            if description is not None:
                updates.append('description = ?')
                values.append(description)
            if category is not None:
                updates.append('category = ?')
                values.append(category)
            if source is not None:
                updates.append('source = ?')
                values.append(source)
            if date is not None:
                updates.append('date = ?')
                values.append(date)
            if is_recurring is not None:
                updates.append('is_recurring = ?')
                values.append(is_recurring)
            if recurring_frequency is not None:
                updates.append('recurring_frequency = ?')
                values.append(recurring_frequency)
            if tags is not None:
                updates.append('tags = ?')
                values.append(json.dumps(tags))
            if notes is not None:
                updates.append('notes = ?')
                values.append(notes)
            
            if not updates:
                return False
            
            # Add transaction_id to values
            values.append(transaction_id)
            
            query = f'''
                UPDATE transactions 
                SET {', '.join(updates)}
                WHERE id = ?
            '''
            
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            return cursor.rowcount > 0
    
    def get_balance(self) -> float:
        """Calculate current balance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(amount) FROM transactions')
            return cursor.fetchone()[0] or 0.0
    
    def get_category_summary(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, float]:
        """Get summary of transactions by category"""
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        transactions = self.get_all_transactions()
        if start_date and end_date:
            transactions = self.get_transactions_by_date_range(start_date, end_date)
        
        return [{
            'id': t[0],
            'amount': t[1],
            'description': t[2],
            'category': t[3],
            'source': t[4],
            'date': t[5],
            'created_at': t[6],
            'is_recurring': bool(t[7]),
            'recurring_frequency': t[8],
            'next_date': t[9],
            'tags': t[10],
            'notes': t[11]
        } for t in transactions]
    
    def add_budget(self, category: str, amount: float, period: str,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> int:
        """Add a new budget"""
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts
                SET read = 1
                WHERE id = ?
            ''', (alert_id,))
            return cursor.rowcount > 0 