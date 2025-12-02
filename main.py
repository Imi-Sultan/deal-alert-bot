import requests
import time
import json
from datetime import datetime

WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK"
DISCOUNT_TRIGGER = 30   # change to 85 later
CHECK_INTERVAL = 300    # 5 minutes

sent_deals = set()

API_URL = "https://www.onedayonly.co.za/api/products/today"

def fetch_products():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Fetch error:", e)
        return []

def send_discord(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except:
        pass

def format_price(value):
    return f"R{value:,.0f}"

def check_deals():
    global sent_deals

    products = fetch_products()
    if not products:
        return

    for item in products:

        try:
            name = item.get("name") or "Unknown"
            brand = item.get("brand") or ""
            title = f"{brand} {name}".strip()

            was_price = item["retailPrice"]["value"]
            now_price = item["price"]["value"]

            if was_price <= 0:
                continue

            discount = round((1 - (now_price / was_price)) * 100, 2)

            # avoid duplicates
            uid = f"{item['id']}-{now_price}"
            if uid in sent_deals:
                continue

            if discount >= DISCOUNT_TRIGGER:

                url = "https://www.onedayonly.co.za" + item["url"]
                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"Now: {format_price(now_price)}\n"
                    f"Was: {format_price(was_price)}\n"
                    f"{url}"
                )

                send_discord(msg)
                sent_deals.add(uid)

        except Exception as e:
            print("Parse error:", e)
            continue


# -------- MAIN LOOP ----------
send_discord(f"🟢 ODO Deal Monitor started ({DISCOUNT_TRIGGER}%+)")

while True:
    check_deals()
    time.sleep(CHECK_INTERVAL)
