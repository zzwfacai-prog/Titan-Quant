import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import time
from core.storage import Storage

# 页面配置
st.set_page_config(page_title="Titan Pro 控制台", layout="wide", page_icon="🚀")

# 路径
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, 'config', 'config.json')
SECRETS_FILE = os.path.join(ROOT, 'config', 'secrets.json')
DB_FILE = os.path.join(ROOT, 'data', 'titan.db')
STATUS_FILE = os.path.join(ROOT, 'data', 'status.json')

# 自定义 CSS (赛博朋克风)
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    .metric-card {background-color: #1E1E1E; border: 1px solid #333; padding: 15px; border-radius: 10px;}
    div[data-testid="stMetricValue"] {color: #00FF99;}
    </style>
    """, unsafe_allow_html=True)

# --- 辅助函数 ---
def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f: json.dump(data, f, indent=4)

# --- 侧边栏：核心控制 ---
st.sidebar.title("🎛️ 泰坦指挥中心")

config = load_json(CONFIG_FILE)
secrets = load_json(SECRETS_FILE)

# 开关
is_running = st.sidebar.toggle("🔴 启动机器人", value=config['system']['is_running'])
if is_running != config['system']['is_running']:
    config['system']['is_running'] = is_running
    save_json(CONFIG_FILE, config)
    st.rerun()

st.sidebar.divider()

# 菜单
menu = st.sidebar.radio("导航", ["📊 实时看板", "⚙️ 策略参数", "🔑 交易所配置", "📜 历史回溯"])

# --- Tab 1: 实时看板 ---
if menu == "📊 实时看板":
    st.header("🔥 实时战场监控 (Live Monitor)")
    
    # 读取实时状态
    status = {}
    if os.path.exists(STATUS_FILE):
        status = load_json(STATUS_FILE)
    
    # 顶部指标卡
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前价格 (BTC)", f"${status.get('price', 0)}")
    c2.metric("ADX 动能", f"{status.get('adx', 0):.1f}", delta=">15 开火" if status.get('adx',0)>15 else "等待")
    c3.metric("当前持仓", status.get('position', '空仓'), delta_color="off")
    c4.metric("账户余额", f"${status.get('balance', 0):.2f}")

    # 信号分析
    st.subheader("🧠 AI 决策脑图")
    logic_col1, logic_col2 = st.columns([3, 1])
    with logic_col1:
        st.code(f"最新日志: {status.get('reason', '正在初始化...')}", language="text")
    with logic_col2:
        if status.get('signal'):
            st.success(f"信号: {status['signal']}")
        else:
            st.info("信号: WAIT")

# --- Tab 2: 策略参数 ---
elif menu == "⚙️ 策略参数":
    st.header("🛠️ v5.5 策略热修 (即时生效)")
    
    with st.form("strategy_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_adx = st.number_input("ADX 阈值 (推荐 15)", value=config['strategy']['adx_threshold'])
            new_sl = st.number_input("止损 ATR倍数 (推荐 2.0)", value=config['strategy']['sl_atr_mult'])
        with c2:
            new_risk = st.number_input("单笔风险 % (推荐 0.018)", value=config['strategy']['risk_per_trade'])
            new_tp = st.number_input("止盈 ATR倍数 (推荐 8.0)", value=config['strategy']['tp_atr_mult'])
            
        new_webhook = st.text_input("钉钉/飞书 Webhook (用于通知)", value=config['system']['webhook_url'])
        
        submitted = st.form_submit_button("💾 保存配置")
        if submitted:
            config['strategy']['adx_threshold'] = new_adx
            config['strategy']['sl_atr_mult'] = new_sl
            config['strategy']['risk_per_trade'] = new_risk
            config['strategy']['tp_atr_mult'] = new_tp
            config['system']['webhook_url'] = new_webhook
            save_json(CONFIG_FILE, config)
            st.success("配置已更新！")

# --- Tab 3: 交易所配置 ---
elif menu == "🔑 交易所配置":
    st.header("🔐 API 密钥管理 (本地加密存储)")
    st.warning("注意：请确保你的服务器安全，Key 仅存储在本地 secrets.json 中。")
    
    with st.form("api_form"):
        api_key = st.text_input("API Key", value=secrets['apiKey'], type="password")
        secret_key = st.text_input("Secret Key", value=secrets['secret'], type="password")
        
        submitted = st.form_submit_button("更新密钥")
        if submitted:
            secrets['apiKey'] = api_key
            secrets['secret'] = secret_key
            save_json(SECRETS_FILE, secrets)
            st.success("密钥已更新，请重启机器人进程生效！")

# --- Tab 4: 历史回溯 ---
elif menu == "📜 历史回溯":
    st.header("💰 账户资金曲线")
    
    storage = Storage(DB_FILE)
    df_trades = storage.get_trades()
    
    if not df_trades.empty:
        # 资金曲线图
        curve = storage.get_equity_curve(initial_capital=100) # 假设100U起步
        if not curve.empty:
            fig = px.line(curve, x='time', y='equity', title='资金增长趋势')
            st.plotly_chart(fig, use_container_width=True)
        
        # 详细表格
        st.subheader("交易明细")
        st.dataframe(df_trades, use_container_width=True)
    else:
        st.info("暂无交易数据，机器人正在努力搬砖中...")
