import os
import discord
from discord import SyncWebhook, Embed
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
LAST_DATA_FILE = "last_data.txt"

def fetch_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=zh-TW")

    driver = webdriver.Chrome(options=options)  # 用 setup-chromedriver 安裝的

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(8)

    result = {}
    print("頁面載入完成:", driver.title)

    try:
        # 標題：抓第一個 h3（最新公告）
        title = driver.find_element(By.TAG_NAME, "h3").text.strip()
        result['title'] = title
        print("找到標題:", title)
    except:
        result['title'] = "未找到標題"
        print("標題失敗")

    try:
        # 日期：通常在 h3 旁邊的小文字或 parent 元素（這裡假設在同層，實際可調整）
        # 備用：找包含數字的文字，或 parent 的 span
        date = driver.find_element(By.CSS_SELECTOR, "h3 ~ span, h3 + span, .date").text.strip()
        result['date'] = date
        print("找到日期:", date)
    except:
        result['date'] = "未知日期"
        print("日期失敗，使用未知")

    try:
        # 詳情連結：抓第一個包含 /bulletin/ 的 a
        link = driver.find_element(By.CSS_SELECTOR, "a[href*='/bulletin/']")
        result['more_url'] = "https://tw.nexon.com" + link.get_attribute("href")
        print("找到詳情 URL:", result['more_url'])
    except:
        result['more_url'] = url

    # 圖片：這則公告沒圖，跳過或設空
    result['img_url'] = ""

    driver.quit()
    return result

def send_to_discord(data):
    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    embed = Embed(
        title=data['title'],
        description=f"日期： {data['date']}\n[查看詳情]({data['more_url']})",
        color=discord.Color.green()
    )
    webhook.send(embed=embed)
    print("已發送訊息")

def main():
    data = fetch_data()
    current_key = f"{data['title']}|{data['date']}"

    last_key = ""
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r", encoding="utf-8") as f:
            last_key = f.read().strip()

    print(f"目前 key: {current_key}")
    print(f"上次 key: {last_key}")

    if current_key != last_key and "未找到" not in current_key:
        send_to_discord(data)
        with open(LAST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_key)
        print("有新公告，已發送並更新檔案！")
    else:
        print("無新公告，未發送。")

if __name__ == "__main__":
    main()
