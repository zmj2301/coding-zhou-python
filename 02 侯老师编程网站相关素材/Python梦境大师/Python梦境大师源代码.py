import requests
import base64
import os
import time
import json
import gradio as gr
from pathlib import Path

# 配置参数
TEXT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
IMAGE_API_URL = "https://api.siliconflow.cn/v1/images/generations"
API_TOKEN = "改成自己的key"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# 辅助函数：带重试的API请求
def make_api_request(url, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"API请求失败: {str(e)}")
            time.sleep(2 ** attempt)
    return None

# 梦境解析模块
def analyze_dream(keywords):
    """处理梦境解析并验证响应格式"""
    try:
        system_prompt = """你是一个梦境解析专家，请严格按以下JSON格式响应：
{
  "analysis": "心理学分析文本（不少于100字）",
  "emotions": ["主要情绪1", "次要情绪2"],
  "symbols": ["核心意象1", "核心意象2", "核心意象3"],
  "visual_prompt": {
    "style": "艺术风格（如：赛博朋克水墨风）",
    "color_palette": "主色号（如：#2E3192→#1BFFFF渐变）",
    "composition": "构图要求（如：中心对称布局）"
  }
}"""

        user_prompt = f"解析以下梦境关键词：{keywords}，需要包含至少三个视觉符号"

        payload = {
            "model": "Qwen/Qwen2.5-VL-32B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        result = make_api_request(TEXT_API_URL, payload)
        if not result:
            raise ValueError("API返回空响应")

        raw_content = result['choices'][0]['message']['content']
        
        # 严格验证JSON结构
        parsed = json.loads(raw_content)
        required_keys = ['analysis', 'emotions', 'symbols', 'visual_prompt']
        for key in required_keys:
            if key not in parsed:
                raise KeyError(f"缺少必要字段: {key}")

        if not isinstance(parsed['visual_prompt'], dict):
            raise TypeError("visual_prompt字段格式错误")

        return parsed

    except json.JSONDecodeError as e:
        error_msg = f"JSON解析失败: {str(e)}\n原始响应: {raw_content[:200]}..."
        raise RuntimeError(error_msg)
    except Exception as e:
        raise RuntimeError(f"梦境解析失败: {str(e)}")

# 图像生成模块
def generate_dream_image(prompt_data, reference_image=None):
    """生成梦境图像"""
    try:
        # 构建提示词
        prompt = f"""风格：{prompt_data['visual_prompt']['style']}
元素：{', '.join(prompt_data['symbols'][:3])}
色彩：{prompt_data['visual_prompt']['color_palette']}
构图：{prompt_data['visual_prompt'].get('composition', '自由构图')}"""

        payload = {
            "model": "Kwai-Kolors/Kolors",
            "prompt": prompt,
            "negative_prompt": "畸形, 比例失调, 模糊, 低质量",
            "image_size": "1024x1024",
            "num_inference_steps": 45,
            "guidance_scale": 7.5,
            "denoising_strength": 0.2
        }

        # 处理参考图
        if reference_image:
            if not reference_image.name.lower().endswith('.png'):
                raise ValueError("只支持PNG格式参考图")
            
            with open(reference_image.name, "rb") as f:
                if f.read(4) != b'\x89PNG':
                    raise ValueError("无效的PNG文件")
                f.seek(0)
                encoded_image = base64.b64encode(f.read()).decode('utf-8')
                payload["image"] = f"data:image/png;base64,{encoded_image}"

        # 调用API
        result = make_api_request(IMAGE_API_URL, payload)
        if not result or 'data' not in result:
            raise ValueError("无效的图像API响应")

        image_url = result['data'][0]['url']
        
        # 下载图像
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()

        output_path = Path(f"outputs/dream_{int(time.time())}.png")
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(2048):
                f.write(chunk)

        if os.path.getsize(output_path) < 1024:
            raise ValueError("生成图像文件过小")

        return str(output_path)

    except Exception as e:
        raise RuntimeError(f"图像生成失败: {str(e)}")

# Gradio界面
def dream_interpreter(keywords, reference_image=None):
    """主处理函数"""
    try:
        # 解析梦境
        analysis_result = analyze_dream(keywords)
        
        # 生成图像
        image_path = generate_dream_image(analysis_result, reference_image)
        
        # 格式化输出
        formatted_output = {
            "心理学分析": analysis_result['analysis'],
            "主要情绪": analysis_result['emotions'],
            "视觉元素": analysis_result['symbols'],
            "艺术风格": analysis_result['visual_prompt']['style']
        }
        
        return formatted_output, image_path

    except Exception as e:
        return {"错误信息": str(e)}, None

# 创建界面
interface = gr.Interface(
    fn=dream_interpreter,
    inputs=[
        gr.Textbox(label="🛌 输入梦境关键词", 
                 placeholder="例如：飞行 迷宫 蓝色...",
                 info="用空格分隔多个关键词"),
        gr.File(label="🎨 可选参考图（PNG格式）", 
              file_types=[".png"])
    ],
    outputs=[
        gr.JSON(label="📝 解析报告"),
        gr.Image(label="🖼️ 梦境可视化", type="filepath")
    ],
    title="🔮 AI梦境解析器",
    description="输入梦境关键词，获取心理学解析和AI生成的视觉化图像",
    allow_flagging="never"
)

# 启动应用
interface.launch()