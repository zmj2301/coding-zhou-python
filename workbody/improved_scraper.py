"""
改进版爬虫 - 通过答题卡数字按钮遍历所有题目
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def scrape_all_questions_improved(driver, exam_url, exam_name):
    """通过答题卡按钮遍历所有题目"""
    print(f"\n正在爬取: {exam_name}")
    print(f"URL: {exam_url}")
    
    driver.get(exam_url)
    time.sleep(5)  # 增加等待时间
    
    # 填写姓名并开始考试
    try:
        print("填写姓名...")
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]'))
        )
        name_input.clear()
        name_input.send_keys("测试用户")
        time.sleep(2)
        
        print("点击开始考试...")
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "开始考试")]'))
        )
        start_button.click()
        print("✓ 已开始考试")
        time.sleep(8)  # 增加等待时间,确保题目完全加载
        
    except Exception as e:
        print(f"✗ 开始考试失败: {e}")
        return None
    
    # 获取所有题目
    all_questions = []
    
    try:
        # 获取总题数
        progress_text = driver.find_element(By.XPATH, '//div[contains(text(), "进度")]').text
        print(f"进度信息: {progress_text}")
        
        # 解析总题数
        total_questions = 14  # 默认14题
        if '/' in progress_text:
            parts = progress_text.split('/')
            try:
                total_questions = int(parts[-1].strip())
                print(f"✓ 总题数: {total_questions}")
            except:
                pass
        
        # 尝试获取第一题
        print("\n开始遍历题目...")
        
        # 先保存第1题(当前显示的题目)
        current_page = driver.find_element(By.TAG_NAME, 'body').text
        all_questions.append(f"\n{'='*60}\n第 1 题\n{'='*60}\n\n{current_page}\n")
        print(f"✓ 已获取第1题")
        
        # 通过答题卡按钮遍历其他题目
        for question_num in range(2, total_questions + 1):
            print(f"\n正在获取第 {question_num} 题...")
            
            # 方法1: 尝试点击答题卡数字按钮
            try:
                # 查找所有可能的按钮元素
                all_buttons = driver.find_elements(By.CSS_SELECTOR, 'button, div[role="button"], span[role="button"]')
                
                target_button = None
                for btn in all_buttons:
                    btn_text = btn.text.strip()
                    if btn_text == str(question_num):
                        target_button = btn
                        break
                
                if target_button:
                    # 点击按钮
                    target_button.click()
                    time.sleep(3)  # 等待题目加载
                    
                    # 获取题目内容
                    current_page = driver.find_element(By.TAG_NAME, 'body').text
                    all_questions.append(f"\n{'='*60}\n第 {question_num} 题\n{'='*60}\n\n{current_page}\n")
                    print(f"✓ 已获取第 {question_num} 题")
                else:
                    print(f"✗ 未找到第 {question_num} 题按钮")
                    
                    # 方法2: 尝试点击"下一题"按钮
                    try:
                        next_button = driver.find_element(By.XPATH, '//button[contains(text(), "下一题")]')
                        next_button.click()
                        time.sleep(3)
                        
                        current_page = driver.find_element(By.TAG_NAME, 'body').text
                        all_questions.append(f"\n{'='*60}\n第 {question_num} 题\n{'='*60}\n\n{current_page}\n")
                        print(f"✓ 通过下一题按钮获取第 {question_num} 题")
                    except:
                        print(f"✗ 无法获取第 {question_num} 题")
                        break
                        
            except Exception as e:
                print(f"✗ 获取第 {question_num} 题失败: {e}")
                break
        
        # 保存单个试卷文件
        with open(f"{exam_name}_完整题目.txt", "w", encoding="utf-8") as f:
            f.write(f"试卷: {exam_name}\n")
            f.write(f"URL: {exam_url}\n")
            f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            f.write("\n".join(all_questions))
        
        print(f"\n✓ {exam_name} 完成,共获取 {len(all_questions)} 题")
        
        return {
            'exam_name': exam_name,
            'url': exam_url,
            'questions': all_questions,
            'count': len(all_questions)
        }
        
    except Exception as e:
        print(f"✗ 爬取失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存当前页面
        try:
            current_page = driver.find_element(By.TAG_NAME, 'body').text
            with open(f"{exam_name}_部分内容.txt", "w", encoding="utf-8") as f:
                f.write(f"试卷: {exam_name}\n")
                f.write(f"错误: {e}\n")
                f.write("="*60 + "\n\n")
                f.write(current_page)
        except:
            pass
        
        return None

def main():
    print("="*60)
    print("改进版试卷爬虫 - 通过答题卡按钮遍历题目")
    print("="*60)
    
    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # 试卷列表
    exams = [
        ("2026年信息素养大赛Python复赛卷(一)", "https://exam.xiaoxiangbc.com/#/exam/271"),
        ("2026年信息素养大赛Python复赛模拟卷(二)小学组", "https://exam.xiaoxiangbc.com/#/exam/263"),
        ("2026年信息素养大赛Python复赛模拟卷(三)小学组", "https://exam.xiaoxiangbc.com/#/exam/266"),
        ("2026年信息素养大赛Python复赛卷(四)小学组", "https://exam.xiaoxiangbc.com/#/exam/272"),
        ("2026年信息素养大赛Python复赛卷(五)小学组", "https://exam.xiaoxiangbc.com/#/exam/270"),
        ("2026年信息素养大赛Python复赛模拟卷(二)初中组", "https://exam.xiaoxiangbc.com/#/exam/262"),
        ("2026年信息素养大赛Python复赛模拟卷(三)初中组", "https://exam.xiaoxiangbc.com/#/exam/265"),
        ("2026年信息素养大赛Python复赛卷(四)初中组", "https://exam.xiaoxiangbc.com/#/exam/267"),
        ("2026年信息素养大赛Python复赛卷(五)初中组", "https://exam.xiaoxiangbc.com/#/exam/269"),
    ]
    
    all_results = []
    
    try:
        for i, (exam_name, exam_url) in enumerate(exams, 1):
            print(f"\n[{i}/{len(exams)}] {'='*60}")
            result = scrape_all_questions_improved(driver, exam_url, exam_name)
            if result:
                all_results.append(result)
            time.sleep(3)
        
        # 创建汇总文件
        print("\n" + "="*60)
        print("正在创建汇总文件...")
        
        summary = []
        summary.append("="*60 + "\n")
        summary.append("小象编程 - Python复赛模拟题完整汇总\n")
        summary.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        summary.append(f"共爬取 {len(all_results)} 个试卷\n")
        summary.append("="*60 + "\n\n")
        
        for result in all_results:
            if result and 'questions' in result:
                summary.append("\n" + "="*60 + "\n")
                summary.append(f"试卷: {result['exam_name']}\n")
                summary.append(f"题目数: {result['count']}\n")
                summary.append("="*60 + "\n\n")
                summary.append("\n".join(result['questions']) + "\n\n")
        
        # 保存汇总文件
        with open("所有试卷题目汇总.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(summary))
        
        print("\n" + "="*60)
        print("✓ 爬取完成!")
        print(f"✓ 汇总文件: 所有试卷题目汇总.txt")
        print(f"✓ 单个试卷文件: {len(all_results)} 个")
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