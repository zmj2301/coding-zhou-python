"""
简化版全自动爬虫 - 专注于获取所有试卷的题目
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def main():
    print("="*60)
    print("开始爬取所有试卷")
    print("="*60)

    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    print("正在启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    print("浏览器启动成功!")

    # 试卷列表
    exams = [
        ("2026年信息素养大赛Python复赛卷(一)", "271"),
        ("2026年信息素养大赛Python复赛模拟卷(二)小学组", "263"),
        ("2026年信息素养大赛Python复赛模拟卷(三)小学组", "266"),
        ("2026年信息素养大赛Python复赛卷(四)小学组", "272"),
        ("2026年信息素养大赛Python复赛卷(五)小学组", "270"),
        ("2026年信息素养大赛Python复赛模拟卷(二)初中组", "262"),
        ("2026年信息素养大赛Python复赛模拟卷(三)初中组", "265"),
        ("2026年信息素养大赛Python复赛卷(四)初中组", "267"),
        ("2026年信息素养大赛Python复赛卷(五)初中组", "269"),
    ]

    all_content = []
    all_content.append("="*60 + "\n")
    all_content.append("小象编程 - Python复赛模拟题汇总\n")
    all_content.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    all_content.append("="*60 + "\n\n")

    try:
        for i, (exam_name, exam_id) in enumerate(exams, 1):
            print(f"\n[{i}/{len(exams)}] 正在爬取: {exam_name}")

            url = f"https://exam.xiaoxiangbc.com/#/exam/{exam_id}"
            driver.get(url)

            print(f"  访问URL: {url}")
            time.sleep(3)

            # 尝试点击开始考试按钮
            try:
                button = driver.find_element(By.XPATH, '//button[contains(text(), "开始考试")]')
                button.click()
                print("  ✓ 已点击'开始考试'按钮")
                time.sleep(3)
            except:
                print("  ! 未找到'开始考试'按钮")

            # 等待页面加载
            time.sleep(2)

            # 获取页面文本
            try:
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                print(f"  ✓ 获取页面文本 (长度: {len(page_text)})")

                # 添加到汇总
                all_content.append("\n" + "="*60 + "\n")
                all_content.append(f"试卷 {i}: {exam_name}\n")
                all_content.append("="*60 + "\n\n")
                all_content.append(page_text + "\n\n")

                # 保存单独的文件
                with open(f"试卷{i}_{exam_id}.txt", "w", encoding="utf-8") as f:
                    f.write(f"试卷: {exam_name}\n")
                    f.write(f"ID: {exam_id}\n")
                    f.write("="*60 + "\n\n")
                    f.write(page_text)
                print(f"  ✓ 已保存单独文件")

            except Exception as e:
                print(f"  ✗ 获取文本失败: {e}")

            time.sleep(1)

        # 保存汇总文件
        with open("所有试卷题目汇总.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(all_content))

        print("\n" + "="*60)
        print("✓ 爬取完成!")
        print(f"✓ 所有题目已保存到: 所有试卷题目汇总.txt")
        print(f"✓ 共爬取 {len(exams)} 个试卷")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n浏览器已关闭")

if __name__ == "__main__":
    main()