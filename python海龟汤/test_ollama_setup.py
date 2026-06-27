# 测试Ollama安装和运行状态
import subprocess
import sys

def test_ollama_setup():
    """
    测试Ollama是否安装并运行正常
    """
    try:
        print("1. 检查Ollama是否安装...")
        result = subprocess.run(
            [sys.executable, "-c", "from ollama import chat; print('Ollama库已安装')"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Ollama库已安装")
        else:
            print("❌ Ollama库未安装")
            print(f"错误信息：{result.stderr}")
            return False
        
        # 检查Ollama服务是否运行
        print("2. 检查Ollama服务是否运行...")
        result = subprocess.run(
            "ollama list",
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Ollama服务正在运行")
            print("可用模型：")
            print(result.stdout)
        else:
            print("❌ Ollama服务未运行")
            print(f"错误信息：{result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"测试失败：{str(e)}")
        return False

if __name__ == "__main__":
    test_ollama_setup()