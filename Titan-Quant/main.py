import time
import json
import os
import sys
from core.data_engine import DataEngine
from core.strategy_engine import StrategyEngine
from core.storage import Storage
from core.notifier import Notifier

# 路径
ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(ROOT, 'config', 'config.json')
SECRETS_FILE = os.path.join(ROOT, 'config', 'secrets.json')
DB_FILE = os.path.join(ROOT, 'data', 'titan.db')
STATUS_FILE = os.path.join(ROOT, 'data', 'status.json')

def main():
    print("🚀 Titan-Quant Pro 正在启动...")
    
    # 初始化
    storage = Storage(DB_FILE)
    
    while True:
        try:
            # 1. 读取配置 (支持热更新)
            with open(CONFIG_FILE, 'r') as f: config = json.load(f)
            with open(SECRETS_FILE, 'r') as f: secrets = json.load(f)
            
            # 通知模块
            notifier = Notifier(config['system']['webhook_url'])

            # 检查开关
            if not config['system']['is_running']:
                print("💤 机器人暂停中... (请在前端开启)")
                time.sleep(5)
                continue
                
            # 检查 Key
            if not secrets['apiKey']:
                print("⚠️ 未配置 API Key (请在前端配置)")
                time.sleep(5)
                continue

            # 初始化数据引擎
            data_eng = DataEngine(secrets['apiKey'], secrets['secret'])
            strat_conf = config['strategy']
            symbol = strat_conf['symbol']

            # 2. 获取数据
            df = data_eng.fetch_data(symbol, strat_conf['timeframe'])
            balance = data_eng.get_balance()
            
            # 3. 分析策略
            res = StrategyEngine.analyze(df, strat_conf)
            
            # 4. 更新前端状态
            status = {
                "price": res['indicators']['price'],
                "adx": res['indicators']['adx'],
                "signal": res['signal'],
                "reason": res['reason'],
                "balance": balance,
                "position": "检测中..." # 这里可以扩展读取真实持仓
            }
            with open(STATUS_FILE, 'w') as f:
                json.dump(status, f)

            # 5. 执行逻辑 (这里为了安全，先打印 Log，实盘时取消注释 execute)
            if res['signal']:
                msg = f"🔔 信号触发: {res['signal']} @ {res['entry_price']}\n理由: {res['reason']}"
                print(msg)
                notifier.send("信号触发", msg)
                
                # TODO: 在这里调用 execution_engine 下单
                # exec_eng.place_order(...) 
                # storage.log_trade(...)

            print(f"[{time.strftime('%H:%M:%S')}] 扫描完成. ADX={res['indicators']['adx']:.1f}")
            time.sleep(config['system']['check_interval'])

        except Exception as e:
            print(f"❌ 主循环错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
