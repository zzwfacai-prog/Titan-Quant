class ExecutionEngine:
    def __init__(self, exchange_instance, symbol, leverage=20, risk_per_trade=0.018):
        self.ex = exchange_instance
        self.symbol = symbol
        self.leverage = leverage
        self.risk = risk_per_trade
        self.position_state = {
            "status": "idle",
            "side": None,
            "entry_price": 0,
            "stop_loss": 0,
            "take_profit": 0
        }

    def calc_size(self, balance, entry, sl):
        dist = abs(entry - sl)
        if dist == 0: return 0
        risk_amt = balance * self.risk
        qty = risk_amt / dist
        
        # v5.5 规则: 110U 最小名义价值修正
        if qty * entry < 110: qty = 110 / entry
        # 最大杠杆修正
        if qty * entry > balance * self.leverage: qty = (balance * self.leverage) / entry
        
        return self.ex.amount_to_precision(self.symbol, qty)

    def execute_signal(self, signal_dict):
        if self.position_state['status'] != 'idle':
            return 

        sig = signal_dict['signal']
        if not sig: return

        try:
            # 1. 设置杠杆
            try:
                self.ex.set_leverage(self.leverage, self.symbol)
            except:
                pass # 部分交易所可能不支持或是全仓模式
            
            # 2. 计算仓位
            bal = self.ex.fetch_balance()['USDT']['free']
            qty = self.calc_size(bal, signal_dict['entry_price'], signal_dict['stop_loss'])
            
            print(f"🚀 尝试开单: {sig} {qty}...")
            
            # 3. 市价开单
            side = 'buy' if sig == 'LONG' else 'sell'
            order = self.ex.create_market_order(self.symbol, side, float(qty))
            
            # 4. 挂止损止盈
            sl_price = signal_dict['stop_loss']
            tp_price = signal_dict['take_profit']
            opp_side = 'sell' if side == 'buy' else 'buy'
            
            self.ex.create_order(self.symbol, 'STOP_MARKET', opp_side, float(qty), params={'stopPrice': sl_price})
            self.ex.create_order(self.symbol, 'TAKE_PROFIT_MARKET', opp_side, float(qty), params={'stopPrice': tp_price})

            # 更新状态
            self.position_state = {
                "status": "in_position",
                "side": sig,
                "entry_price": signal_dict['entry_price'],
                "stop_loss": sl_price,
                "take_profit": tp_price
            }
            print(f"✅ 开单成功! SL:{sl_price} TP:{tp_price}")
            
        except Exception as e:
            print(f"❌ 下单异常: {e}")

    def sync_position(self):
        """同步链上持仓状态"""
        try:
            positions = self.ex.fetch_positions([self.symbol])
            active = [p for p in positions if float(p['contracts']) > 0]
            if not active:
                self.position_state['status'] = 'idle'
            else:
                p = active[0]
                self.position_state['status'] = 'in_position'
                self.position_state['side'] = 'LONG' if p['side'] == 'long' else 'SHORT'
                self.position_state['entry_price'] = float(p['entryPrice'])
        except Exception as e:
            print(f"同步失败: {e}")
