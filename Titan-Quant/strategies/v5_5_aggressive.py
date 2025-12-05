from core.base_strategy import BaseStrategy
import pandas_ta as ta

class Strategy(BaseStrategy):
    def add_indicators(self, df):
        # 准商业级实现：使用 pandas_ta 批量计算
        # ADX
        adx = df.ta.adx(length=14)
        df['adx'] = adx['ADX_14']
        
        # EMA
        df['ema50'] = df.ta.ema(length=50)
        
        # MACD
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        
        # ATR
        df['atr'] = df.ta.atr(length=14)
        return df

    def on_bar(self, df, i):
        # 获取第 i 根K线的数据 (防未来函数)
        curr = df.iloc[i]
        prev = df.iloc[i-1] # 信号通常基于上一根收盘确认
        
        # 参数提取
        adx_thresh = self.params.get('adx_threshold', 15)
        sl_mult = self.params.get('sl_atr_mult', 2.0)
        tp_mult = self.params.get('tp_atr_mult', 8.0)
        
        signal = None
        sl = 0
        tp = 0
        reason = ""

        # 逻辑判断
        trend_long = prev['close'] > prev['ema50']
        trend_short = prev['close'] < prev['ema50']
        macd_bull = prev['macd'] > prev['macd_signal']
        macd_bear = prev['macd'] < prev['macd_signal']
        
        if prev['adx'] > adx_thresh:
            atr_val = prev['atr']
            
            if trend_long and macd_bull:
                signal = 'LONG'
                sl = curr['close'] - (atr_val * sl_mult)
                tp = curr['close'] + (atr_val * tp_mult)
                reason = f"ADX:{prev['adx']:.1f} | EMA+MACD Bull"
                
            elif trend_short and macd_bear:
                signal = 'SHORT'
                sl = curr['close'] + (atr_val * sl_mult)
                tp = curr['close'] - (atr_val * tp_mult)
                reason = f"ADX:{prev['adx']:.1f} | EMA+MACD Bear"
                
        return {
            "signal": signal,
            "stop_loss": sl,
            "take_profit": tp,
            "reason": reason
        }
