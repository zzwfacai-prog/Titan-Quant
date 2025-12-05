class StrategyEngine:
    @staticmethod
    def analyze(df, params):
        if df is None or len(df) < 55: return None

        last = df.iloc[-2]
        curr = df.iloc[-1]

        adx_th = params.get('adx_threshold', 15)
        adx_val = last['adx']
        
        trend_long = last['close'] > last['ema50']
        trend_short = last['close'] < last['ema50']
        macd_bull = last['macd'] > last['macd_signal']
        macd_bear = last['macd'] < last['macd_signal']

        signal = None
        reason = f"ADX:{adx_val:.1f}"

        if adx_val > adx_th:
            if trend_long and macd_bull:
                signal = 'LONG'
                sl = curr['close'] - (last['atr'] * params['sl_atr_mult'])
                tp = curr['close'] + (last['atr'] * params['tp_atr_mult'])
                reason += " | Tech: Long Confirmed"
            elif trend_short and macd_bear:
                signal = 'SHORT'
                sl = curr['close'] + (last['atr'] * params['sl_atr_mult'])
                tp = curr['close'] - (last['atr'] * params['tp_atr_mult'])
                reason += " | Tech: Short Confirmed"
        
        return {
            "signal": signal,
            "entry_price": curr['close'],
            "stop_loss": sl if signal else 0,
            "take_profit": tp if signal else 0,
            "reason": reason,
            "indicators": {"adx": adx_val, "price": curr['close']}
        }
