import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHECK_INTERVAL = 300  # 5 minutes
DISCOUNT_TRIGGER = 10

sent_deals = set()

def send_discord_message(msg):
    data = {"content": msg}
    requests.post(WEBHOOK_URL, json=data)

def fetch_page():
    r = requests.get("https://www.onedayonly.co.za", timeout=10)
    return BeautifulSoup(r.text, "html.parser")

def check_deals():
    global sent_deals
    soup = fetch_page()
    tiles = soup.find_all("div", {"class": "daily-deal-tile"})

    for tile in tiles:
        try:
            title = tile.find("h3").text.strip()
            price_now = tile.find("span", class_="price").text.strip()
            price_was = tile.find("span", class_="was-price").text.strip()
            link = "https://www.onedayonly.co.za" + tile.find("a")["href"]

            p_now = float(price_now.replace("R", "").replace(",", ""))
            p_was = float(price_was.replace("R", "").replace(",", ""))
            discount = round((1 - p_now / p_was) * 100, 2)

            unique_id = title + price_now

            if discount >= DISCOUNT_TRIGGER and unique_id not in sent_deals:
                sent_deals.add(unique_id)
                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"{price_now} (was {price_was})\n"
                    f"{link}"
                )
                send_discord_message(msg)

        except:
            pass

def main():
    send_discord_message("🟢 Deal monitor started (OneDayOnly 85%+)")
    while True:
        try:
            check_deals()
        except Exception as e:
            send_discord_message(f"⚠️ Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
