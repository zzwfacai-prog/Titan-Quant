import streamlit as st
import pandas as pd
import json
import os
import sys
import importlib.util
import plotly.graph_objects as go
from datetime import datetime

# 添加项目根目录到路径，以便导入 core
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from core.data_engine import DataEngine
from core.backtest_engine import BacktestEngine
from core.command_bridge import CommandBridge

# 页面配置
st.set_page_config(page_title="Titan Quantum AI", layout="wide", page_icon="⚡", initial_sidebar_state="expanded")

# 路径常量
CONFIG_PATH = os.path.join(ROOT, 'config', 'config.json')
SECRETS_PATH = os.path.join(ROOT, 'config', 'secrets.json')
STRATEGY_DIR = os.path.join(ROOT, 'strategies')
os.makedirs(STRATEGY_DIR, exist_ok=True)

# --- 工具函数 ---
def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def get_strategies():
    """扫描 strategies 文件夹下的所有策略文件"""
    files = [f for f in os.listdir(STRATEGY_DIR) if f.endswith('.py') and f != '__init__.py' and f != 'base_strategy.py']
    return files

def load_strategy_class(filename):
    """动态加载策略类"""
    path = os.path.join(STRATEGY_DIR, filename)
    spec = importlib.util.spec_from_file_location("StrategyModule", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # 假设策略类名统一为 Strategy 或文件中唯一的类
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if isinstance(attribute, type) and attribute_name != 'BaseStrategy':
             return attribute
    return None

# --- 侧边栏导航 ---
st.sidebar.markdown("## ⚡ Titan Quantum")
page = st.sidebar.radio("导航", ["📊 实盘监控", "🧪 回测实验室", "🧠 策略工坊", "⚙️ 系统设置"])

# --- 1. 实盘监控 ---
if page == "📊 实盘监控":
    st.title("📊 实盘交易监控")
    status = load_json(os.path.join(ROOT, 'data', 'status.json'))
    
    # 顶部指标
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前价格", f"${status.get('price', 0)}")
    c2.metric("最新信号", status.get('signal', 'WAIT'), delta=status.get('adx', 0))
    c3.metric("账户余额", f"${status.get('balance', '---')}")
    c4.metric("AI 审计", "PASS" if status.get('ai_score', 0) > 60 else "WAIT")

    # K线图
    st.markdown("### 市场走势")
    config = load_json(CONFIG_PATH)
    secrets = load_json(SECRETS_PATH)
    
    if st.button("🔄 刷新图表"):
        try:
            eng = DataEngine('view', config['exchanges']['binance_main'], secrets['exchanges']['binance_main'])
            df = eng.fetch_ohlcv(config['strategy']['symbol'], config['strategy']['timeframe'])
            if df is not None:
                fig = DataEngine.plot_chart(df, config['strategy']['symbol'])
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")

# --- 2. 回测实验室 ---
elif page == "🧪 回测实验室":
    st.title("🧪 历史回测实验室")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("参数配置")
        symbol = st.text_input("交易对", "BTC/USDT")
        timeframe = st.selectbox("周期", ["15m", "1h", "4h", "1d"], index=1)
        limit = st.slider("K线数量", 500, 5000, 1000)
        init_balance = st.number_input("初始资金", 1000, 100000, 10000)
        
        strat_files = get_strategies()
        selected_strat = st.selectbox("选择策略", strat_files)
        
        if st.button("🚀 开始回测", type="primary"):
            if not selected_strat:
                st.error("请先在策略工坊创建策略")
            else:
                with st.spinner("正在拉取数据并模拟交易..."):
                    # 1. 获取数据
                    config = load_json(CONFIG_PATH)
                    secrets = load_json(SECRETS_PATH)
                    eng = DataEngine('backtest', config['exchanges']['binance_main'], secrets['exchanges']['binance_main'])
                    df = eng.fetch_ohlcv(symbol, timeframe, limit=limit)
                    
                    if df is not None:
                        # 2. 加载策略
                        StratClass = load_strategy_class(selected_strat)
                        # 3. 运行回测
                        bt = BacktestEngine(initial_balance=init_balance)
                        res = bt.run(df, StratClass, config['strategy'])
                        
                        st.session_state['bt_res'] = res
                    else:
                        st.error("无法获取历史数据")

    with col2:
        if 'bt_res' in st.session_state:
            res = st.session_state['bt_res']
            if "error" in res:
                st.warning(res['error'])
            else:
                # 展示结果
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("总交易次数", res['total_trades'])
                m2.metric("最终权益", f"${res['final_balance']:.2f}", delta=f"{res['total_pnl']:.2f}")
                m3.metric("胜率", f"{res['win_rate']:.2f}%")
                m4.metric("盈亏比", f"{res['wl_ratio']:.2f}")
                
                # 资金曲线
                st.subheader("资金曲线")
                if not res['equity'].empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=res['equity']['time'], y=res['equity']['balance'], mode='lines', name='Balance'))
                    st.plotly_chart(fig, use_container_width=True)
                
                # 交易列表
                st.subheader("交易明细")
                st.dataframe(res['trades'])

# --- 3. 策略工坊 (AI 生成) ---
elif page == "🧠 策略工坊":
    st.title("🧠 AI 策略生成器")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("在这里输入你的想法，AI 将自动为你编写 Python 策略代码。")
        prompt = st.text_area("描述你的策略逻辑 (例如: 当RSI低于30且价格突破布林带下轨时做多)", height=150)
        strat_name = st.text_input("策略文件名 (英文)", "my_new_strategy")
        
        if st.button("✨ 生成策略代码"):
            secrets = load_json(SECRETS_PATH)
            api_key = secrets['deepseek'].get('apiKey')
            base_url = secrets['deepseek'].get('base_url', 'https://api.deepseek.com')
            model = secrets['deepseek'].get('model', 'deepseek-chat')
            
            if not api_key:
                st.error("请先在设置中配置 DeepSeek API Key")
            else:
                with st.spinner("AI 正在思考并编写代码..."):
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key, base_url=base_url)
                        
                        sys_prompt = """
                        你是一个量化交易Python专家。请基于用户的描述编写一个策略类。
                        要求:
                        1. 必须继承自 BaseStrategy (虽然不需要显式导入，假设环境已有)。
                        2. 必须包含 add_indicators(self, df) 方法，使用 df.ta (pandas_ta) 计算指标。
                        3. 必须包含 on_bar(self, df) 方法，返回字典 {'signal': 'LONG'/'SHORT', 'stop_loss': float, 'take_profit': float, 'reason': str}。
                        4. 仅输出 Python 代码，不要Markdown标记。
                        """
                        
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        code = response.choices[0].message.content.replace("```python", "").replace("```", "")
                        st.session_state['gen_code'] = code
                    except Exception as e:
                        st.error(f"生成失败: {e}")

    with c2:
        code_content = st.session_state.get('gen_code', "# 等待生成...")
        new_code = st.text_area("代码预览 (可手动修改)", code_content, height=400)
        
        if st.button("💾 保存到策略库"):
            if not strat_name.endswith(".py"): strat_name += ".py"
            save_path = os.path.join(STRATEGY_DIR, strat_name)
            
            # 添加必要的头文件
            final_code = "from strategies.base_strategy import BaseStrategy\nimport pandas_ta as ta\n\n" + new_code
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(final_code)
            st.success(f"策略已保存至 {save_path}")

# --- 4. 系统设置 ---
elif page == "⚙️ 系统设置":
    st.title("⚙️ 全局配置")
    
    secrets = load_json(SECRETS_PATH)
    config = load_json(CONFIG_PATH)
    
    with st.form("settings_form"):
        st.subheader("🤖 AI 模型配置")
        c1, c2, c3 = st.columns(3)
        ai_key = c1.text_input("API Key", value=secrets.get('deepseek', {}).get('apiKey', ''), type="password")
        ai_url = c2.text_input("Base URL", value=secrets.get('deepseek', {}).get('base_url', 'https://api.deepseek.com'))
        ai_model = c3.text_input("Model Name", value=secrets.get('deepseek', {}).get('model', 'deepseek-chat'))
        
        st.divider()
        st.subheader("🏦 交易所配置")
        ex_key = st.text_input("Binance API Key", value=secrets['exchanges']['binance_main'].get('apiKey', ''), type="password")
        ex_sec = st.text_input("Binance Secret", value=secrets['exchanges']['binance_main'].get('secret', ''), type="password")
        
        if st.form_submit_button("💾 保存所有设置"):
            # 更新 Secrets
            if 'deepseek' not in secrets: secrets['deepseek'] = {}
            secrets['deepseek']['apiKey'] = ai_key
            secrets['deepseek']['base_url'] = ai_url
            secrets['deepseek']['model'] = ai_model
            
            secrets['exchanges']['binance_main']['apiKey'] = ex_key
            secrets['exchanges']['binance_main']['secret'] = ex_sec
            
            save_json(SECRETS_PATH, secrets)
            st.success("配置已保存，请重启系统生效！")
