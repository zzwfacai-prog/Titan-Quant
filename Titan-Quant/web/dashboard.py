import streamlit as st
import json
import os
import pandas as pd
import time

st.set_page_config(page_title="Titan v5.5 控制台", layout="wide", page_icon="⚡")

# 路径处理
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config', 'pairs.json')
STATUS_PATH = os.path.join(ROOT_DIR, 'logs', 'status.json')

st.title("⚡ Titan Quant: v5.5 High-Freq Aggressive")

# --- 侧边栏 ---
st.sidebar.header("🕹️ 总控开关")

# 读取配置
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
else:
    st.error("配置文件未找到")
    st.stop()

# 开关
is_running = st.sidebar.toggle("启动机器人", value=config.get('is_running', False))
if is_running != config.get('is_running'):
    config['is_running'] = is_running
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🛠️ 策略参数热修")
new_adx = st.sidebar.number_input("ADX 阈值", value=config.get('adx_threshold', 15))
new_sl = st.sidebar.number_input("止损 ATR", value=config.get('sl_atr_mult', 2.0))
new_tp = st.sidebar.number_input("止盈 ATR", value=config.get('tp_atr_mult', 8.0))

if st.sidebar.button("保存参数"):
    config['adx_threshold'] = new_adx
    config['sl_atr_mult'] = new_sl
    config['tp_atr_mult'] = new_tp
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)
    st.success("参数已保存！")

# --- 主面板 ---
col1, col2, col3 = st.columns(3)

# 读取实时状态
status = {}
if os.path.exists(STATUS_PATH):
    try:
        with open(STATUS_PATH, 'r') as f:
            status = json.load(f)
    except:
        pass

current_price = status.get('price', 0)
adx_val = status.get('adx', 0)
signal_val = status.get('signal', 'WAIT')

col1.metric("当前价格 (BTC)", f"${current_price}")
col2.metric("ADX 强度", f"{adx_val:.2f}", delta="> 15 开火" if adx_val > 15 else "等待")
col3.metric("当前信号", signal_val, delta_color="off" if signal_val=='WAIT' else "normal")

st.info(f"💡 最新分析逻辑: {status.get('reason', '正在初始化...')}")

st.divider()
st.caption("提示: 请确保在 config/exchanges.json 中配置了正确的 API Key 并在后台运行了 main.py")
