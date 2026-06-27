import os
from openai import OpenAI

class AIAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('NVIDIA_API_KEY')
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置NVIDIA_API_KEY环境变量")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
    
    def chat(self, prompt, model="stepfun-ai/step-3.5-flash", temperature=1, top_p=0.9, max_tokens=16384, thinking_budget=None):
        extra_body = {}
        if thinking_budget:
            extra_body["thinking_budget"] = thinking_budget
        
        completion = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=False,
            extra_body=extra_body if extra_body else None
        )
        
        return completion.choices[0].message.content

    def chat_with_thinking(self, prompt, thinking_budget=2048):
        return self.chat(prompt, model="bytedance/seed-oss-36b-instruct", temperature=1.1, top_p=0.95, max_tokens=4096, thinking_budget=thinking_budget)

    def chat_fast(self, prompt):
        return self.chat(prompt, model="stepfun-ai/step-3.5-flash", temperature=1, top_p=0.9, max_tokens=16384)

if __name__ == "__main__":
    assistant = AIAssistant()
    print("=== 快速回答模式 ===")
    print(assistant.chat_fast("糖醋排骨咋做？"))
    print("\n=== 思考模式 ===")
    print(assistant.chat_with_thinking("糖醋排骨咋做？"))