import os
import discord
from discord import SyncWebhook, Embed
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LAST_DATA_FILE = "last_data.txt"

def fetch_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-images")  # 加快載入（可选）
    options.add_argument("--lang=zh-TW")

    # GitHub Actions 環境用系統 chromedriver
    driver = webdriver.Chrome(options=options)

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(5)  # 多等 JS 載入

    result = {}
    print("頁面載入完成，標題:", driver.title)

    try:
        # 新結構：第一則公告的標題（通常是 h3 或 a 內文字）
        title_element = driver.find_element(By.CSS_SELECTOR, "ul li:first-child h3, ul li:first-child a")  # 抓第一則的 h3 或連結
        result['title'] = title_element.text.strip()
        print("找到標題:", result['title'])
    except Exception as e:
        print("標題抓取失敗:", str(e))
        result['title'] = "未找到標題"

    try:
        # 日期通常在小文字或 span
        date_element = driver.find_element(By.CSS_SELECTOR, "ul li:first-child span, ul li:first-child .date, ul li:first-child small")
        result['date'] = date_element.text.strip()
        print("找到日期:", result['date'])
    except Exception as e:
        print("日期抓取失敗:", str(e))
        result['date'] = "未找到日期"

    try:
        # MORE 連結（直接抓 href）
        more_link = driver.find_element(By.CSS_SELECTOR, "ul li:first-child a[href*='/bulletin/']")
        result['more_url'] = "https://tw.nexon.com" + more_link.get_attribute("href")
        print("找到詳情 URL:", result['more_url'])
    except Exception as e:
        print("MORE 連結抓取失敗:", str(e))
        result['more_url'] = url

    try:
        # 圖片現在是 img 標籤
        img_element = driver.find_element(By.CSS_SELECTOR, "ul li:first-child img")
        result['img_url'] = img_element.get_attribute("src")
        if result['img_url'].startswith("//"):
            result['img_url'] = "https:" + result['img_url']
        elif not result['img_url'].startswith("http"):
            result['img_url'] = "https://tw.nexon.com" + result['img_url']
        print("找到圖片:", result['img_url'])
    except Exception as e:
        print("圖片抓取失敗:", str(e))
        result['img_url'] = "未找到圖片"

    driver.quit()
    return result

def send_to_discord(data):
    if not WEBHOOK_URL:
        print("錯誤：DISCORD_WEBHOOK_URL 未設定")
        return
    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    embed = Embed(
        title=data.get('title', '無標題'),
        description=f"日期： {data.get('date', '未知')}\n[詳情連結]({data.get('more_url', '')})",
        color=discord.Color.green()
    )
    if data.get('img_url') and data['img_url'] != "未找到圖片":
        embed.set_image(url=data['img_url'])
    webhook.send(embed=embed)
    print("訊息已成功發送至 Discord")

def main():
    data = fetch_data()
    current_key = f"{data.get('title','無標題')}|{data.get('date','未知')}"

    last_key = ""
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r", encoding="utf-8") as f:
            last_key = f.read().strip()

    print(f"目前 key: {current_key}")
    print(f"上次 key: {last_key}")

    if current_key != last_key and "未找到" not in current_key:  # 避免抓取失敗時誤發
        send_to_discord(data)
        with open(LAST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_key)
        print("檢測到新資訊，已發送並更新 last_data.txt！")
    else:
        print("沒有新資訊（或與上次相同），未發送。")

if __name__ == "__main__":
    main()
