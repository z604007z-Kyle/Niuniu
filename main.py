import os
import discord
from discord import SyncWebhook
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LAST_DATA_FILE = "last_data.txt"

def fetch_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")  # 繞過 headless 偵測

    driver = webdriver.Chrome(service=Service(), options=options)  # 移除 ChromeDriverManager，如果 Actions 環境有問題

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(8)  # 延長等待 JS 載入

    result = {}
    print("頁面載入完成，標題:", driver.title)

    try:
        title_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-title")  # 原 selector
        result['title'] = title_element.text.strip()
    except:
        print("原標題失敗，試備用...")
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "h3, .title, a[href*='/bulletin/']")  # 備用：第一個 h3 或公告連結
            result['title'] = title_element.text.strip()
        except:
            result['title'] = "未找到標題"
    print("標題:", result['title'])

    try:
        date_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-date")
        result['date'] = date_element.text.strip()
    except:
        print("原日期失敗，試備用...")
        try:
            date_element = driver.find_element(By.CSS_SELECTOR, "span.date, small, time")  # 備用
            result['date'] = date_element.text.strip()
        except:
            result['date'] = "未找到日期"
    print("日期:", result['date'])

    try:
        # 先試抓直接連結，避免點擊
        more_link = driver.find_element(By.CSS_SELECTOR, "a[href*='/bulletin/']")  # 抓包含 /bulletin/ 的連結
        result['more_url'] = "https://tw.nexon.com" + more_link.get_attribute("href")
        print("直接抓到詳情 URL:", result['more_url'])
    except:
        print("直接抓連結失敗，試點擊 MORE...")
        try:
            wait = WebDriverWait(driver, 10)
            more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "morearrow__inner")))  # 原 class
            ActionChains(driver).move_to_element(more_button).click().perform()
            time.sleep(3)
            result['more_url'] = driver.current_url
        except:
            print("原 MORE class 失敗，試備用...")
            try:
                more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".more-arrow, a.more, button.more, [onclick*='bulletin']")))  # 備用 class
                ActionChains(driver).move_to_element(more_button).click().perform()
                time.sleep(3)
                result['more_url'] = driver.current_url
            except:
                result['more_url'] = "未能獲取詳情 URL"

    try:
        img_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-img")
        img_url = img_element.value_of_css_property("background-image").split('url("')[1].split('")')[0]
        result['img_url'] = img_url
    except:
        print("原圖片失敗，試備用...")
        try:
            img_element = driver.find_element(By.CSS_SELECTOR, "img[src*='bulletin'], .thumbnail img")
            result['img_url'] = img_element.get_attribute("src")
        except:
            result['img_url'] = "未找到圖片"

    driver.quit()
    return result

def send_to_discord(data):
    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    embed = discord.Embed(
        title=data['title'],
        description=f"日期： {data['date']}\n {data['more_url']}",
        color=discord.Color.green()
    )
    if data['img_url'] != "未找到圖片 URL":
        embed.set_image(url=data['img_url'])
    webhook.send(embed=embed)
    print("訊息發送成功")

def main():
    data = fetch_data()
    current_key = f"{data['title']}|{data['date']}"

    last_key = ""
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r", encoding="utf-8") as f:
            last_key = f.read().strip()

    print("目前 key:", current_key)
    print("上次 key:", last_key)

    if current_key != last_key and "未找到" not in current_key:
        send_to_discord(data)
        with open(LAST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_key)
        print("有新資訊，已發送並更新檔案")
    else:
        print("沒有新資料，或抓取失敗，未發送")

if __name__ == "__main__":
    main()
