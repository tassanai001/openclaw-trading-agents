"""Database Logger for Trading Agents"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class DBLogger:
    def __init__(self, db_path: str = "data/state.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL,
            action TEXT,
            result TEXT,
            error TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT,
            duration REAL,
            data TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def log_trade(self, agent: str, action: str, result: dict = None, error: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO trade_log (timestamp, agent, action, result, error)
        VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            agent,
            action,
            json.dumps(result) if result else None,
            error
        ))
        
        conn.commit()
        conn.close()
    
    def log_agent_run(self, agent_name: str, status: str, duration: float = None, data: dict = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO agent_runs (timestamp, agent_name, status, duration, data)
        VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            agent_name,
            status,
            duration,
            json.dumps(data) if data else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_trade_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trade_log")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_agent_runs(self, agent_name: str = None, limit: int = 10) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent_name:
            cursor.execute("""
            SELECT * FROM agent_runs 
            WHERE agent_name = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (agent_name, limit))
        else:
            cursor.execute("""
            SELECT * FROM agent_runs 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return rows

# Global instance
db_logger = DBLogger()
