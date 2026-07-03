"""
交互式考试题目爬虫
尝试点击按钮并获取题目
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def setup_driver():
    """设置Chrome WebDriver"""
    chrome_options = Options()
    # 不使用无头模式,以便观察
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--start-maximized')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_single_exam(driver, exam_url, exam_name):
    """爬取单个试卷"""
    print(f"\n正在访问: {exam_name}")
    driver.get(exam_url)
    time.sleep(3)

    # 尝试点击"开始考试"按钮
    try:
        print("查找'开始考试'按钮...")
        # 尝试多种方式查找按钮
        button_found = False

        # 方式1: 通过文本查找
        try:
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "开始考试")]'))
            )
            print("找到按钮(方式1)")
            button.click()
            button_found = True
            time.sleep(3)
        except:
            pass

        # 方式2: 通过class查找
        if not button_found:
            try:
                button = driver.find_element(By.CSS_SELECTOR, 'button')
                if "开始考试" in button.text:
                    print("找到按钮(方式2)")
                    button.click()
                    button_found = True
                    time.sleep(3)
            except:
                pass

        if not button_found:
            print("未找到'开始考试'按钮")

        # 获取页面内容
        time.sleep(5)  # 等待内容加载

        # 保存页面HTML
        html_file = f"{exam_name}_questions.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"页面HTML已保存: {html_file}")

        # 获取页面文本
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        text_file = f"{exam_name}_questions.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(page_text)
        print(f"页面文本已保存: {text_file}")

        # 截图
        screenshot_file = f"{exam_name}_screenshot.png"
        driver.save_screenshot(screenshot_file)
        print(f"截图已保存: {screenshot_file}")

        return page_text

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    # 获取试卷列表
    exam_urls = [
        ("试卷1", "https://exam.xiaoxiangbc.com/#/exam/271"),
        ("试卷2", "https://exam.xiaoxiangbc.com/#/exam/263"),
        ("试卷3", "https://exam.xiaoxiangbc.com/#/exam/266"),
        ("试卷4", "https://exam.xiaoxiangbc.com/#/exam/272"),
        ("试卷5", "https://exam.xiaoxiangbc.com/#/exam/270"),
        ("试卷6", "https://exam.xiaoxiangbc.com/#/exam/262"),
        ("试卷7", "https://exam.xiaoxiangbc.com/#/exam/265"),
        ("试卷8", "https://exam.xiaoxiangbc.com/#/exam/267"),
        ("试卷9", "https://exam.xiaoxiangbc.com/#/exam/269"),
    ]

    print("="*60)
    print("开始爬取试卷题目")
    print("="*60)
    print("\n提示: 浏览器将打开,您可以观察爬取过程")
    print("如果需要登录,请在浏览器中手动登录后继续")
    print("\n按Ctrl+C停止爬取")

    driver = setup_driver()

    all_content = []

    try:
        for exam_name, exam_url in exam_urls:
            content = scrape_single_exam(driver, exam_url, exam_name)
            if content:
                all_content.append(f"\n{'='*60}\n{exam_name}\n{'='*60}\n{content}")

            time.sleep(3)  # 等待一段时间再访问下一个

        # 合并所有内容到一个文件
        if all_content:
            with open("all_exam_questions.txt", "w", encoding="utf-8") as f:
                f.write("小象编程 - Python复赛模拟题汇总\n")
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n".join(all_content))
            print(f"\n所有题目已合并保存到: all_exam_questions.txt")

    except KeyboardInterrupt:
        print("\n用户中断爬取")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n按Enter键关闭浏览器...")
        input()
        driver.quit()

if __name__ == "__main__":
    main()