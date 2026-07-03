"""
全自动后台运行的考试题目爬虫
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """设置Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_exam(driver, exam_id, exam_name):
    """爬取单个试卷"""
    url = f"https://exam.xiaoxiangbc.com/#/exam/{exam_id}"
    print(f"\n正在爬取: {exam_name} (ID: {exam_id})")

    try:
        driver.get(url)
        time.sleep(3)

        # 尝试点击"开始考试"按钮
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "开始考试")]'))
            )
            button.click()
            print("✓ 已点击'开始考试'按钮")
            time.sleep(5)  # 等待题目加载
        except TimeoutException:
            print("! 未找到'开始考试'按钮,可能已开始考试或需要登录")

        # 获取页面内容
        time.sleep(3)
        page_source = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, 'body').text

        # 保存单独的文件
        with open(f"{exam_name}_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        with open(f"{exam_name}_content.txt", "w", encoding="utf-8") as f:
            f.write(page_text)

        print(f"✓ 已保存 {exam_name} 的内容")

        return {
            'exam_name': exam_name,
            'exam_id': exam_id,
            'page_text': page_text,
            'page_source_length': len(page_source)
        }

    except Exception as e:
        print(f"✗ 爬取失败: {e}")
        return {
            'exam_name': exam_name,
            'exam_id': exam_id,
            'error': str(e)
        }

def extract_questions_from_text(text):
    """从文本中提取题目"""
    questions = []

    # 简单的题目提取逻辑
    lines = text.split('\n')
    question_num = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 查找题目编号
        if line.startswith('题目') or line.startswith('第') or any(str(i) in line for i in range(1, 15)):
            question_num += 1
            questions.append(f"\n{line}\n")
        elif question_num > 0:
            questions.append(line + "\n")

    return questions

def main():
    """主函数"""
    print("="*60)
    print("全自动考试题目爬虫")
    print("="*60)

    # 试卷列表
    exams = [
        ("试卷1_2026复赛一", 271),
        ("试卷2_2026模拟二小学", 263),
        ("试卷3_2026模拟三小学", 266),
        ("试卷4_2026复赛四小学", 272),
        ("试卷5_2026复赛五小学", 270),
        ("试卷6_2026模拟二初中", 262),
        ("试卷7_2026模拟三初中", 265),
        ("试卷8_2026复赛四初中", 267),
        ("试卷9_2026复赛五初中", 269),
    ]

    driver = setup_driver()
    all_results = []

    try:
        for exam_name, exam_id in exams:
            result = scrape_exam(driver, exam_id, exam_name)
            all_results.append(result)
            time.sleep(2)  # 避免请求过快

        # 合并所有结果
        print("\n" + "="*60)
        print("正在整理所有题目...")
        print("="*60)

        final_content = []
        final_content.append("小象编程 - Python复赛模拟题汇总\n")
        final_content.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        final_content.append(f"共爬取 {len(exams)} 个试卷\n")
        final_content.append("="*60 + "\n\n")

        for result in all_results:
            if 'page_text' in result:
                final_content.append(f"\n{'='*60}\n")
                final_content.append(f"{result['exam_name']}\n")
                final_content.append(f"{'='*60}\n\n")

                # 提取题目
                questions = extract_questions_from_text(result['page_text'])
                if questions:
                    final_content.extend(questions)
                else:
                    final_content.append(result['page_text'] + "\n")

                final_content.append("\n")

            elif 'error' in result:
                final_content.append(f"\n{result['exam_name']}: 爬取失败 - {result['error']}\n")

        # 保存汇总文件
        with open("all_exam_questions_summary.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(final_content))

        print(f"\n✓ 所有题目已汇总保存到: all_exam_questions_summary.txt")

        # 保存JSON格式的详细信息
        with open("scraping_results.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"✓ 详细结果已保存到: scraping_results.json")

        # 统计结果
        successful = len([r for r in all_results if 'page_text' in r])
        failed = len([r for r in all_results if 'error' in r])

        print(f"\n统计:")
        print(f"  成功: {successful} 个试卷")
        print(f"  失败: {failed} 个试卷")

        if failed > 0:
            print("\n提示: 部分试卷可能需要登录才能查看题目")
            print("请检查生成的HTML文件查看页面结构")

    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n✓ 浏览器已关闭")
        print("="*60)

if __name__ == "__main__":
    main()