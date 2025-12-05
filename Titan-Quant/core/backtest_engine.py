import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_balance=10000, commission=0.0005):
        self.initial_balance = initial_balance
        self.commission = commission
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []

    def run(self, df, strategy_class, params):
        # 1. 初始化策略
        strategy = strategy_class(params)
        
        # 2. 计算指标 (一次性计算以加速)
        df = df.copy()
        strategy.add_indicators(df)
        
        # 3. 逐K线模拟
        in_position = False
        entry_price = 0
        direction = None
        sl = 0
        tp = 0
        
        for i in range(50, len(df)): # 前50根用于指标预热
            curr_bar = df.iloc[i]
            prev_bar = df.iloc[i-1]
            current_idx = df.index[i]
            
            # 记录资金曲线
            self.equity_curve.append({'time': curr_bar['time'], 'balance': self.balance})

            # --- 平仓逻辑 (止盈止损) ---
            if in_position:
                pnl = 0
                close_signal = False
                exit_price = curr_bar['close'] # 简化：以收盘价结算
                
                # 检查止损止盈
                if direction == 'LONG':
                    if curr_bar['low'] <= sl: 
                        exit_price = sl
                        close_signal = True
                        reason = "SL"
                    elif curr_bar['high'] >= tp:
                        exit_price = tp
                        close_signal = True
                        reason = "TP"
                elif direction == 'SHORT':
                    if curr_bar['high'] >= sl:
                        exit_price = sl
                        close_signal = True
                        reason = "SL"
                    elif curr_bar['low'] <= tp:
                        exit_price = tp
                        close_signal = True
                        reason = "TP"

                if close_signal:
                    # 计算盈亏
                    if direction == 'LONG':
                        pnl = (exit_price - entry_price) / entry_price * self.balance
                    else:
                        pnl = (entry_price - exit_price) / entry_price * self.balance
                    
                    # 扣除手续费 (开+平)
                    fee = self.balance * self.commission * 2
                    pnl -= fee
                    
                    self.balance += pnl
                    self.trades.append({
                        'entry_time': entry_time,
                        'exit_time': curr_bar['time'],
                        'side': direction,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl / (self.balance - pnl),
                        'reason': reason
                    })
                    in_position = False
                    direction = None

            # --- 开单逻辑 ---
            if not in_position:
                # 传入当前切片数据给策略
                # 注意：为了防未来函数，这里应该非常小心，简化起见我们传入截止当前的df
                # 实际策略中通常取 iloc[-1]
                temp_df = df.iloc[:i+1]
                res = strategy.on_bar(temp_df)
                
                if res and res['signal']:
                    direction = res['signal']
                    entry_price = curr_bar['close']
                    sl = res['stop_loss']
                    tp = res['take_profit']
                    entry_time = curr_bar['time']
                    in_position = True
        
        return self.generate_report()

    def generate_report(self):
        if not self.trades:
            return {"error": "无交易产生"}
            
        df_trades = pd.DataFrame(self.trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]
        
        total_trades = len(df_trades)
        win_rate = len(wins) / total_trades * 100
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['pnl'].mean()) if not losses.empty else 0
        wl_ratio = avg_win / avg_loss if avg_loss != 0 else 0
        
        max_drawdown = 0 # 需单独计算，此处简化
        
        return {
            "total_trades": total_trades,
            "final_balance": self.balance,
            "total_pnl": self.balance - self.initial_balance,
            "win_rate": win_rate,
            "wl_ratio": wl_ratio,
            "trades": df_trades,
            "equity": pd.DataFrame(self.equity_curve)
        }