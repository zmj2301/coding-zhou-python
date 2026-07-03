"""
单试卷测试脚本 - 爬取一个试卷的所有题目
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    print("="*60)
    print("单试卷测试 - 爬取Python复赛卷(一)的所有题目")
    print("="*60)
    
    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 使用无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问试卷页面
        url = "https://exam.xiaoxiangbc.com/#/exam/271"
        print(f"\n访问: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 填写姓名
        print("\n1. 填写姓名...")
        try:
            name_input = driver.find_element(By.XPATH, '//input[@placeholder="姓名" or contains(@placeholder, "姓名")]')
            name_input.send_keys("测试用户")
            print("✓ 已填写姓名: 测试用户")
            time.sleep(2)
        except Exception as e:
            print(f"✗ 填写姓名失败: {e}")
        
        # 点击开始考试
        print("\n2. 点击开始考试...")
        try:
            start_button = driver.find_element(By.XPATH, '//button[contains(text(), "开始考试")]')
            start_button.click()
            print("✓ 已点击开始考试")
            time.sleep(5)  # 等待题目加载
        except Exception as e:
            print(f"✗ 点击开始考试失败: {e}")
        
        # 检查页面内容
        print("\n3. 检查页面内容...")
        page_source = driver.page_source
        print(f"页面源码长度: {len(page_source)}")
        
        # 保存完整页面源码
        with open("test_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("✓ 已保存页面源码: test_page_source.html")
        
        # 查找题目相关元素
        print("\n4. 查找题目元素...")
        
        # 尝试查找题目容器
        question_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "question")]')
        print(f"找到 {len(question_elements)} 个题目容器元素")
        
        # 尝试查找题目编号
        question_numbers = driver.find_elements(By.XPATH, '//div[contains(text(), "单选题") or contains(text(), "多选题") or contains(text(), "填空题") or contains(text(), "编程题")]')
        print(f"找到 {len(question_numbers)} 个题目类型元素")
        
        # 尝试查找下一题按钮
        next_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "下一题")]')
        print(f"找到 {len(next_buttons)} 个'下一题'按钮")
        
        # 尝试查找答题卡
        answer_cards = driver.find_elements(By.XPATH, '//div[contains(text(), "答题卡")]')
        print(f"找到 {len(answer_cards)} 个答题卡元素")
        
        # 获取页面文本内容
        print("\n5. 获取当前页面文本...")
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # 保存页面文本
        with open("test_page_text.txt", "w", encoding="utf-8") as f:
            f.write("当前页面文本内容:\n")
            f.write("="*60 + "\n\n")
            f.write(page_text)
        print("✓ 已保存页面文本: test_page_text.txt")
        
        # 尝试遍历所有题目
        print("\n6. 尝试遍历题目...")
        
        all_questions = []
        all_questions.append(f"\n=== 第1题 ===\n{page_text}")
        
        # 查找进度信息
        try:
            progress = driver.find_element(By.XPATH, '//div[contains(text(), "进度")]')
            print(f"进度信息: {progress.text}")
            
            # 尝试点击下一题按钮
            for i in range(2, 15):  # 假设最多14题
                try:
                    print(f"\n尝试获取第{i}题...")
                    next_btn = driver.find_element(By.XPATH, '//button[contains(text(), "下一题")]')
                    next_btn.click()
                    time.sleep(2)
                    
                    current_text = driver.find_element(By.TAG_NAME, 'body').text
                    all_questions.append(f"\n=== 第{i}题 ===\n{current_text}")
                    print(f"✓ 已获取第{i}题")
                    
                except Exception as e:
                    print(f"✗ 无法继续获取第{i}题: {e}")
                    # 尝试其他方法 - 通过答题卡数字按钮
                    try:
                        print(f"尝试通过答题卡按钮获取第{i}题...")
                        # 查找数字按钮
                        number_buttons = driver.find_elements(By.XPATH, f'//button[text()="{i}"] | //div[text()="{i}"]')
                        
                        if number_buttons:
                            number_buttons[0].click()
                            time.sleep(2)
                            current_text = driver.find_element(By.TAG_NAME, 'body').text
                            all_questions.append(f"\n=== 第{i}题 ===\n{current_text}")
                            print(f"✓ 通过答题卡获取第{i}题")
                        else:
                            print(f"✗ 未找到第{i}题按钮")
                            break
                    except Exception as e2:
                        print(f"✗ 答题卡方法也失败: {e2}")
                        break
        except Exception as e:
            print(f"无法获取进度信息: {e}")
        
        # 保存所有题目
        print(f"\n共获取 {len(all_questions)} 个题目内容")
        with open("test_all_questions.txt", "w", encoding="utf-8") as f:
            f.write("测试试卷 - 所有题目内容\n")
            f.write("="*60 + "\n\n")
            f.write("\n".join(all_questions))
        print("✓ 已保存所有题目: test_all_questions.txt")
        
        # 截图
        driver.save_screenshot("test_screenshot.png")
        print("✓ 已保存截图: test_screenshot.png")
        
        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("✓ 浏览器已关闭")

if __name__ == "__main__":
    main()