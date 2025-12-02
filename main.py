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

    # New ODO product selector
    tiles = soup.select("div.measure-this.unbxdanalyticsProduct")

    for tile in tiles:
        try:
            # ---------- PRODUCT LINK ----------
            a_tag = tile.find("a")
            if not a_tag or not a_tag.get("href"):
                continue
            link = a_tag["href"]
            if link.startswith("/"):
                link = "https://www.onedayonly.co.za" + link

            # ---------- TITLE ----------
            brand_tag = tile.select_one("h2.css-1jtyjh7")
            name_tag = tile.select_one("h2.css-khw29m")

            if not brand_tag and not name_tag:
                # fallback: use alt text from image
                img_tag = tile.find("img")
                title = img_tag["alt"] if img_tag else "Unknown Item"
            else:
                brand = brand_tag.text.strip() if brand_tag else ""
                name = name_tag.text.strip() if name_tag else ""
                title = f"{brand} {name}".strip()

            # ---------- PRICES ----------
            price_now_tag = tile.select_one("h2.highlightOnHover")
            price_was_tag = tile.select_one("h2.css-15d1jmj")

            if not price_now_tag or not price_was_tag:
                continue  # skip incomplete tiles

            p_now = float(price_now_tag.text.replace("R", "").replace(",", ""))
            p_was = float(price_was_tag.text.replace("R", "").replace(",", ""))

            if p_was <= 0:
                continue

            discount = round((1 - p_now / p_was) * 100, 2)

            # ---------- UNIQUE ID ----------
            unique_id = f"{title}-{p_now}"

            # ---------- SEND ALERT ----------
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
            # Only send errors ONCE per cycle (optional improvement)
            print(f"DEBUG ERROR: {e}")
            continue

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
