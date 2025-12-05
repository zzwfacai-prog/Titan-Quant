import sqlite3
import pandas as pd
from datetime import datetime

class Storage:
    def __init__(self, db_path):
        self.db_path = db_path

    def log_trade(self, exchange, symbol, side, price, qty, reason, ai_score=0, pnl=0):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO trades (time, exchange, symbol, side, price, qty, pnl, ai_score, ai_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exchange, symbol, side, price, qty, pnl, ai_score, reason))
        conn.commit()
        conn.close()

    def get_trades(self):
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", conn)
        except:
            df = pd.DataFrame()
        conn.close()
        return df
