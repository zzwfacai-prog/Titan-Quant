import sqlite3
import pandas as pd
from datetime import datetime

class Storage:
    def __init__(self, db_path):
        self.db_path = db_path

    def log_trade(self, symbol, side, price, qty, reason, pnl=0):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO trades (time, symbol, side, price, qty, pnl, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), symbol, side, price, qty, pnl, reason))
        conn.commit()
        conn.close()

    def get_trades(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", conn)
        conn.close()
        return df

    def get_equity_curve(self, initial_capital=100):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT time, pnl FROM trades", conn)
        conn.close()
        if df.empty: return pd.DataFrame()
        df['cumulative_pnl'] = df['pnl'].cumsum()
        df['equity'] = initial_capital + df['cumulative_pnl']
        return df
