import ccxt
import pandas as pd
import pandas_ta as ta

class DataEngine:
    def __init__(self, api_key, secret, exchange_id='binanceusdm'):
        config = {
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        }
        self.exchange = getattr(ccxt, exchange_id)(config)

    def fetch_data(self, symbol, timeframe):
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            # 计算 v5.5 指标
            df['adx'] = df.ta.adx(length=14)['ADX_14']
            df['ema50'] = df.ta.ema(length=50)
            df['atr'] = df.ta.atr(length=14)
            macd = df.ta.macd(fast=12, slow=26, signal=9)
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            
            return df
        except Exception as e:
            print(f"Data Error: {e}")
            return None
    
    def get_balance(self):
        try:
            return self.exchange.fetch_balance()['USDT']['free']
        except:
            return 0
