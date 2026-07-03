"""
完整版爬虫 - 爬取所有试卷的所有题目
包括单选题、多选题、编程题等所有题型
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def scrape_all_questions_from_exam(driver, exam_id, exam_name):
    """爬取单个试卷的所有题目"""
    url = f"https://exam.xiaoxiangbc.com/#/exam/{exam_id}"
    print(f"\n正在爬取: {exam_name}")
    print(f"URL: {url}")

    driver.get(url)
    time.sleep(3)

    # 填写姓名并开始考试
    try:
        name_input = driver.find_element(By.XPATH, '//input[@placeholder="姓名" or contains(@placeholder, "姓名")]')
        name_input.send_keys("测试用户")
        time.sleep(1)

        button = driver.find_element(By.XPATH, '//button[contains(text(), "开始考试")]')
        button.click()
        print("✓ 已开始考试")
        time.sleep(5)

        # 获取所有题目
        all_questions_text = []

        # 首先获取当前页面的题目
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        all_questions_text.append(page_text)

        # 尝试获取总题数
        try:
            progress_text = driver.find_element(By.XPATH, '//div[contains(text(), "进度")]').text
            total_questions = int(progress_text.split('/')[-1])
            print(f"✓ 试卷共 {total_questions} 题")

            # 通过答题卡导航获取所有题目
            try:
                # 查找答题卡按钮
                answer_card_buttons = driver.find_elements(By.XPATH, '//div[contains(@class, "answer-card")]//button | //div[contains(@class, "答题卡")]//button')

                if not answer_card_buttons:
                    # 尝试其他方式
                    answer_card_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[class*="题"]')

                if answer_card_buttons:
                    print(f"找到 {len(answer_card_buttons)} 个题目导航按钮")
                    for i, btn in enumerate(answer_card_buttons[:total_questions], 1):
                        try:
                            btn.click()
                            time.sleep(2)
                            question_text = driver.find_element(By.TAG_NAME, 'body').text
                            all_questions_text.append(f"\n--- 第{i}题 ---\n{question_text}")
                            print(f"✓ 已获取第 {i} 题")
                        except:
                            pass
            except Exception as e:
                print(f"通过答题卡导航失败: {e}")

        except Exception as e:
            print(f"获取题目数量失败: {e}")

        # 保存单个试卷
        with open(f"{exam_name}_完整题目.txt", "w", encoding="utf-8") as f:
            f.write(f"试卷: {exam_name}\n")
            f.write(f"ID: {exam_id}\n")
            f.write("="*60 + "\n\n")
            for text in all_questions_text:
                f.write(text + "\n\n")

        print(f"✓ {exam_name} 爬取完成")

        return {
            'exam_name': exam_name,
            'exam_id': exam_id,
            'content': "\n\n".join(all_questions_text)
        }

    except Exception as e:
        print(f"✗ {exam_name} 爬取失败: {e}")
        return {
            'exam_name': exam_name,
            'exam_id': exam_id,
            'error': str(e)
        }

def main():
    print("="*60)
    print("完整版试卷题目爬虫")
    print("="*60)

    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    print("正在启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    print("✓ 浏览器启动成功!")

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

    all_results = []

    try:
        for i, (exam_name, exam_id) in enumerate(exams, 1):
            print(f"\n[{i}/{len(exams)}]")
            result = scrape_all_questions_from_exam(driver, exam_id, exam_name)
            all_results.append(result)
            time.sleep(3)

        # 创建汇总文件
        print("\n" + "="*60)
        print("正在创建汇总文件...")
        print("="*60)

        summary = []
        summary.append("="*60 + "\n")
        summary.append("小象编程 - Python复赛模拟题完整汇总\n")
        summary.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        summary.append(f"共爬取 {len(exams)} 个试卷\n")
        summary.append("="*60 + "\n\n")

        for result in all_results:
            if 'content' in result:
                summary.append("\n" + "="*60 + "\n")
                summary.append(f"{result['exam_name']}\n")
                summary.append("="*60 + "\n\n")
                summary.append(result['content'] + "\n\n")
            elif 'error' in result:
                summary.append(f"\n{result['exam_name']}: 爬取失败 - {result['error']}\n\n")

        # 保存汇总文件
        with open("Python复赛模拟题_完整汇总.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(summary))

        print("\n" + "="*60)
        print("✓ 爬取完成!")
        print(f"✓ 完整汇总文件: Python复赛模拟题_完整汇总.txt")
        print(f"✓ 单个试卷文件: 共 {len([r for r in all_results if 'content' in r])} 个")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n✓ 浏览器已关闭")

if __name__ == "__main__":
    main()