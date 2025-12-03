import requests
from bs4 import BeautifulSoup
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1445097186374193244/kSs02vq-hJTh85ZQuPDiMKaEAp1l2mS7SzFVNAeELZ3dhMfcpgNb1LYjbq0E3VBzOB8T"
DISCOUNT_TRIGGER = 75
CHECK_INTERVAL = 300

sent = set()

URL = "https://www.onedayonly.co.za/"

def send(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def fetch():
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("Fetch error:", e)
        return None

def get_text_num(el):
    return float(el.text.replace("R", "").replace(",", "").strip())

def check_deals():
    soup = fetch()
    if not soup:
        return

    tiles = soup.select("div.measure-this.unbxdanalyticsProduct")

    print(f"Found {len(tiles)} tiles")

    for t in tiles:
        try:
            # URL
            a = t.find("a")
            if not a or not a.get("href"):
                continue
            link = a["href"]
            if link.startswith("/"):
                link = "https://www.onedayonly.co.za" + link

            # Brand + name (fallbacks included)
            brand = t.select_one("h2.css-1jtyjh7, h2.css-3qnnaq")
            name  = t.select_one("h2.css-khw29m, h2.css-13w51ah")

            if brand or name:
                title = f"{brand.text.strip() if brand else ''} {name.text.strip() if name else ''}".strip()
            else:
                img = t.find("img")
                title = img["alt"] if img else "Unknown Product"

            # Price now (multiple class variants)
            price_now = t.select_one("h2.highlightOnHover, h2.css-1o5ix5z")
            price_was = t.select_one("h2.css-15d1jmj, h2.css-i84nsw")

            if not price_now or not price_was:
                continue

            p_now = get_text_num(price_now)
            p_was = get_text_num(price_was)

            if p_was <= 0:
                continue

            discount = round((1 - p_now / p_was) * 100, 2)

            uid = f"{title}-{p_now}"
            if uid in sent:
                continue

            if discount >= DISCOUNT_TRIGGER:
                sent.add(uid)
                msg = (
                    f"🔥 **{discount}% OFF!**\n"
                    f"**{title}**\n"
                    f"Now: R{p_now:,}\n"
                    f"Was: R{p_was:,}\n"
                    f"{link}"
                )
                send(msg)

        except Exception as e:
            print("Parse error:", e)

send(f"🟢 ODO HTML Monitor started ({DISCOUNT_TRIGGER}%+)")

while True:
    check_deals()
    time.sleep(CHECK_INTERVAL)
