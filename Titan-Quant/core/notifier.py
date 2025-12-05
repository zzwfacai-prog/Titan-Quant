import requests
import json
from datetime import datetime

class Notifier:
    def __init__(self, webhook_url):
        self.url = webhook_url

    def send(self, title, content):
        if not self.url: return
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"Titan: {title}",
                "text": f"### {title}\n\n{content}\n\n> Time: {datetime.now().strftime('%H:%M:%S')}"
            }
        }
        try:
            requests.post(self.url, json=data, timeout=5)
        except:
            pass
