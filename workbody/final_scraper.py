"""
完整版爬虫 - 进入每个试卷页面获取所有题目
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """设置Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_all_questions(driver, exam_url, exam_name):
    """进入试卷页面并获取所有题目"""
    print(f"\n正在爬取: {exam_name}")
    print(f"URL: {exam_url}")
    
    driver.get(exam_url)
    time.sleep(3)
    
    try:
        # 步骤1: 填写姓名
        print("步骤1: 填写姓名...")
        try:
            name_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="姓名" or contains(@placeholder, "姓名")]'))
            )
            name_input.clear()
            name_input.send_keys("测试用户")
            print("✓ 已填写姓名")
            time.sleep(1)
        except TimeoutException:
            print("! 未找到姓名输入框")
        
        # 步骤2: 点击开始考试
        print("步骤2: 点击开始考试...")
        try:
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "开始考试")]'))
            )
            start_button.click()
            print("✓ 已点击开始考试")
            time.sleep(5)  # 等待题目加载
        except TimeoutException:
            print("! 未找到开始考试按钮")
        
        # 步骤3: 获取题目总数和所有题目
        print("步骤3: 获取所有题目...")
        all_questions = []
        
        # 尝试获取当前第一题
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            all_questions.append(f"\n=== 第1题 ===\n{page_text}")
            print("✓ 已获取第1题")
        except:
            print("✗ 获取第1题失败")
        
        # 尝试获取题目总数
        try:
            progress_element = driver.find_element(By.XPATH, '//div[contains(text(), "进度")]')
            progress_text = progress_element.text
            print(f"进度信息: {progress_text}")
            
            # 解析总题数
            if '/' in progress_text:
                total = int(progress_text.split('/')[-1].strip())
                print(f"总题数: {total}")
            else:
                total = 14  # 默认14题
                print(f"使用默认题数: {total}")
        except:
            total = 14
            print(f"无法获取进度信息,使用默认题数: {total}")
        
        # 步骤4: 通过"下一题"按钮或答题卡导航获取所有题目
        print(f"步骤4: 遍历获取 {total} 道题目...")
        
        for i in range(2, total + 1):
            try:
                # 尝试点击"下一题"按钮
                next_button = driver.find_element(By.XPATH, '//button[contains(text(), "下一题")]')
                next_button.click()
                time.sleep(2)
                
                # 获取题目内容
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                all_questions.append(f"\n=== 第{i}题 ===\n{page_text}")
                print(f"✓ 已获取第{i}题")
                
            except NoSuchElementException:
                # 如果"下一题"按钮不存在,尝试通过答题卡导航
                print(f"尝试通过答题卡获取第{i}题...")
                try:
                    # 查找答题卡中的题目按钮
                    answer_card_buttons = driver.find_elements(By.CSS_SELECTOR, 'button, div[class*="题"]')
                    
                    for btn in answer_card_buttons:
                        btn_text = btn.text.strip()
                        if btn_text == str(i) or btn_text == f"第{i}题":
                            btn.click()
                            time.sleep(2)
                            
                            page_text = driver.find_element(By.TAG_NAME, 'body').text
                            all_questions.append(f"\n=== 第{i}题 ===\n{page_text}")
                            print(f"✓ 已获取第{i}题(通过答题卡)")
                            break
                except Exception as e:
                    print(f"✗ 获取第{i}题失败: {e}")
                    break
            
            except Exception as e:
                print(f"✗ 获取第{i}题失败: {e}")
                break
        
        # 保存单个试卷
        with open(f"{exam_name}_完整.txt", "w", encoding="utf-8") as f:
            f.write(f"试卷: {exam_name}\n")
            f.write(f"URL: {exam_url}\n")
            f.write("="*60 + "\n\n")
            f.write("\n".join(all_questions))
        
        print(f"✓ {exam_name} 爬取完成,共获取 {len(all_questions)} 题")
        
        return {
            'exam_name': exam_name,
            'url': exam_url,
            'questions': all_questions,
            'total_questions': len(all_questions)
        }
        
    except Exception as e:
        print(f"✗ {exam_name} 爬取失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误信息
        with open(f"{exam_name}_错误.txt", "w", encoding="utf-8") as f:
            f.write(f"试卷: {exam_name}\n")
            f.write(f"URL: {exam_url}\n")
            f.write(f"错误: {e}\n")
            f.write("="*60 + "\n\n")
            try:
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                f.write(page_text)
            except:
                f.write("无法获取页面内容")
        
        return {
            'exam_name': exam_name,
            'url': exam_url,
            'error': str(e)
        }

def main():
    """主函数"""
    print("="*60)
    print("完整试卷题目爬虫 - 进入试卷页面获取所有题目")
    print("="*60)
    
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
    
    print("正在启动浏览器...")
    driver = setup_driver()
    print("✓ 浏览器启动成功!")
    
    all_results = []
    
    try:
        for i, (exam_name, exam_url) in enumerate(exams, 1):
            print(f"\n[{i}/{len(exams)}] ====================")
            result = scrape_all_questions(driver, exam_url, exam_name)
            all_results.append(result)
            
            # 试卷之间休息一下
            time.sleep(3)
        
        # 创建汇总文件
        print("\n" + "="*60)
        print("正在创建汇总文件...")
        print("="*60)
        
        summary_content = []
        summary_content.append("="*60 + "\n")
        summary_content.append("小象编程 - Python复赛模拟题完整汇总\n")
        summary_content.append(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        summary_content.append(f"共爬取 {len(exams)} 个试卷\n")
        summary_content.append("="*60 + "\n\n")
        
        success_count = 0
        fail_count = 0
        
        for result in all_results:
            if 'questions' in result and result['questions']:
                success_count += 1
                summary_content.append("\n" + "="*60 + "\n")
                summary_content.append(f"试卷: {result['exam_name']}\n")
                summary_content.append(f"URL: {result['url']}\n")
                summary_content.append(f"题目数: {result['total_questions']}\n")
                summary_content.append("="*60 + "\n\n")
                summary_content.append("\n".join(result['questions']) + "\n\n")
            elif 'error' in result:
                fail_count += 1
                summary_content.append("\n" + "="*60 + "\n")
                summary_content.append(f"试卷: {result['exam_name']}\n")
                summary_content.append(f"爬取失败: {result['error']}\n")
                summary_content.append("="*60 + "\n\n")
        
        # 保存汇总文件
        with open("所有试卷题目汇总.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(summary_content))
        
        print("\n" + "="*60)
        print("✓ 爬取完成!")
        print(f"✓ 成功: {success_count} 个试卷")
        print(f"✗ 失败: {fail_count} 个试卷")
        print(f"✓ 汇总文件: 所有试卷题目汇总.txt")
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