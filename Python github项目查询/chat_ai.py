import os
import time


class AIAssistant:
    from openai import OpenAI
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('NVIDIA_API_KEY')
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置NVIDIA_API_KEY环境变量")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            timeout=60.0
        )
        self.max_retries = 3
        self.retry_delay = 2
    
    def chat(self, prompt, model="stepfun-ai/step-3.5-flash", temperature=1, top_p=0.9, max_tokens=16384, thinking_budget=0):
        extra_body = {"thinking_budget": thinking_budget} if thinking_budget else None
        
        for attempt in range(self.max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=False,
                    extra_body=extra_body,
                    timeout=60.0
                )
                return completion.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API连接失败，{self.retry_delay}秒后重试... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    raise e

    def chat_with_thinking(self, prompt, thinking_budget=2048):
        return self.chat(prompt, model="bytedance/seed-oss-36b-instruct", temperature=1.1, top_p=0.95, max_tokens=4096, thinking_budget=thinking_budget)

    def deepseek_chat(self, prompt):
        return self.chat(prompt, model="deepseek/deepseek-3.2")

    def qwen_chat(self, prompt):
        return self.chat(prompt, model="qwen/qwen3-coder-480b-a35b-instruct")

    def chat_fast(self, prompt):
        return self.chat(prompt)

