import streamlit as st
import pandas as pd
import json
import os
import sys
import importlib.util
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 核心环境设置 ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from core.data_engine import DataEngine
from core.backtest_engine import BacktestEngine
from core.base_strategy import BaseStrategy

# --- 页面配置 ---
st.set_page_config(
    page_title="Titan Quantum Terminal",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- 样式注入 (CSS) ---
st.markdown("""
<style>
    .metric-card {background-color: #1e222d; padding: 15px; border-radius: 10px; border-left: 5px solid #00bcd4;}
    .stButton>button {width: 100%; border-radius: 5px;}
    .report-table {font-size: 12px;}
</style>
""", unsafe_allow_html=True)

# --- 路径定义 ---
CONFIG_PATH = os.path.join(ROOT, 'config', 'config.json')
SECRETS_PATH = os.path.join(ROOT, 'config', 'secrets.json')
STRATEGY_DIR = os.path.join(ROOT, 'strategies')
os.makedirs(STRATEGY_DIR, exist_ok=True)

# --- 工具函数 ---
def load_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def load_strategies():
    """扫描策略文件"""
    files = [f for f in os.listdir(STRATEGY_DIR) if f.endswith('.py') and f not in ['__init__.py']]
    return files

def get_strategy_class(filename):
    """动态导入策略类"""
    path = os.path.join(STRATEGY_DIR, filename)
    spec = importlib.util.spec_from_file_location("dynamic_strategy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # 查找 BaseStrategy 的子类
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
            return obj
    return None

# ==========================================
#              侧边栏导航
# ==========================================
st.sidebar.title("⚡ Titan Quantum")
st.sidebar.caption("v6.0 Pro Edition")
nav = st.sidebar.radio("Modules", ["📈 市场监控 (Live)", "🧪 回测实验室 (Backtest)", "🧠 策略工坊 (AI Studio)", "⚙️ 系统配置 (Config)"])

# ==========================================
#              1. 市场监控
# ==========================================
if nav == "📈 市场监控 (Live)":
    st.title("📈 实盘与市场监控")
    
    # 读取状态
    status = load_json(os.path.join(ROOT, 'data', 'status.json'))
    
    # 顶部数据卡片
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前标的", "BTC/USDT")
    c2.metric("最新价格", f"${status.get('price', 0):,.2f}")
    c3.metric("ADX 动能", f"{status.get('adx', 0):.1f}")
    c4.metric("账户权益", f"${status.get('balance', '---')}")
    
    # 交互式图表
    st.subheader("实时行情")
    config = load_json(CONFIG_PATH)
    secrets = load_json(SECRETS_PATH)
    
    if st.button("🔄 刷新图表"):
        try:
            with st.spinner("连接交易所数据中..."):
                eng = DataEngine('view', config['exchanges']['binance_main'], secrets['exchanges']['binance_main'])
                df = eng.fetch_ohlcv(config['strategy']['symbol'], config['strategy']['timeframe'], limit=100)
                if df is not None:
                    fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='K线')])
                    fig.update_layout(template='plotly_dark', height=500, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"数据加载失败: {e}")

# ==========================================
#              2. 回测实验室
# ==========================================
elif nav == "🧪 回测实验室 (Backtest)":
    st.title("🧪 历史回测实验室")
    
    with st.container():
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            symbol = st.text_input("回测币种", "BTC/USDT")
            timeframe = st.selectbox("K线周期", ["15m", "1h", "4h", "1d"], index=1)
        with c2:
            balance = st.number_input("初始资金 (U)", 1000, 1000000, 10000)
            limit = st.slider("数据长度 (根)", 500, 5000, 1500)
        with c3:
            strategy_files = load_strategies()
            selected_strat = st.selectbox("选择策略", strategy_files)
    
    if st.button("🚀 启动回测引擎", type="primary"):
        if not selected_strat:
            st.warning("请先选择一个策略！")
        else:
            with st.status("回测进行中...", expanded=True) as status:
                # 1. 获取数据
                st.write("📡 正在从 Binance 拉取历史数据...")
                conf = load_json(CONFIG_PATH)
                sec = load_json(SECRETS_PATH)
                eng = DataEngine('backtest', conf['exchanges']['binance_main'], sec['exchanges']['binance_main'])
                df = eng.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                if df is not None:
                    # 2. 初始化策略
                    st.write("⚙️ 正在编译策略逻辑...")
                    StratClass = get_strategy_class(selected_strat)
                    # 从配置中读取参数传递给策略
                    strat_instance = StratClass(conf['strategy'])
                    
                    # 3. 运行引擎
                    st.write("⚡ 正在模拟逐笔交易...")
                    engine = BacktestEngine(initial_capital=balance)
                    result = engine.run(df, strat_instance)
                    
                    status.update(label="回测完成!", state="complete", expanded=False)
                    st.session_state['bt_result'] = result
                else:
                    status.update(label="数据获取失败", state="error")
    
    # 结果展示区
    if 'bt_result' in st.session_state:
        res = st.session_state['bt_result']
        if "error" in res:
            st.error(res['error'])
        else:
            st.divider()
            # 关键指标
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("总收益率", f"{res['total_return']:.2f}%", delta_color="normal")
            k2.metric("最大回撤", f"{res['max_drawdown']:.2f}%", delta_color="inverse")
            k3.metric("胜率", f"{res['win_rate']:.2f}%")
            k4.metric("盈亏比", f"{res['profit_factor']:.2f}")
            
            # 资金曲线图
            st.subheader("💸 资金权益曲线")
            equity_df = res['equity']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=equity_df['time'], y=equity_df['equity'], mode='lines', name='权益', line=dict(color='#00ff88')))
            fig.update_layout(template='plotly_dark', height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 交易列表
            st.subheader("📋 交易日志")
            st.dataframe(res['trades'], use_container_width=True)

# ==========================================
#              3. 策略工坊 (AI)
# ==========================================
elif nav == "🧠 策略工坊 (AI Studio)":
    st.title("🧠 AI 策略生成器")
    st.info("输入您的交易逻辑，AI 将自动编写符合 Titan 标准的 Python 策略代码。")
    
    col_input, col_code = st.columns([1, 1])
    
    with col_input:
        st.subheader("💡 描述您的策略")
        prompt_text = st.text_area("例如: 当 RSI(14) 小于 30 且价格突破布林带下轨时做多，止损 2%...", height=200)
        file_name = st.text_input("策略保存文件名", "my_new_strategy")
        
        if st.button("✨ 生成代码"):
            secrets = load_json(SECRETS_PATH)
            ai_conf = secrets.get('deepseek', {})
            
            if not ai_conf.get('apiKey'):
                st.error("请先在系统配置中填写 AI API Key！")
            else:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=ai_conf['apiKey'], base_url=ai_conf.get('base_url', 'https://api.deepseek.com'))
                    
                    system_prompt = """
                    你是一个量化交易Python专家。请编写一个继承自 `core.base_strategy.BaseStrategy` 的策略类。
                    要求:
                    1. 类名必须是 `Strategy`。
                    2. 实现 `add_indicators(self, df)`: 使用 pandas_ta 计算指标。
                    3. 实现 `on_bar(self, df, i)`: 返回 {'signal': 'LONG'/'SHORT', 'stop_loss': float, 'take_profit': float, 'reason': str}。
                    4. 不要包含 ```python 标记，只返回纯代码。
                    5. 导入路径: `from core.base_strategy import BaseStrategy`
                    """
                    
                    with st.spinner("AI 正在思考架构..."):
                        response = client.chat.completions.create(
                            model=ai_conf.get('model', 'deepseek-chat'),
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt_text}
                            ]
                        )
                        code = response.choices[0].message.content.strip().replace("```python", "").replace("```", "")
                        st.session_state['gen_code'] = code
                        st.success("代码生成完毕！")
                        
                except Exception as e:
                    st.error(f"AI 调用失败: {e}")

    with col_code:
        st.subheader("📝 代码预览")
        code_content = st.session_state.get('gen_code', "# 等待生成...")
        final_code = st.text_area("编辑器", code_content, height=400)
        
        if st.button("💾 保存到策略库"):
            if not file_name.endswith(".py"): file_name += ".py"
            full_path = os.path.join(STRATEGY_DIR, file_name)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(final_code)
            st.toast(f"策略已保存至 {full_path}")
            time.sleep(1)
            st.rerun()

# ==========================================
#              4. 系统配置
# ==========================================
elif nav == "⚙️ 系统配置 (Config)":
    st.title("⚙️ 全局参数配置")
    
    secrets = load_json(SECRETS_PATH)
    config = load_json(CONFIG_PATH)
    
    with st.form("config_form"):
        st.subheader("🤖 AI 模型配置")
        c1, c2, c3 = st.columns(3)
        ai_key = c1.text_input("API Key", value=secrets.get('deepseek', {}).get('apiKey', ''), type="password")
        ai_url = c2.text_input("Base URL", value=secrets.get('deepseek', {}).get('base_url', '[https://api.deepseek.com](https://api.deepseek.com)'))
        ai_model = c3.text_input("Model Name", value=secrets.get('deepseek', {}).get('model', 'deepseek-chat'))
        
        st.divider()
        st.subheader("🏦 交易所配置 (Binance)")
        ex_key = st.text_input("API Key", value=secrets['exchanges']['binance_main'].get('apiKey', ''), type="password")
        ex_sec = st.text_input("Secret Key", value=secrets['exchanges']['binance_main'].get('secret', ''), type="password")
        
        st.divider()
        st.subheader("🎮 策略默认参数")
        p1, p2 = st.columns(2)
        risk = p1.number_input("单笔风险 %", value=config['strategy'].get('risk_per_trade', 0.01))
        lev = p2.number_input("杠杆倍数", value=config['strategy'].get('leverage', 10))
        
        if st.form_submit_button("💾 保存设置"):
            # 更新 Secrets
            if 'deepseek' not in secrets: secrets['deepseek'] = {}
            secrets['deepseek']['apiKey'] = ai_key
            secrets['deepseek']['base_url'] = ai_url
            secrets['deepseek']['model'] = ai_model
            
            secrets['exchanges']['binance_main']['apiKey'] = ex_key
            secrets['exchanges']['binance_main']['secret'] = ex_sec
            
            # 更新 Config
            config['strategy']['risk_per_trade'] = risk
            config['strategy']['leverage'] = lev
            
            save_json(SECRETS_PATH, secrets)
            save_json(CONFIG_PATH, config)
            st.success("配置已更新！")
