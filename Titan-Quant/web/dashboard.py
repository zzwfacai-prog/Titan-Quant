import streamlit as st
import pandas as pd
import json
import os
import time
from core.data_engine import DataEngine
from core.command_bridge import CommandBridge

st.set_page_config(page_title="Titan Extreme", layout="wide", page_icon="⚡")

# 路径配置
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, 'config', 'config.json')
SECRETS_PATH = os.path.join(ROOT, 'config', 'secrets.json')
STATUS_PATH = os.path.join(ROOT, 'data', 'status.json')
LOG_PATH = os.path.join(ROOT, 'logs', 'bot.log')

# --- 辅助函数 ---
def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

# --- 登录逻辑 ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("## 🔒 Titan System Login")
    conf = load_json(CONFIG_PATH)
    pwd = st.text_input("请输入访问密码 (默认: admin)", type="password")
    if st.button("解锁控制台"):
        true_pwd = conf.get('system', {}).get('ui_password', 'admin')
        if pwd == true_pwd:
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("密码错误")
    st.stop()

# --- 主界面 ---
config = load_json(CONFIG_PATH)
secrets = load_json(SECRETS_PATH)

# 侧边栏
st.sidebar.title("🎮 Titan 控制台")
is_running = st.sidebar.toggle("🟢 机器人开关", value=config.get('system', {}).get('is_running', False))

if is_running != config.get('system', {}).get('is_running', False):
    config['system']['is_running'] = is_running
    save_json(CONFIG_PATH, config)
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("🛑 紧急平仓 (Panic Sell)", type="primary"):
    CommandBridge.send_command("CLOSE_ALL")
    st.toast("指令已下达：全仓平仓！")

# Tabs
t1, t2, t3, t4 = st.tabs(["📊 实时监控", "⚙️ 策略配置", "🔐 密钥管理", "📝 运行日志"])

# 1. 监控
with t1:
    status = load_json(STATUS_PATH)
    
    # 指标卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BTC 价格", f"${status.get('price', 0)}")
    col2.metric("ADX 动能", f"{status.get('adx', 0):.1f}", delta=">15 激活" if status.get('adx',0)>15 else "待机")
    col3.metric("当前信号", status.get('signal', 'WAIT'), delta_color="inverse")
    col4.metric("钱包余额", f"${status.get('balance', '---')}")
    
    st.info(f"🧠 系统分析: {status.get('reason', '正在初始化...')}")
    
    # 绘制图表
    try:
        ex_conf = config['exchanges']['binance_main']
        ex_sec = secrets['exchanges']['binance_main']
        eng = DataEngine('view', ex_conf, ex_sec)
        df = eng.fetch_ohlcv(config['strategy']['symbol'], config['strategy']['timeframe'])
        if df is not None:
            st.plotly_chart(DataEngine.plot_chart(df, config['strategy']['symbol']), use_container_width=True)
    except Exception as e:
        st.warning(f"图表加载失败 (可能是网络或Key问题): {e}")

# 2. 策略
with t2:
    st.subheader("v5.5 核心参数热修")
    with st.form("strat_form"):
        c1, c2 = st.columns(2)
        adx = c1.number_input("ADX 阈值", value=config['strategy']['adx_threshold'])
        sl = c2.number_input("止损 ATR倍数", value=config['strategy']['sl_atr_mult'])
        tp = c1.number_input("止盈 ATR倍数", value=config['strategy']['tp_atr_mult'])
        risk = c2.number_input("单笔风险 %", value=config['strategy']['risk_per_trade'])
        
        if st.form_submit_button("💾 保存配置"):
            config['strategy']['adx_threshold'] = adx
            config['strategy']['sl_atr_mult'] = sl
            config['strategy']['tp_atr_mult'] = tp
            config['strategy']['risk_per_trade'] = risk
            save_json(CONFIG_PATH, config)
            st.success("配置已更新")

# 3. 密钥
with t3:
    st.warning("⚠️ Key 将保存在本地 secrets.json 中，请勿泄露")
    with st.form("key_form"):
        ak = st.text_input("Binance API Key", value=secrets['exchanges']['binance_main'].get('apiKey', ''), type="password")
        sk = st.text_input("Binance Secret", value=secrets['exchanges']['binance_main'].get('secret', ''), type="password")
        dk = st.text_input("DeepSeek API Key", value=secrets['deepseek'].get('apiKey', ''), type="password")
        
        if st.form_submit_button("更新密钥库"):
            secrets['exchanges']['binance_main']['apiKey'] = ak
            secrets['exchanges']['binance_main']['secret'] = sk
            secrets['deepseek']['apiKey'] = dk
            save_json(SECRETS_PATH, secrets)
            st.success("密钥已安全保存")

# 4. 日志
with t4:
    if st.button("刷新日志"): st.rerun()
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-50:]
            st.code("".join(lines))
    else:
        st.info("日志文件尚未生成")
