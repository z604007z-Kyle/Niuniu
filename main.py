import os
import discord
from discord import SyncWebhook, Embed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]  # GitHub Actions 用環境變數
LAST_DATA_FILE = "last_data.txt"

def fetch_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")

    url = "https://tw.nexon.com/mh/zh/home/bulletin/0/"
    driver.get(url)
    time.sleep(8)

    result = {}
    print("頁面載入完成:", driver.title)

    try:
        title_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-title")
        result['title'] = title_element.text.strip()
        print("找到標題:", result['title'])
    except Exception as e:
        print("標題失敗:", str(e))
        result['title'] = "未找到目標標題"

    try:
        date_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-date")
        result['date'] = date_element.text.strip()
        print("找到日期:", result['date'])
    except Exception as e:
        print("日期失敗:", str(e))
        result['date'] = "未找到目標日期"

    try:
        wait = WebDriverWait(driver, 15)
        more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "morearrow__inner")))
        ActionChains(driver).move_to_element(more_button).click().perform()
        time.sleep(4)
        result['more_url'] = driver.current_url
        print("點擊 MORE 成功，詳情 URL:", result['more_url'])
    except Exception as e:
        print("點擊 MORE 失敗:", str(e))
        result['more_url'] = "未能獲取新網址"

    try:
        img_element = driver.find_element(By.CSS_SELECTOR, ".newslist__item-img")
        img_url = img_element.value_of_css_property("background-image")
        img_url = img_url.replace('url("', '').replace('")', '').strip()
        result['img_url'] = img_url
        print("找到圖片:", result['img_url'])
    except Exception as e:
        print("圖片失敗:", str(e))
        result['img_url'] = "未找到圖片 URL"

    driver.quit()
    return result

def send_to_discord(data):
    if not WEBHOOK_URL:
        print("錯誤：DISCORD_WEBHOOK_URL 未設定")
        return
    webhook = SyncWebhook.from_url(WEBHOOK_URL)  # 修正這裡！原本錯打成 WEBOOK_URL
    embed = Embed(
        title=data['title'],
        description=f"日期： {data['date']}\n{data['more_url']}",
        color=discord.Color.green()
    )
    if data['img_url'] != "未找到圖片 URL":
        embed.set_image(url=data['img_url'])
    webhook.send(embed=embed)
    print("訊息已成功發送到 Discord")

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
        print("有新資訊，已發送並更新檔案！")
    else:
        print("沒有新資料，未發送。")

if __name__ == "__main__":
    main()
