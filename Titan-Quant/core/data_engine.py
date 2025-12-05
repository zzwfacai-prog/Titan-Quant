import ccxt
import pandas as pd
import pandas_ta as ta
import requests

class DataEngine:
    def __init__(self, exchange_name, config, secrets):
        self.name = exchange_name
        self.type = config.get('type', 'ccxt')
        
        if self.type == 'ccxt':
            ex_id = config.get('id', 'binanceusdm')
            ex_class = getattr(ccxt, ex_id)
            self.client = ex_class({
                'apiKey': secrets.get('apiKey'),
                'secret': secrets.get('secret'),
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        elif self.type == 'custom':
            self.api_url = config.get('api_url')
            self.api_key = secrets.get('apiKey')

    def fetch_ohlcv(self, symbol, timeframe):
        try:
            if self.type == 'ccxt':
                bars = self.client.fetch_ohlcv(symbol, timeframe, limit=100)
                df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            elif self.type == 'custom':
                # ASterdex 适配占位符
                print(f"[{self.name}] Custom API logic needed")
                return None

            if not df.empty:
                df['adx'] = df.ta.adx(length=14)['ADX_14']
                df['ema50'] = df.ta.ema(length=50)
                df['atr'] = df.ta.atr(length=14)
                macd = df.ta.macd(fast=12, slow=26, signal=9)
                df['macd'] = macd['MACD_12_26_9']
                df['macd_signal'] = macd['MACDs_12_26_9']
            
            return df

        except Exception as e:
            print(f"[{self.name}] Data Error: {e}")
            return None
