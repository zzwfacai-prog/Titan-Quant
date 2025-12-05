import time
import json
import os
import logging
from core.data_engine import DataEngine
from core.strategy_engine import StrategyEngine
from core.command_bridge import CommandBridge
from core.ai_guardian import AIGuardian

# 路径配置
ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(ROOT, 'logs', 'bot.log')
CONFIG_FILE = os.path.join(ROOT, 'config', 'config.json')
SECRETS_FILE = os.path.join(ROOT, 'config', 'secrets.json')
STATUS_FILE = os.path.join(ROOT, 'data', 'status.json')

# 确保目录存在
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)

# 日志配置
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def main():
    print("🚀 Titan-Quant Core Started.")
    logging.info("System Initialized")
    
    while True:
        try:
            # 1. 实时读取配置
            config = load_json(CONFIG_FILE)
            secrets = load_json(SECRETS_FILE)
            
            # 2. 响应前端指令
            cmd = CommandBridge.read_command()
            if cmd:
                print(f"⚡ 收到指令: {cmd['command']}")
                logging.info(f"Command: {cmd['command']}")
                # 实例化引擎处理平仓指令
                temp_eng = DataEngine('cmd', config['exchanges']['binance_main'], secrets['exchanges']['binance_main'])
                if cmd['command'] == "CLOSE_ALL":
                    msg = temp_eng.close_all(config['strategy']['symbol'])
                    logging.info(msg)

            # 3. 检查开关
            if not config['system']['is_running']:
                time.sleep(2)
                continue

            # 4. 执行策略
            ex_conf = config['exchanges']['binance_main']
            ex_sec = secrets['exchanges']['binance_main']
            symbol = config['strategy']['symbol']
            
            engine = DataEngine('binance', ex_conf, ex_sec)
            df = engine.fetch_ohlcv(symbol, config['strategy']['timeframe'])
            
            if df is None:
                print("获取行情失败...")
                time.sleep(5)
                continue
                
            res = StrategyEngine.analyze(df, config['strategy'])
            
            # 5. 更新状态文件
            status_data = {
                "price": res['indicators']['price'],
                "adx": res['indicators']['adx'],
                "signal": res['signal'],
                "reason": res['reason'],
                "balance": "API未配"
            }
            try:
                if ex_sec['apiKey']:
                    bal = engine.client.fetch_balance()['USDT']['free']
                    status_data['balance'] = round(bal, 2)
            except:
                pass
                
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(status_data, f)
            
            print(f"扫描完成: ADX={res['indicators']['adx']:.1f} | 信号: {res['signal']}")

            # 6. 信号触发
            if res['signal']:
                logging.info(f"SIGNAL FOUND: {res['signal']} @ {res['entry_price']}")
                
                # AI 过滤
                allow = True
                if config['strategy']['use_ai_filter']:
                    ai = AIGuardian(secrets['deepseek']['apiKey'])
                    ai_res = ai.review(df, res['signal'])
                    if not ai_res['approved']:
                        allow = False
                        logging.info(f"AI REJECTED: {ai_res['reason']}")
                
                if allow:
                    # engine.execute_order(...)
                    logging.info("执行开单逻辑 (Simulation Mode)")

            time.sleep(config['system']['check_interval'])

        except Exception as e:
            print(f"Main Loop Error: {e}")
            logging.error(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
