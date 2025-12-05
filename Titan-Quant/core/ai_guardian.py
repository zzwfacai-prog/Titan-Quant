import json
from openai import OpenAI

class AIGuardian:
    def __init__(self, api_key, model="deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model
        
    def review(self, df, signal):
        # 无Key模式下自动放行
        if not self.client.api_key:
            return {"approved": True, "score": 0, "reason": "No AI Key, Auto Pass"}
            
        try:
            data_str = df.tail(5)[['time','close','adx','ema50']].to_string()
            prompt = f"Analyze crypto data:\n{data_str}\nSignal: {signal}\nFormat: JSON {{approved:bool, score:int, reason:str}}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {"approved": True, "score": 50, "reason": f"AI Error: {e}"}
