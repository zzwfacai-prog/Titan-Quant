import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="Titan Ultra AI", layout="wide", page_icon="🤖")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, 'config/config.json')
SECRETS_PATH = os.path.join(ROOT, 'config/secrets.json')
STATUS_PATH = os.path.join(ROOT, 'data/status.json')

def load_data():
    with open(CONFIG_PATH) as f: c = json.load(f)
    with open(SECRETS_PATH) as f: s = json.load(f)
    return c, s

conf, sec = load_data()

st.title("🤖 Titan-Quant Ultra: AI 协同版")

# --- 侧边栏 ---
st.sidebar.header("🧠 AI 配置")
ai_enable = st.sidebar.toggle("启用 DeepSeek 审计", value=conf['strategy']['use_ai_filter'])
if ai_enable != conf['strategy']['use_ai_filter']:
    conf['strategy']['use_ai_filter'] = ai_enable
    with open(CONFIG_PATH, 'w') as f: json.dump(conf, f, indent=4)
    st.rerun()

st.sidebar.divider()
st.sidebar.info("当启用 AI 时，所有 Python 策略发现的信号都会发送给 DeepSeek 进行二次确认。")

# --- 主界面 ---
tabs = st.tabs(["📊 监控台", "🔗 交易所管理", "🔐 密钥保险箱"])

with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("策略引擎", "v5.5 High-Freq")
    c2.metric("AI 模型", "DeepSeek-Chat", "在线" if ai_enable else "离线")
    c3.metric("运行状态", "Running" if conf['system']['is_running'] else "Stopped")
    
    st.subheader("实时状态")
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH) as f: st.info(json.load(f).get('last_log', '无数据'))

with tabs[1]:
    st.subheader("交易所配置")
    st.json(conf['exchanges'])

with tabs[2]:
    st.subheader("配置 DeepSeek API")
    with st.form("ai_key"):
        dk = st.text_input("DeepSeek API Key", value=sec['deepseek']['apiKey'], type="password")
        if st.form_submit_button("更新 AI Key"):
            sec['deepseek']['apiKey'] = dk
            with open(SECRETS_PATH, 'w') as f: json.dump(sec, f, indent=4)
            st.success("已保存")
