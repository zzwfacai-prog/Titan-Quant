class StrategyEngine:
    @staticmethod
    def v5_5_high_freq(df, params):
        """
        v5.5 高频激进版 (High-Freq Aggressive)
        逻辑: ADX>15 + EMA趋势 + MACD金死叉
        """
        if df is None: return None

        last = df.iloc[-2] # 信号确认K线
        curr = df.iloc[-1] # 当前K线

        # 参数解包
        adx_th = params.get('adx_threshold', 15)
        sl_mult = params.get('sl_atr_mult', 2.0)
        tp_mult = params.get('tp_atr_mult', 8.0)

        # 逻辑判断
        adx_ok = last['adx'] > adx_th
        trend_long = last['close'] > last['ema50']
        trend_short = last['close'] < last['ema50']
        macd_bull = last['macd'] > last['macd_signal']
        macd_bear = last['macd'] < last['macd_signal']

        signal = None
        reason = f"ADX:{last['adx']:.1f}"

        if adx_ok and trend_long and macd_bull:
            signal = 'LONG'
            sl = curr['close'] - (last['atr'] * sl_mult)
            tp = curr['close'] + (last['atr'] * tp_mult)
            reason += " | 多头激进模式激活"
            
        elif adx_ok and trend_short and macd_bear:
            signal = 'SHORT'
            sl = curr['close'] + (last['atr'] * sl_mult)
            tp = curr['close'] - (last['atr'] * tp_mult)
            reason += " | 空头激进模式激活"

        return {
            "signal": signal,
            "entry_price": curr['close'],
            "stop_loss": sl if signal else 0,
            "take_profit": tp if signal else 0,
            "reason": reason
        }
