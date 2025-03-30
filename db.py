import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

class FinanceDB:
    def __init__(self, db_name: str = "finance.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_transaction(self, amount: float, description: str, 
                       category: Optional[str] = None, 
                       source: Optional[str] = None,
                       date: Optional[str] = None) -> int:
        """Add a new transaction to the database"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (amount, description, category, source, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (amount, description, category, source, date))
            conn.commit()
            return cursor.lastrowid

    def get_transaction(self, transaction_id: int) -> Optional[Tuple]:
        """Retrieve a specific transaction by ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            return cursor.fetchone()

    def get_all_transactions(self) -> List[Tuple]:
        """Retrieve all transactions"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions ORDER BY date DESC')
            return cursor.fetchall()

    def update_transaction(self, transaction_id: int, amount: float, description: str, 
                         category: Optional[str] = None, 
                         source: Optional[str] = None,
                         date: Optional[str] = None) -> bool:
        """Update an existing transaction"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET amount = ?, description = ?, category = ?, source = ?, date = ?
                WHERE id = ?
            ''', (amount, description, category, source, date, transaction_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction by ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_balance(self) -> float:
        """Calculate current balance"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(amount) FROM transactions')
            return cursor.fetchone()[0] or 0.0

    def get_transactions_by_date_range(self, start_date: str, end_date: str) -> List[Tuple]:
        """Get transactions within a date range"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            return cursor.fetchall()

    def get_category_summary(self, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> Dict[str, float]:
        """Get summary of transactions by category"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = '''
                SELECT category, SUM(amount) 
                FROM transactions 
                WHERE category IS NOT NULL
            '''
            params = []
            if start_date and end_date:
                query += ' AND date BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            query += ' GROUP BY category'
            
            cursor.execute(query, params)
            return dict(cursor.fetchall())

    def get_source_summary(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Dict[str, float]:
        """Get summary of transactions by source"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = '''
                SELECT source, SUM(amount) 
                FROM transactions 
                WHERE source IS NOT NULL
            '''
            params = []
            if start_date and end_date:
                query += ' AND date BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            query += ' GROUP BY source'
            
            cursor.execute(query, params)
            return dict(cursor.fetchall())

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, float]:
        """Get summary for a specific month"""
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        transactions = self.get_transactions_by_date_range(start_date, end_date)
        summary = defaultdict(float)
        
        for t in transactions:
            summary['total'] += t[1]  # amount
            if t[1] > 0:
                summary['income'] += t[1]
            else:
                summary['expenses'] += abs(t[1])
        
        return dict(summary)

    def export_transactions(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> List[Dict]:
        """Export transactions to a list of dictionaries"""
        if start_date and end_date:
            transactions = self.get_transactions_by_date_range(start_date, end_date)
        else:
            transactions = self.get_all_transactions()
        
        return [
            {
                'id': t[0],
                'amount': t[1],
                'description': t[2],
                'category': t[3],
                'source': t[4],
                'date': t[5],
                'created_at': t[6]
            }
            for t in transactions
        ] 