# ⚡ Titan-Quant Extreme (v5.0)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red) ![Strategy](https://img.shields.io/badge/Strategy-v5.5-green) ![AI](https://img.shields.io/badge/AI-DeepSeek-purple)

**Titan-Quant Extreme** 是一套基于 Python 的全栈量化交易系统。它集成了 **交互式 K 线图表**、**Web 控制台**、**v5.5 高频激进策略** 以及 **DeepSeek AI 风险审计**，旨在为个人交易者提供机构级的自动化交易体验。

---

## 🌟 核心特性 (Key Features)

* **📊 赛博朋克控制台**: 基于 Streamlit 的暗黑风格 UI，支持手机/电脑端实时监控。
* **🧠 AI 风险审计**: 集成 **DeepSeek 大模型**，在开单前对技术信号进行宏观逻辑二次校验。
* **⚡ 指令桥接系统**: 前端按钮直接控制后端核心，支持“一键平仓”、“手动开单”等毫秒级响应。
* **📈 交互式图表**: 内置 Plotly K 线图，实时展示 EMA 趋势线与买卖点信号。
* **🛡️ 极致安全**: API 密钥采用本地独立加密存储 (`secrets.json`)，带登录密码锁，拒绝云端泄露。

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
确保已安装 Python 3.8 或以上版本。

```bash
# 1. 进入项目目录
cd Titan-Quant-Extreme

# 2. 安装依赖库
pip install -r requirements.txt
2. 初始化配置
首次运行建议先启动 UI 进行配置：

Bash

streamlit run web/dashboard.py
默认登录密码: admin

进入 "🔐 密钥管理" 页面，填入你的 Binance API Key 和 DeepSeek API Key。

进入 "⚙️ 策略配置" 页面，调整风险参数（默认已配置为 v5.5）。

3. 启动双进程
为了实现全自动交易，你需要同时运行 后端核心 和 前端面板。

Windows: 打开两个 CMD/PowerShell 窗口：

窗口 A: python main.py

窗口 B: streamlit run web/dashboard.py

Linux / Server (后台运行):

Bash

nohup python3 main.py > logs/bot.log 2>&1 &
nohup streamlit run web/dashboard.py --server.port 8501 > logs/ui.log 2>&1 &
🧠 策略详解：v5.5 High-Freq Aggressive
本系统默认搭载 "利润之王" v5.5 策略，专为小资金快速翻倍设计。

入场逻辑 (Entry)
动能过滤器: 1h_ADX > 15 (捕捉趋势启动的瞬间)。

趋势判定: 价格位于 1h_EMA50 之上做多，之下做空。

信号触发: MACD 金叉/死叉确认。

AI 终审: (可选) 将最近 5 小时数据发送给 DeepSeek，若 AI 认为趋势不可持续，则拦截信号。

出场逻辑 (Exit)
止损 (SL): 2.0 ATR (极窄止损，以小博大)。

止盈 (TP): 8.0 ATR (贪婪止盈，吃尽鱼身)。

风控: 严格遵守 1.8% 单笔风险，且满足交易所最小名义价值 (110U)。

📂 项目结构
Plaintext

Titan-Quant-Extreme/
├── config/              # 配置中心
│   ├── config.json      # 策略参数 (可热修)
│   └── secrets.json     # API 密钥 (本地加密)
├── core/                # 核心引擎
│   ├── ai_guardian.py   # AI 审计模块
│   ├── command_bridge.py# 前后端通信桥
│   ├── data_engine.py   # 数据与绘图
│   └── strategy_engine.py # v5.5 策略逻辑
├── web/                 # 前端界面
│   └── dashboard.py     # Streamlit 面板代码
├── logs/                # 运行日志
├── data/                # 实时状态缓存
├── main.py              # 后端主程序
└── requirements.txt     # 依赖清单
⚠️ 风险免责声明 (Disclaimer)
本软件仅供学习与辅助决策使用，不构成任何投资建议。

加密货币衍生品交易具有极高风险，可能导致本金全额损失。

请务必在实盘前使用 "回测实验室" 或小资金进行充分测试。

作者不对因软件故障、API 延迟或策略亏损导致的任何资金损失负责。

Made with ❤️ by Titan Quant Team
