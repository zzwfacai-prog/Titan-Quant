import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

class DataEngine:
    def __init__(self, exchange_name, config, secrets):
        self.name = exchange_name
        self.type = config.get('type', 'ccxt')
        
        # 初始化交易所
        if self.type == 'ccxt':
            ex_id = config.get('id', 'binanceusdm')
            ex_class = getattr(ccxt, ex_id)
            
            # 处理无 Key 情况 (仅供查看行情)
            api_key = secrets.get('apiKey', '')
            secret = secrets.get('secret', '')
            
            self.client = ex_class({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        try:
            # 如果是公开数据，不需要签名
            bars = self.client.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            # 计算指标 v5.5
            df['adx'] = df.ta.adx(length=14)['ADX_14']
            df['ema50'] = df.ta.ema(length=50)
            df['atr'] = df.ta.atr(length=14)
            macd = df.ta.macd(fast=12, slow=26, signal=9)
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            
            return df
        except Exception as e:
            print(f"数据获取失败 [{self.name}]: {e}")
            return None

    def execute_order(self, symbol, side, qty, params={}):
        if not self.client.apiKey:
            print("❌ 无法下单: 未配置 API Key")
            return None
        try:
            return self.client.create_market_order(symbol, side, qty, params)
        except Exception as e:
            print(f"❌ 下单报错: {e}")
            return None

    def close_all(self, symbol):
        if not self.client.apiKey: return "无 Key"
        try:
            positions = self.client.fetch_positions([symbol])
            count = 0
            for p in positions:
                amt = float(p['contracts'])
                if amt > 0:
                    side = 'sell' if p['side'] == 'long' else 'buy'
                    self.client.create_market_order(symbol, side, amt)
                    count += 1
            return f"已平仓 {count} 单"
        except Exception as e:
            return f"平仓失败: {e}"

    @staticmethod
    def plot_chart(df, symbol):
        if df is None or df.empty: return None
        
        fig = go.Figure(data=[go.Candlestick(x=df['time'],
                        open=df['open'], high=df['high'],
                        low=df['low'], close=df['close'], name='Price')])
        
        fig.add_trace(go.Scatter(x=df['time'], y=df['ema50'], line=dict(color='#FFA500', width=1), name='EMA 50'))
        
        fig.update_layout(
            title=f'{symbol} Live (v5.5)',
            yaxis_title='Price',
            template='plotly_dark',
            height=450,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis_rangeslider_visible=False
        )
        return fig
