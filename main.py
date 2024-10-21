import os
import base64
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def initialize_driver():
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options)

def delete_elements(driver):
    js_script = """
    document.querySelectorAll(
        '.nav__placeholder, .nav.stickyFixed, .private__domain__association__ad, footer, \
        .article__widget, .article__meta, .article__comment, .user__follow__wrap'
    ).forEach(el => el.remove());

    // 删除页签弹窗
    document.querySelectorAll('.modals.dimmer.js-shown').forEach(el => el.remove());
    """
    driver.execute_script(js_script)

def extract_article_info(driver):
    try:
        # 获取页面源代码
        page_source = driver.page_source

        # 提取标题
        title_match = re.search(r'<h1[^>]*class="article__bd__title"[^>]*>(.*?)<\/h1>', page_source, re.S)
        title = title_match.group(1).strip() if title_match else None

        # 提取时间
        time_match = re.search(r'<time[^>]*datetime[^>]*title="(.*?)"', page_source, re.S)
        time_str = time_match.group(1).strip() if time_match else None

        return title, time_str
    except Exception as e:
        print(f"Error extracting article info: {e}")
        return None, None

def sanitize_filename(name):
    # 替换不安全字符为下划线，并移除多余的空格
    return re.sub(r'[\\/*?:"<>|]', '_', name).replace(' ', '_')

def print_to_pdf(driver, url, output_dir):
    driver.get(url)

    try:
        # 等待页面加载完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # 删除特定元素
        delete_elements(driver)

        # 提取标题和时间
        title, time = extract_article_info(driver)
        if title is None or time is None:
            print(f"Error: Could not retrieve title or time for {url}")
            return

        # 生成文件名 (安全处理)
        pdf_file_name = f"{time} {title}.pdf"
        pdf_file_name = sanitize_filename(pdf_file_name)
        pdf_file_path = os.path.join(output_dir, pdf_file_name)

        # 使用 DevTools Protocol 打印为 PDF
        result = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})

        # 将 Base64 编码的PDF解码，并保存为文件
        with open(pdf_file_path, "wb") as f:
            f.write(base64.b64decode(result['data']))

        print(f"PDF 生成完成：{pdf_file_path}")

    except Exception as e:
        print(f"Error processing {url}: {e}")

def read_urls_from_file(file_path):
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error reading URLs from file: {e}")
    return urls

def main():
    # 创建pdf目录，如果不存在
    pdf_dir = os.path.join(os.getcwd(), 'pdf2')
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    driver = initialize_driver()

    # 从文件中读取URL列表
    urls = read_urls_from_file('article_urls.txt')

    for url in urls:
        print_to_pdf(driver, url, pdf_dir)
        time.sleep(1)

    driver.quit()
    print("所有PDF生成完成")

if __name__ == "__main__":
    main()