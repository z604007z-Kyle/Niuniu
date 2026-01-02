import os
import discord
from discord import SyncWebhook  # 用 webhook 發訊息，不需要完整 bot
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

load_dotenv()

# 用 Discord Webhook 發訊息（安全，不露 token）
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # 稍後教你建立
CHANNEL_ID = 1286668475997356155  # 你原本的頻道 ID（用來 mention，如果需要）

# 上次資料（用簡單檔案存，或這裡用全域變數；GitHub Actions 每次新容器，用環境變數或外部存，但簡單起見用檔案）
LAST_DATA_FILE = "last_data.txt"

def fetch_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(3)

    result = {}
    try:
        title_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-title")
        result['title'] = title_element.text
    except:
        result['title'] = "未找到目標標題"

    try:
        date_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-date")
        result['date'] = date_element.text
    except:
        result['date'] = "未找到目標日期"

    try:
        wait = WebDriverWait(driver, 10)
        more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "morearrow__inner")))
        ActionChains(driver).move_to_element(more_button).click().perform()
        time.sleep(3)
        result['more_url'] = driver.current_url
    except:
        result['more_url'] = "未能獲取新網址"

    try:
        img_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-img")
        img_url = img_element.value_of_css_property("background-image")
        img_url = img_url.split('url("')[1].split('")')[0]
        result['img_url'] = img_url
    except:
        result['img_url'] = "未找到圖片 URL"

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

def main():
    data = fetch_data()
    current_key = f"{data['title']}|{data['date']}"

    # 讀取上次資料
    last_key = ""
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r", encoding="utf-8") as f:
            last_key = f.read().strip()

    if current_key != last_key:
        send_to_discord(data)
        with open(LAST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_key)
        print("有新資訊，已發送！")
    else:
        print("沒有新資料。")

if __name__ == "__main__":
    main()
