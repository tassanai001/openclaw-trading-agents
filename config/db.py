import sqlite3
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.init_tables()

    def init_tables(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cash REAL,
                total_value REAL,
                positions TEXT
            )
        ''')
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL,
                avg_price REAL,
                current_price REAL,
                unrealized_pnl REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL,
                price REAL,
                side TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                order_id TEXT
            )
        ''')
        
        # Scan results cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                result_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expiry DATETIME
            )
        ''')
        
        # Sentiment cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sentiment_score REAL,
                sentiment_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expiry DATETIME
            )
        ''')
        
        # Trading signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT,
                strength REAL,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_portfolio_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest portfolio state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cash, total_value, positions, timestamp 
            FROM portfolio_state 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'cash': row[0] or 0.0,
                'total_value': row[1] or 0.0,
                'positions': json.loads(row[2]) if row[2] else {},
                'timestamp': row[3] if row[3] else ''
            }
        return None

    def update_portfolio_state(self, cash: float, total_value: float, positions: Dict[str, Any]):
        """Update portfolio state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio_state (cash, total_value, positions)
            VALUES (?, ?, ?)
        ''', (cash, total_value, json.dumps(positions)))
        
        conn.commit()
        conn.close()

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, quantity, avg_price, current_price, unrealized_pnl, timestamp
            FROM positions
            WHERE quantity != 0
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        positions = []
        for row in rows:
            positions.append({
                'symbol': row[0] if row[0] else '',
                'quantity': row[1] if row[1] is not None else 0.0,
                'avg_price': row[2] if row[2] is not None else 0.0,
                'current_price': row[3] if row[3] is not None else 0.0,
                'unrealized_pnl': row[4] if row[4] is not None else 0.0,
                'timestamp': row[5] if row[5] else ''
            })
        
        return positions

    def add_position(self, symbol: str, quantity: float, avg_price: float, current_price: Optional[float] = None):
        """Add or update a position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if position already exists
        cursor.execute('''
            SELECT id FROM positions WHERE symbol = ?
        ''', (symbol,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing position
            cursor.execute('''
                UPDATE positions 
                SET quantity = ?, avg_price = ?, current_price = ?
                WHERE symbol = ?
            ''', (quantity or 0.0, avg_price or 0.0, current_price or 0.0, symbol))
        else:
            # Insert new position
            cursor.execute('''
                INSERT INTO positions (symbol, quantity, avg_price, current_price)
                VALUES (?, ?, ?, ?)
            ''', (symbol, quantity or 0.0, avg_price or 0.0, current_price or 0.0))
        
        conn.commit()
        conn.close()

    def update_position(self, symbol: str, quantity: Optional[float] = None, avg_price: Optional[float] = None, current_price: Optional[float] = None):
        """Update a position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        
        if avg_price is not None:
            updates.append("avg_price = ?")
            params.append(avg_price)
        
        if current_price is not None:
            updates.append("current_price = ?")
            params.append(current_price)
        
        if updates:
            params.append(symbol)
            query = f"UPDATE positions SET {', '.join(updates)} WHERE symbol = ?"
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()

    def add_trade(self, symbol: str, quantity: float, price: float, side: str, order_id: Optional[str] = None):
        """Add a trade record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (symbol, quantity, price, side, order_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, quantity or 0.0, price or 0.0, side or '', order_id))
        
        conn.commit()
        conn.close()

    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT symbol, quantity, price, side, timestamp, order_id
                FROM trades
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor.execute('''
                SELECT symbol, quantity, price, side, timestamp, order_id
                FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append({
                'symbol': row[0] if row[0] else '',
                'quantity': row[1] if row[1] is not None else 0.0,
                'price': row[2] if row[2] is not None else 0.0,
                'side': row[3] if row[3] else '',
                'timestamp': row[4] if row[4] else '',
                'order_id': row[5] if row[5] else ''
            })
        
        return trades

    def cache_scan_result(self, symbol: str, result_data: Any, expiry_minutes: int = 60):
        """Cache a scan result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expiry = datetime.now().replace(microsecond=0)
        expiry = expiry.timestamp() + (expiry_minutes * 60)
        
        cursor.execute('''
            INSERT INTO scan_results_cache (symbol, result_data, expiry)
            VALUES (?, ?, ?)
        ''', (symbol, json.dumps(result_data), expiry))
        
        conn.commit()
        conn.close()

    def cache_sentiment(self, symbol: str, sentiment_score: float, sentiment_text: str, expiry_minutes: int = 60):
        """Cache sentiment data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expiry = datetime.now().replace(microsecond=0)
        expiry = expiry.timestamp() + (expiry_minutes * 60)
        
        cursor.execute('''
            INSERT INTO sentiment_cache (symbol, sentiment_score, sentiment_text, expiry)
            VALUES (?, ?, ?, ?)
        ''', (symbol, sentiment_score, sentiment_text, expiry))
        
        conn.commit()
        conn.close()

    def get_latest_signals(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest trading signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT symbol, signal_type, strength, confidence, timestamp
                FROM trading_signals
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor.execute('''
                SELECT symbol, signal_type, strength, confidence, timestamp
                FROM trading_signals
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'symbol': row[0] if row[0] else '',
                'signal_type': row[1] if row[1] else '',
                'strength': row[2] if row[2] is not None else 0.0,
                'confidence': row[3] if row[3] is not None else 0.0,
                'timestamp': row[4] if row[4] else ''
            })
        
        return signals