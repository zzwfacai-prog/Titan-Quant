import time
import json
import os
from core.data_engine import DataEngine
from core.strategy_engine import StrategyEngine
from core.ai_guardian import AIGuardian
from core.storage import Storage
from core.notifier import Notifier

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def main():
    print("🚀 Titan-Quant Ultra (AI-Agent) 启动中...")
    
    config = load_json(os.path.join(ROOT, 'config/config.json'))
    secrets = load_json(os.path.join(ROOT, 'config/secrets.json'))
    
    storage = Storage(os.path.join(ROOT, 'data/titan.db'))
    notifier = Notifier(config['system']['webhook_url'])
    
    ai_agent = None
    if config['strategy']['use_ai_filter']:
        ai_agent = AIGuardian(secrets['deepseek']['apiKey'], secrets['deepseek']['model'])
        print("🤖 DeepSeek 风险官已就位")

    engines = {}
    for name, ex_conf in config['exchanges'].items():
        engines[name] = DataEngine(name, ex_conf, secrets['exchanges'][name])

    while True:
        try:
            config = load_json(os.path.join(ROOT, 'config/config.json'))
            if not config['system']['is_running']:
                time.sleep(5)
                continue

            for name, engine in engines.items():
                symbol = config['exchanges'][name]['symbol']
                df = engine.fetch_ohlcv(symbol, config['strategy']['timeframe'])
                if df is None: continue
                
                tech_res = StrategyEngine.analyze(df, config['strategy'])
                status_msg = f"[{name}] 扫描: {tech_res['reason']}"
                
                if tech_res['signal']:
                    print(f"🔔 {name} 技术信号: {tech_res['signal']}")
                    
                    if ai_agent:
                        print("🤖 AI 正在审计...")
                        ai_res = ai_agent.review_signal(df, tech_res)
                        if ai_res['approved']:
                            print(f"✅ AI 通过! 评分: {ai_res['score']}")
                            notifier.send(f"开单 ({name})", f"AI评分: {ai_res['score']}\n{ai_res['reason']}")
                            storage.log_trade(name, symbol, tech_res['signal'], tech_res['entry_price'], 0, ai_res['reason'], ai_res['score'])
                        else:
                            print(f"🛑 AI 驳回: {ai_res['reason']}")
                            status_msg = f"AI 驳回: {ai_res['reason']}"
                    else:
                        print("✅ 无AI模式，执行开单")
                        storage.log_trade(name, symbol, tech_res['signal'], tech_res['entry_price'], 0, tech_res['reason'])

                with open(os.path.join(ROOT, 'data/status.json'), 'w') as f:
                    json.dump({"last_log": status_msg}, f)

        except Exception as e:
            print(f"❌ 错误: {e}")
        
        time.sleep(config['system']['check_interval'])

if __name__ == "__main__":
    main()
