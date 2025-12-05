import json
import time
import threading
import os
from datetime import datetime
from core.data_engine import DataEngine
from core.strategy_engine import StrategyEngine
from core.execution_engine import ExecutionEngine

def load_config():
    with open(f'{os.path.dirname(__file__)}/config/exchanges.json') as f: ex_conf = json.load(f)
    with open(f'{os.path.dirname(__file__)}/config/pairs.json') as f: pair_conf = json.load(f)
    return ex_conf, pair_conf

def bot_loop(account_name, exchange_conf, pair_conf):
    print(f"🔥 线程启动: {account_name} | 策略: v5.5 High-Freq")
    
    data_eng = DataEngine(exchange_conf)
    exec_eng = ExecutionEngine(data_eng.exchange, pair_conf['symbol'], 
                               leverage=pair_conf['leverage'], 
                               risk_per_trade=pair_conf['risk_per_trade'])
    
    while True:
        try:
            # 动态重新加载配置 (支持前端热修参数)
            with open(f'{os.path.dirname(__file__)}/config/pairs.json') as f: 
                current_conf = json.load(f)
            
            if not current_conf.get('is_running', False):
                print(f"💤 {account_name}: 等待启动指令...")
                time.sleep(10)
                continue

            # 1. 同步持仓状态
            exec_eng.sync_position()
            
            # 如果有持仓，跳过分析 (v5.5 规则: 不加仓，死拿)
            if exec_eng.position_state['status'] != 'idle':
                print(f"🔒 {account_name} 持仓中，跳过信号扫描...")
                time.sleep(60)
                continue

            # 2. 获取数据
            df = data_eng.fetch_ohlcv(current_conf['symbol'], current_conf['timeframe'])
            df = data_eng.add_indicators(df)
            
            if df is None:
                time.sleep(10)
                continue

            # 3. 计算信号
            result = StrategyEngine.v5_5_high_freq(df, current_conf)
            
            # 4. 输出状态日志
            status = {
                "time": str(datetime.now()),
                "price": result['entry_price'],
                "adx": df.iloc[-2]['adx'],
                "signal": result['signal'],
                "reason": result['reason']
            }
            with open(f'{os.path.dirname(__file__)}/logs/status.json', 'w') as f:
                json.dump(status, f)

            # 5. 执行
            if result['signal']:
                print(f"🔔 信号触发: {result['signal']} | 原因: {result['reason']}")
                exec_eng.execute_signal(result)
            else:
                print(f"Scan: 无信号 (ADX={df.iloc[-2]['adx']:.1f})")

            time.sleep(60) # 每分钟检查一次

        except Exception as e:
            print(f"❌ 错误 {account_name}: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ex_configs, pair_configs = load_config()
    
    threads = []
    for name, conf in ex_configs.items():
        t = threading.Thread(target=bot_loop, args=(name, conf, pair_configs))
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
