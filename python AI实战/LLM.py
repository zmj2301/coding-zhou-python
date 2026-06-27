
# 创建一个 hello.txt 文件,内容是 "hello world"
from ast import Break
import os

def get_answer(question):
    # 调用AI模型获取回答
    try:

        from openai import OpenAI

        # 直接用 OpenAI 格式调用智谱 AI
        client = OpenAI(
            api_key=os.environ.get('ZHIPUAI_API_KEY', ''),  # 去 https://open.bigmodel.cn 申请
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )

        response = client.chat.completions.create(
            model="GLM-4-Flash",  # 免费模型，速度快
            messages=question
        )

        reply = response.choices[0].message.content


        return reply
    except FileNotFoundError as e:
        messagebox.showerror("错误", f"未找到SKILL.md文件: {e}")
        exit(1)
    except Exception as e:
        return f"\n\nAI回答获取失败: {str(e)}"

try:
    skillmd = open("SKILL.md", "r", encoding="utf-8").read()
except FileNotFoundError as e:
    messagebox.showerror("错误", f"未找到SKILL.md文件: {e}")
    skillmd = ""

messages = [{"role": "system", "content": """你的目标是完成用户的任务，你必须选择下面的其中一种格式进行回答：
            1.如果你认为需要执行命令，则输出'命令:XXX',xxx为命令本身，不要用任何的格式，不要解释
            2.如果你认为不需要执行命令，则输出'完成:XXX',xxx为你总结的信息"""+skillmd}]



while True:
    user_input = input("\n你：")
    messages.append({"role": "user", "content": user_input})

    print("\n-------------------------Agent 循环开始-------------------------")

    while True:
        answer = get_answer(messages)
        messages.append({"role": "assistant", "content": answer})
        print(f"[Agent] {answer}")
        
        # 提取实际的回答内容，去除"AI回答:"前缀
        actual_answer = answer.strip()
        
        if actual_answer.startswith("完成:"):
            print("\n-------------------------Agent 循环结束-------------------------")
            print(f"[Agent] {actual_answer.split('完成:')[1].strip()}")
            break

        if actual_answer.startswith("命令:"):
            command = actual_answer.split("命令:")[1].strip()
            # 检查是否是创建文件的命令，如果是则使用Python文件操作
            if "echo" in command and ">" in command:
                # 提取文件名和内容
                parts = command.split(">")
                if len(parts) == 2:
                    content_part = parts[0].replace("echo", "").strip()
                    # 去除引号
                    if content_part.startswith('"') and content_part.endswith('"'):
                        content_part = content_part[1:-1]
                    elif content_part.startswith("'") and content_part.endswith("'"):
                        content_part = content_part[1:-1]
                    file_name = parts[1].strip()
                    # 使用Python文件操作创建文件，确保UTF-8编码
                    try:
                        with open(file_name, 'w', encoding='utf-8') as f:
                            f.write(content_part)
                        command_result = f"成功创建文件 {file_name}"
                    except Exception as e:
                        command_result = f"创建文件失败: {str(e)}"
                else:
                    command_result = "命令格式错误"
            else:
                command_result = os.popen(command).read()
            
            content = f"执行完毕 {command_result}"
            print(f"[Agent] {content}")
            messages.append({"role": "assistant", "content": content})
        else:
            print("[Agent] 无法识别的响应格式", actual_answer)
            break