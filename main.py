import os
import discord
from discord import SyncWebhook, Embed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    driver = webdriver.Chrome(options=options)

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(8)  # 確保載入

    result = {}
    print("頁面載入完成:", driver.title)

    try:
        # 標題：第一個 h3
        title = driver.find_element(By.TAG_NAME, "h3").text.strip()
        result['title'] = title
        print("找到標題:", title)
    except:
        result['title'] = "未找到標題"
        print("標題失敗")

    try:
        # 日期：抓 h3 之後的下一個 sibling 元素（通常是日期的 div 或 p）
        # 用 XPath 更精準：h3 後的第一個包含數字的文字，或直接抓第二個 div
        date_element = driver.find_element(By.XPATH, "//h3/following-sibling::*[contains(text(), '/')]")
        result['date'] = date_element.text.strip()
        if not result['date']:  # 備用：抓包含 2026 的文字
            date_element = driver.find_element(By.XPATH, "//h3/parent::*//following-sibling::*[contains(text(), '2026')]")
            result['date'] = date_element.text.strip()
        print("找到日期:", result['date'])
    except:
        result['date'] = "未知日期"
        print("日期抓取失敗，使用未知")

    try:
        # 詳情連結：抓第一個包含 /bulletin/ 的 a（修正不加重複域名）
        link = driver.find_element(By.CSS_SELECTOR, "a[href*='/bulletin/']")
        full_url = link.get_attribute("href")
        if full_url.startswith("/"):  # 如果是相對路徑
            full_url = "https://tw.nexon.com" + full_url
        result['more_url'] = full_url
        print("找到詳情 URL:", result['more_url'])
    except:
        result['more_url'] = url
        print("URL 失敗，使用列表頁")

    # 圖片：這則公告沒圖，留空
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
    print("已成功發送訊息到 Discord")

def main():
    data = fetch_data()
    current_key = f"{data['title']}|{data['date']}"

    last_key = ""
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r", encoding="utf--8") as f:
            last_key = f.read().strip()

    print(f"目前 key: {current_key}")
    print(f"上次 key: {last_key}")

    if current_key != last_key and "未找到" not in current_key and "未知日期" not in current_key:
        send_to_discord(data)
        with open(LAST_DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_key)
        print("檢測到新公告，已發送並更新檔案！")
    else:
        print("無新公告或日期未知，未發送。")

if __name__ == "__main__":
    main()
