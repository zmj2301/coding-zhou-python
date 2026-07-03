"""
改进版爬虫 - 填写姓名开始考试
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    print("="*60)
    print("尝试填写姓名开始考试并爬取题目")
    print("="*60)

    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    print("正在启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)

    # 测试第一个试卷
    exam_url = "https://exam.xiaoxiangbc.com/#/exam/271"
    print(f"\n访问: {exam_url}")
    driver.get(exam_url)
    time.sleep(3)

    # 尝试填写姓名并开始考试
    try:
        # 查找姓名输入框
        print("查找姓名输入框...")
        name_input = driver.find_element(By.XPATH, '//input[@placeholder="姓名" or contains(@placeholder, "姓名")]')
        print("找到姓名输入框")
        name_input.send_keys("测试用户")
        print("已填写姓名")
        time.sleep(1)

        # 点击开始考试按钮
        button = driver.find_element(By.XPATH, '//button[contains(text(), "开始考试")]')
        button.click()
        print("已点击开始考试按钮")
        time.sleep(5)

        # 获取题目内容
        print("\n等待题目加载...")
        time.sleep(3)

        page_text = driver.find_element(By.TAG_NAME, 'body').text
        print(f"\n页面文本长度: {len(page_text)}")
        print("\n页面内容:")
        print("-"*60)
        print(page_text)
        print("-"*60)

        # 保存内容
        with open("试卷_带姓名.txt", "w", encoding="utf-8") as f:
            f.write("试卷: 2026年信息素养大赛Python复赛卷(一)\n")
            f.write("="*60 + "\n\n")
            f.write(page_text)

        print("\n✓ 已保存到: 试卷_带姓名.txt")

        # 如果成功,对所有试卷执行相同操作
        if len(page_text) > 200:  # 如果内容足够长,说明成功获取了题目
            print("\n✓ 成功获取题目!正在爬取所有试卷...")

            exams = [
                ("试卷1", "271"),
                ("试卷2", "263"),
                ("试卷3", "266"),
                ("试卷4", "272"),
                ("试卷5", "270"),
                ("试卷6", "262"),
                ("试卷7", "265"),
                ("试卷8", "267"),
                ("试卷9", "269"),
            ]

            all_content = []
            all_content.append("小象编程 - Python复赛模拟题汇总\n")
            all_content.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            all_content.append("="*60 + "\n\n")

            for exam_name, exam_id in exams:
                print(f"\n正在爬取: {exam_name}")
                url = f"https://exam.xiaoxiangbc.com/#/exam/{exam_id}"
                driver.get(url)
                time.sleep(3)

                try:
                    name_input = driver.find_element(By.XPATH, '//input[@placeholder="姓名" or contains(@placeholder, "姓名")]')
                    name_input.send_keys("测试用户")
                    time.sleep(1)

                    button = driver.find_element(By.XPATH, '//button[contains(text(), "开始考试")]')
                    button.click()
                    time.sleep(5)

                    page_text = driver.find_element(By.TAG_NAME, 'body').text

                    all_content.append(f"\n{'='*60}\n")
                    all_content.append(f"{exam_name}\n")
                    all_content.append(f"{'='*60}\n\n")
                    all_content.append(page_text + "\n")

                    # 保存单独文件
                    with open(f"{exam_name}_题目.txt", "w", encoding="utf-8") as f:
                        f.write(page_text)

                    print(f"✓ {exam_name} 完成")

                except Exception as e:
                    print(f"✗ {exam_name} 失败: {e}")

                time.sleep(2)

            # 保存汇总
            with open("所有试卷题目_完整版.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(all_content))

            print("\n" + "="*60)
            print("✓ 所有试卷已爬取完成!")
            print("✓ 已保存到: 所有试卷题目_完整版.txt")
            print("="*60)

    except Exception as e:
        print(f"\n尝试失败: {e}")
        print("\n这个网站可能需要登录才能查看题目")
        print("建议:")
        print("1. 如果你有账号,可以手动登录后使用浏览器扩展提取题目")
        print("2. 或者提供账号信息,我可以使用登录状态爬取")

    finally:
        driver.quit()
        print("\n浏览器已关闭")

if __name__ == "__main__":
    main()