import html, json, os, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from matcher import classify

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
ADS_FILE = ROOT / "docs" / "ads.json"

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT = os.environ.get("TG_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "uk-UA,uk;q=0.9,ru;q=0.8",
}

def fetch(query):
    url = f"{CFG['domain']}/api/v1/offers/"
    params = {"offset": 0, "limit": 40, "query": query, "sort_by": "created_at:desc"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json().get("data", [])
            print(f"[{query}] HTTP {r.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[{query}] error: {e}", file=sys.stderr)
        time.sleep(2 * (attempt + 1))
    return []

def get_price(offer):
    for p in offer.get("params", []):
        if p.get("key") == "price":
            v = p.get("value", {})
            return v.get("value"), v.get("currency", "UAH")
    return None, "UAH"

def to_uah(price, cur):
    # грубая конвертация для сравнения с минимумами/бюджетом; поправь курс при желании
    rates = {"UAH": 1, "USD": 41, "EUR": 45}
    return price * rates.get(cur, 1) if price is not None else None

def photo(offer):
    ph = offer.get("photos") or []
    if ph:
        return ph[0].get("link", "").replace("{width}", "300").replace("{height}", "300")
    return ""

def send_tg(ad):
    if not TG_TOKEN or not TG_CHAT:
        return
    price = f"{ad['price']} {ad['currency']}" if ad["price"] is not None else "цена не указана"
    text = (f"📱 <b>{html.escape(ad['group'])}</b>\n"
            f"{html.escape(ad['title'])}\n💰 {price}\n"
            f"📍 {html.escape(ad.get('city') or '')}\n{ad['url']}")
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print("telegram error:", e, file=sys.stderr)

def main():
    stored = []
    first_run = True
    if ADS_FILE.exists():
        try:
            stored = json.loads(ADS_FILE.read_text(encoding="utf-8"))
            first_run = len(stored) == 0
        except Exception:
            stored = []
    seen = {str(a["id"]) for a in stored}

    now = datetime.now(timezone.utc)
    window = timedelta(minutes=CFG["notify_window_minutes"])
    new_ads = []

    for q in CFG["queries"]:
        for offer in fetch(q):
            oid = str(offer["id"])
            if oid in seen:
                continue
            title = offer.get("title", "")
            group = classify(title, offer.get("description", ""))
            if not group:
                continue
            price, cur = get_price(offer)
            uah = to_uah(price, cur)
            if uah is not None:
                if uah < CFG["min_price"].get(group, 0):
                    continue
                if CFG["max_price"] is not None and uah > CFG["max_price"]:
                    continue
            ad = {
                "id": oid, "title": title, "url": offer.get("url", ""),
                "group": group, "price": price, "currency": cur, "price_uah": uah,
                "city": (offer.get("location", {}).get("city") or {}).get("name", ""),
                "created": offer.get("created_time", ""), "photo": photo(offer),
            }
            seen.add(oid)
            new_ads.append(ad)
        time.sleep(0.5)

    if not new_ads:
        print("Новых объявлений нет")
        return

    for ad in new_ads:
        if first_run:
            continue  # при первом запуске только наполняем сайт, без спама в Telegram
        try:
            created = datetime.fromisoformat(ad["created"])
            if now - created > window:
                continue
        except Exception:
            pass
        send_tg(ad)

    all_ads = new_ads + stored
    all_ads.sort(key=lambda a: a.get("created", ""), reverse=True)
    all_ads = all_ads[: CFG["keep_ads"]]
    ADS_FILE.write_text(json.dumps(all_ads, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Добавлено: {len(new_ads)}")

if __name__ == "__main__":
    main()
