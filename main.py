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

    # Updated selector for new ODO layout
    tiles = soup.select("div.measure-this.unbxdanalyticsProduct")

    for tile in tiles:
        try:
            # Product link
            link = tile.find("a")["href"]
            if link.startswith("/"):
                link = "https://www.onedayonly.co.za" + link

            # Brand and name
            brand = tile.select_one("h2.css-1jtyjh7")
            name = tile.select_one("h2.css-khw29m")

            title = ""
            if brand:
                title += brand.text.strip() + " "
            if name:
                title += name.text.strip()

            # Prices
            price_now = tile.select_one("h2.highlightOnHover")
            price_was = tile.select_one("h2.css-15d1jmj")

            if not price_now or not price_was:
                continue

            p_now = float(price_now.text.replace("R", "").replace(",", "").strip())
            p_was = float(price_was.text.replace("R", "").replace(",", "").strip())

            discount = round((1 - p_now / p_was) * 100, 2)

            # Unique ID prevents duplicates
            unique_id = f"{title}-{p_now}"

            if discount >= DISCOUNT_TRIGGER and unique_id not in sent_deals:
                sent_deals.add(unique_id)

                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"Now: R{p_now:,}\n"
                    f"Was: R{p_was:,}\n"
                    f"{link}"
                )

                send_discord_message(msg)

        except Exception as e:
            send_discord_message(f"Error parsing item: {e}")

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
