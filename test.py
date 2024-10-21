import os
import time
from collections import OrderedDict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options)

def close_modals(driver):
    js_script = """
    document.querySelectorAll('.modals.dimmer.js-shown').forEach(el => el.remove());
    """
    driver.execute_script(js_script)

def wait_for_page_load(driver, element_selector, timeout=20):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
    )

def get_current_page(driver):
    try:
        active_page = driver.find_element(By.CSS_SELECTOR, 'a.active')
        return int(active_page.text)
    except:
        return 1

def get_all_urls(driver, start_url, pagination_selector, link_selector):
    driver.get(start_url)
    all_urls = OrderedDict()

    while True:
        wait_for_page_load(driver, link_selector)

        # 获取当前页面的所有文章链接
        links = driver.find_elements(By.CSS_SELECTOR, link_selector)
        for link in links:
            url = link.get_attribute('href')
            if url.startswith('/'):
                url = "https://xueqiu.com" + url
            all_urls[url] = None  # 使用 OrderedDict 进行去重并保持顺序

        current_page = get_current_page(driver)
        print(f"当前页数: {current_page}, 已获取链接数量: {len(all_urls)}")

        # 查找下一页按钮
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, pagination_selector)
        except:
            print("没有更多页面，抓取完成。")
            break  # 没有更多的页面

        # 如果下一页按钮隐藏，说明已经是最后一页
        if next_button.value_of_css_property('display') == 'none':
            print("已到达最后一页，抓取完成。")
            break

        # 尝试使用 ActionChains 点击
        try:
            close_modals(driver)  # 尝试关闭所有模态对话框
            actions = ActionChains(driver)
            actions.move_to_element(next_button).click().perform()
        except ElementClickInterceptedException as e:
            print(f"点击被其他元素拦截，抓取中止。异常信息: {e}")
            break

        # 等待页面加载完成
        time.sleep(2)  # 先短暂的等待以让页面开始加载
        wait_for_page_load(driver, link_selector)

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