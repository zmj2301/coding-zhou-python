"""
小象编程考试题目爬虫 - 改进版
爬取指定页面的所有题目并保存到txt文件
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def setup_driver():
    """设置Chrome WebDriver"""
    print("正在配置Chrome选项...")
    chrome_options = Options()
    # 使用无头模式
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-software-rasterizer')
    # 设置用户代理
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        print("正在启动Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome浏览器启动成功!")
        return driver
    except WebDriverException as e:
        print(f"启动Chrome浏览器失败: {e}")
        print("\n可能的原因:")
        print("1. 未安装Chrome浏览器")
        print("2. ChromeDriver版本不匹配")
        print("3. ChromeDriver未添加到PATH环境变量")
        print("\n请尝试:")
        print("- 确保已安装Chrome浏览器")
        print("- 下载对应版本的ChromeDriver: https://chromedriver.chromium.org/downloads")
        print("- 或运行: pip install webdriver-manager")
        raise

def get_exam_list(driver, url):
    """获取试卷列表"""
    print(f"正在访问页面: {url}")
    driver.get(url)
    print("等待页面加载...")
    time.sleep(5)  # 增加等待时间

    exam_links = []
    try:
        # 查找所有考试链接
        print("正在查找考试链接...")
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/exam/"]')
        print(f"找到 {len(links)} 个链接")

        for link in links:
            href = link.get_attribute('href')
            text = link.text
            print(f"链接: {href} - 文本: {text}")
            if href and '/exam/' in href and '开始考试' in text:
                if href not in exam_links:  # 避免重复
                    exam_links.append(href)
    except Exception as e:
        print(f"获取考试列表失败: {e}")
        import traceback
        traceback.print_exc()

    return exam_links

def scrape_exam_questions(driver, exam_url, exam_title=""):
    """爬取单个试卷的题目"""
    print(f"正在访问试卷: {exam_url}")
    driver.get(exam_url)
    time.sleep(3)

    questions = []

    try:
        # 尝试点击"开始考试"按钮
        try:
            print("查找'开始考试'按钮...")
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "开始考试")]'))
            )
            print("找到'开始考试'按钮，正在点击...")
            start_button.click()
            time.sleep(3)
            print("已点击'开始考试'按钮")
        except TimeoutException:
            print("未找到'开始考试'按钮，可能已经进入考试")
        except Exception as e:
            print(f"点击'开始考试'按钮时出错: {e}")

        # 等待页面加载
        print("等待题目加载...")
        time.sleep(3)

        # 获取整个页面的HTML用于调试
        page_html = driver.page_source
        print(f"页面HTML长度: {len(page_html)}")

        # 尝试多种选择器
        selectors = [
            '.question-item',
            '.question',
            '[class*="question"]',
            '.problem',
            '[class*="problem"]',
            '.exam-question',
            '[class*="exam-question"]'
        ]

        question_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                    question_elements = elements
                    break
            except Exception as e:
                pass

        if not question_elements:
            print("未找到题目元素，尝试获取整个页面文本...")
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            print(f"页面文本长度: {len(page_text)}")

            # 保存页面源码用于调试
            debug_file = f"debug_{exam_title}_{int(time.time())}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(page_html)
            print(f"页面源码已保存到: {debug_file}")

            return [f"\n试卷: {exam_title}\n无法解析题目结构，请查看调试文件\n"]

        # 提取题目文本
        for idx, q_elem in enumerate(question_elements, 1):
            try:
                question_text = q_elem.text
                if question_text.strip():
                    questions.append(f"\n题目 {idx}:\n{question_text}\n")
                    print(f"提取题目 {idx} 成功")
            except Exception as e:
                print(f"提取题目 {idx} 失败: {e}")

    except TimeoutException:
        print("页面加载超时")
        return [f"\n试卷: {exam_title}\n加载超时\n"]
    except Exception as e:
        print(f"爬取试卷失败: {e}")
        import traceback
        traceback.print_exc()
        return [f"\n试卷: {exam_title}\n爬取失败: {e}\n"]

    return questions

def main():
    """主函数"""
    url = "https://exam.xiaoxiangbc.com/#/exams?category=Pythonfusai&grade=fusai-moni"
    output_file = "exam_questions.txt"

    print("="*60)
    print("小象编程考试题目爬虫")
    print("="*60)

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"无法启动浏览器: {e}")
        print("\n将尝试使用替代方案...")
        # 创建一个提示文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("爬虫运行失败\n\n")
            f.write("可能的原因:\n")
            f.write("1. 未安装Chrome浏览器或ChromeDriver\n")
            f.write("2. ChromeDriver版本不匹配\n\n")
            f.write("解决方案:\n")
            f.write("1. 安装Chrome浏览器\n")
            f.write("2. 运行: pip install webdriver-manager\n")
            f.write("3. 修改脚本使用webdriver_manager自动管理驱动\n")
        return

    try:
        print(f"\n正在访问: {url}")
        exam_links = get_exam_list(driver, url)

        if not exam_links:
            print("未找到考试链接")
            print("尝试获取页面截图...")
            driver.save_screenshot("page_screenshot.png")
            print("截图已保存为 page_screenshot.png")

            # 尝试获取整个页面的HTML
            print("\n尝试获取页面HTML...")
            html = driver.page_source
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("页面HTML已保存为 page_source.html")
            return

        print(f"\n找到 {len(exam_links)} 个试卷:")
        for i, link in enumerate(exam_links, 1):
            print(f"{i}. {link}")

        all_questions = []

        for i, exam_url in enumerate(exam_links, 1):
            print(f"\n{'='*60}")
            print(f"正在爬取第 {i}/{len(exam_links)} 个试卷...")
            print(f"{'='*60}")

            questions = scrape_exam_questions(driver, exam_url, f"试卷{i}")

            if questions:
                all_questions.append(f"\n{'='*60}\n试卷 {i}\n{'='*60}")
                all_questions.extend(questions)
            else:
                print(f"试卷 {i} 爬取失败")

            time.sleep(2)  # 避免请求过快

        # 保存到文件
        if all_questions:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("小象编程 - Python复赛模拟题汇总\n")
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
                f.write("\n".join(all_questions))

            print(f"\n{'='*60}")
            print(f"成功！题目已保存到 {output_file}")
            print(f"共爬取 {len(exam_links)} 个试卷")
            print(f"{'='*60}")
        else:
            print("未爬取到任何题目")

    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n正在关闭浏览器...")
        driver.quit()
        print("浏览器已关闭")

if __name__ == "__main__":
    main()