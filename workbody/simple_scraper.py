"""
简单的页面HTML获取脚本
用于分析页面结构
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    # 设置Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=chrome_options)

    # 获取试卷列表页面
    url = "https://exam.xiaoxiangbc.com/#/exams?category=Pythonfusai&grade=fusai-moni"
    driver.get(url)
    time.sleep(5)

    # 保存列表页面HTML
    with open("exam_list_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("试卷列表页面HTML已保存为 exam_list_page.html")

    # 获取第一个试卷页面
    exam_url = "https://exam.xiaoxiangbc.com/#/exam/271"
    driver.get(exam_url)
    time.sleep(5)

    # 保存试卷页面HTML
    with open("exam_271_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("试卷271页面HTML已保存为 exam_271_page.html")

    # 尝试截图
    driver.save_screenshot("exam_271_screenshot.png")
    print("试卷271截图已保存为 exam_271_screenshot.png")

    # 获取页面文本
    page_text = driver.find_element(By.TAG_NAME, 'body').text
    with open("exam_271_text.txt", "w", encoding="utf-8") as f:
        f.write(page_text)
    print("试卷271文本已保存为 exam_271_text.txt")

    driver.quit()
    print("完成!")

if __name__ == "__main__":
    from selenium.webdriver.common.by import By
    main()