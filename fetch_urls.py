import time
from collections import OrderedDict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException

def initialize_driver():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 注释掉headless模式以便调试
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options)

def close_modals(driver):
    try:
        js_script = """
        document.querySelectorAll('.modals.dimmer.js-shown').forEach(el => el.style.display = 'none');
        """
        driver.execute_script(js_script)
    except Exception as e:
        print(f"关闭模态窗口时出错: {e}")

def wait_for_page_load(driver, element_selector, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
        )
    except TimeoutException:
        print(f"等待页面加载超时：{element_selector}")

def get_current_page(driver):
    try:
        active_page = driver.find_element(By.CSS_SELECTOR, '.pagination a.active')
        return int(active_page.text)
    except NoSuchElementException:
        return 1

def click_next_page(driver, pagination_selector):
    for _ in range(5):  # 重试最多5次
        try:
            close_modals(driver)
            next_button = driver.find_element(By.CSS_SELECTOR, pagination_selector)
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            next_button.click()
            time.sleep(5)  # 给页面更多时间加载
            return
        except (ElementClickInterceptedException, TimeoutException, NoSuchElementException) as e:
            print(f"点击下一页按钮时出现问题，重试。异常信息: {e}")
            time.sleep(5)  # 增加等待时间以应对限流
    raise Exception("连续5次点击下一页按钮失败")

def get_all_urls(driver, start_url, pagination_selector, link_selector):
    driver.get(start_url)
    all_urls = OrderedDict()
    last_url_count = 0
    retries = 0

    while True:  # 无限循环，直到手动停止或者达到限制
        current_page = get_current_page(driver)
        wait_for_page_load(driver, link_selector)
        time.sleep(3)  # 让页面有时间完成加载

        # 获取当前页面的所有文章链接
        links = driver.find_elements(By.CSS_SELECTOR, link_selector)
        for link in links:
            url = link.get_attribute('href')
            if url.startswith('/'):
                url = "https://xueqiu.com" + url
            all_urls[url] = None  # 使用 OrderedDict 去重并保持顺序

        print(f"当前页数: {current_page}, 已获取链接数量: {len(all_urls)}")

        # 如果链接数量没有变化，尝试继续获取下一页
        if len(all_urls) == last_url_count:
            retries += 1
            print(f"链接数量没有变化，重试次数: {retries}")
            if retries >= 5:
                print("连续5次没有新链接，停止抓取")
                break
            time.sleep(5)  # 等待5秒再重试
        else:
            last_url_count = len(all_urls)
            retries = 0

        # 尝试点击下一页按钮
        try:
            click_next_page(driver, pagination_selector)
        except Exception as e:
            print(f"点击下一页按钮失败，原因: {e}")
            break

        time.sleep(5)  # 适当的等待

    return list(all_urls.keys())  # 返回 URL 列表

def main():
    driver = initialize_driver()

    start_url = 'https://xueqiu.com/2201555376/column'
    pagination_selector = '.pagination__next'
    link_selector = '.column__item__title > a'

    try:
        all_article_urls = get_all_urls(driver, start_url, pagination_selector, link_selector)
        print(f"所有文章链接: {all_article_urls}")
    finally:
        # 无论是否遇到异常，都将已获取的链接保存到txt文件中
        with open('article_urls.txt', 'w', encoding='utf-8') as file:
            for url in all_article_urls:
                file.write(url + '\n')

        driver.quit()
        print("所有URL已保存到article_urls.txt")

if __name__ == "__main__":
    main()