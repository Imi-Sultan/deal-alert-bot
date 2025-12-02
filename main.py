import requests
import time

WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK"
DISCOUNT_TRIGGER = 10
CHECK_INTERVAL = 300  # 5 min

sent_deals = set()

GRAPHQL_URL = "https://www.onedayonly.co.za/graphql"

QUERY = {
    "query": """
    query {
      productsToday {
        id
        name
        brand
        url
        price { value }
        retailPrice { value }
        saving { percent }
      }
    }
    """
}

def fetch_products():
    try:
        response = requests.post(GRAPHQL_URL, json=QUERY, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["data"]["productsToday"]
    except Exception as e:
        print("Fetch error:", e)
        return []

def send_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except:
        pass

def format_price(value):
    return f"R{value:,.0f}"

def check_deals():
    global sent_deals

    products = fetch_products()
    if not products:
        return

    for p in products:
        try:
            name = p["name"]
            brand = p["brand"] or ""
            title = f"{brand} {name}".strip()

            now_price = p["price"]["value"]
            was_price = p["retailPrice"]["value"]

            if was_price <= 0:
                continue

            discount = round((1 - now_price / was_price) * 100, 2)

            uid = f"{p['id']}-{now_price}"
            if uid in sent_deals:
                continue

            if discount >= DISCOUNT_TRIGGER:
                link = "https://www.onedayonly.co.za" + p["url"]

                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"Now: {format_price(now_price)}\n"
                    f"Was: {format_price(was_price)}\n"
                    f"{link}"
                )

                send_discord(msg)
                sent_deals.add(uid)

        except Exception as e:
            print("Parse error:", e)
            continue


# ------------ MAIN LOOP -------------
send_discord(f"🟢 ODO Deal Monitor started ({DISCOUNT_TRIGGER}%+ GraphQL)")

while True:
    check_deals()
    time.sleep(CHECK_INTERVAL)
