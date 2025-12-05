import json
import os
import time

# 确保路径兼容性
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_FILE = os.path.join(BASE_DIR, 'data', 'commands.json')

class CommandBridge:
    @staticmethod
    def send_command(cmd, params=None):
        data = {"command": cmd, "params": params or {}, "timestamp": time.time()}
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(CMD_FILE), exist_ok=True)
            with open(CMD_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"指令写入失败: {e}")

    @staticmethod
    def read_command():
        if not os.path.exists(CMD_FILE): return None
        try:
            with open(CMD_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            os.remove(CMD_FILE) # 读完即删
            return data
        except:
            return None
