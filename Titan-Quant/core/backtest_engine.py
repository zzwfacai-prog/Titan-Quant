import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core.base_strategy import BaseStrategy

class BacktestEngine:
    def __init__(self, initial_capital=10000, commission=0.0005):
        self.initial_capital = initial_capital
        self.commission = commission  # 手续费率 (默认万5)
        self.reset()

    def reset(self):
        self.balance = self.initial_capital
        self.equity_curve = []
        self.trades = []
        self.position = None  # None, 'LONG', 'SHORT'
        self.entry_price = 0
        self.sl = 0
        self.tp = 0
        self.trade_log = []

    def run(self, df: pd.DataFrame, strategy: BaseStrategy):
        self.reset()
        # 1. 预计算指标
        df = strategy.add_indicators(df.copy())
        
        # 2. 逐K线回测 (Bar-by-Bar)
        # 从第50根开始，给指标留出预热期
        for i in range(50, len(df)):
            current_bar = df.iloc[i]
            prev_bar = df.iloc[i-1]
            timestamp = current_bar['time']
            close_price = current_bar['close']
            
            # --- 记录权益 ---
            unrealized_pnl = 0
            if self.position == 'LONG':
                unrealized_pnl = (close_price - self.entry_price) / self.entry_price * self.balance
            elif self.position == 'SHORT':
                unrealized_pnl = (self.entry_price - close_price) / self.entry_price * self.balance
            
            self.equity_curve.append({
                'time': timestamp,
                'equity': self.balance + unrealized_pnl,
                'price': close_price
            })

            # --- 平仓逻辑 (止盈/止损) ---
            if self.position:
                exit_price = None
                pnl = 0
                reason = ""
                
                # 检查是否触发 SL/TP (使用 High/Low 模拟盘中触达)
                if self.position == 'LONG':
                    if current_bar['low'] <= self.sl:
                        exit_price = self.sl
                        reason = "Stop Loss"
                    elif current_bar['high'] >= self.tp:
                        exit_price = self.tp
                        reason = "Take Profit"
                elif self.position == 'SHORT':
                    if current_bar['high'] >= self.sl:
                        exit_price = self.sl
                        reason = "Stop Loss"
                    elif current_bar['low'] <= self.tp:
                        exit_price = self.tp
                        reason = "Take Profit"
                
                # 执行平仓
                if exit_price:
                    # 计算盈亏 (扣除双边手续费)
                    trade_pnl_pct = (exit_price - self.entry_price) / self.entry_price if self.position == 'LONG' else (self.entry_price - exit_price) / self.entry_price
                    fee_cost = self.commission * 2
                    realized_pnl = self.balance * (trade_pnl_pct - fee_cost)
                    
                    self.balance += realized_pnl
                    self.trades.append({
                        'entry_time': self.entry_time,
                        'exit_time': timestamp,
                        'side': self.position,
                        'entry_price': self.entry_price,
                        'exit_price': exit_price,
                        'pnl': realized_pnl,
                        'pnl_pct': trade_pnl_pct * 100,
                        'reason': reason
                    })
                    self.position = None

            # --- 开仓逻辑 ---
            if self.position is None:
                # 调用策略获取信号
                signal_data = strategy.on_bar(df, i)
                
                if signal_data['signal'] in ['LONG', 'SHORT']:
                    self.position = signal_data['signal']
                    self.entry_price = close_price
                    self.entry_time = timestamp
                    self.sl = signal_data['stop_loss']
                    self.tp = signal_data['take_profit']
        
        return self._generate_report()

    def _generate_report(self):
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        if trades_df.empty:
            return {"error": "无交易产生", "equity": equity_df, "trades": trades_df}

        # 核心指标计算
        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        win_rate = len(wins) / total_trades * 100
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['pnl'].mean()) if not losses.empty else 1
        profit_factor = avg_win / avg_loss
        
        total_return = (self.balance - self.initial_capital) / self.initial_capital * 100
        
        # 最大回撤计算
        equity_series = equity_df['equity']
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        return {
            "initial_capital": self.initial_capital,
            "final_balance": self.balance,
            "total_return": total_return,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "trades": trades_df,
            "equity": equity_df
        }
