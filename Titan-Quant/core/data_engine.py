import ccxt
import pandas as pd
import pandas_ta as ta

class DataEngine:
    def __init__(self, exchange_config):
        self.exchange_id = exchange_config['exchange']
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class(exchange_config)
    
    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            return df
        except Exception as e:
            print(f"[Data Error] {symbol}: {e}")
            return None

    def add_indicators(self, df):
        if df is None: return None
        try:
            # v5.5 核心指标
            df['adx'] = df.ta.adx(length=14)['ADX_14']
            df['ema50'] = df.ta.ema(length=50)
            macd = df.ta.macd(fast=12, slow=26, signal=9)
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['atr'] = df.ta.atr(length=14)
            return df
        except Exception as e:
            print(f"[Indicator Error]: {e}")
            return None
