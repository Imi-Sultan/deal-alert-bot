import requests
import time

WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK"
DISCOUNT_TRIGGER = 30
CHECK_INTERVAL = 300

API_URL = "https://www.onedayonly.co.za/api/products?type=TODAYS_DEALS"

sent_deals = set()

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except:
        pass

def format_price(x):
    return f"R{x:,.0f}"

def fetch_deals():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Fetch error:", e)
        return []

def check_deals():
    products = fetch_deals()
    if not products:
        return

    for item in products:
        try:
            title = f"{item.get('brand','')} {item.get('name','')}".strip()

            was_price = item["retailPrice"]["value"]
            now_price = item["price"]["value"]
            discount = round((1 - now_price / was_price) * 100, 2)

            url = "https://www.onedayonly.co.za" + item["url"]

            uid = f"{item['id']}-{now_price}"
            if uid in sent_deals:
                continue

            if discount >= DISCOUNT_TRIGGER:
                sent_deals.add(uid)

                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"Now: {format_price(now_price)}\n"
                    f"Was: {format_price(was_price)}\n"
                    f"{url}"
                )
                send(msg)

        except Exception as e:
            print("Parse error:", e)
            continue

send(f"🟢 ODO API Monitor started ({DISCOUNT_TRIGGER}%+)")

while True:
    check_deals()
    time.sleep(CHECK_INTERVAL)
