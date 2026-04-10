import os
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

EMAIL = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

def get_shifts(page):
    # 👉 HIER ggf. anpassen!
    shifts = page.query_selector_all(".shift-card")

    results = []
    for s in shifts:
        text = s.inner_text()
        results.append(text.strip())

    return results

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://portal.flaschenpost.de/")

        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)

        shifts = get_shifts(page)

        try:
            with open("shifts.txt", "r") as f:
                old = set(f.read().splitlines())
        except:
            old = set()

        new = set(shifts)
        diff = new - old

        if diff:
            msg = "🚐 Neue Schichten:\n\n" + "\n\n".join(diff)
            send_telegram(msg)

        with open("shifts.txt", "w") as f:
            f.write("\n".join(new))

        browser.close()

if __name__ == "__main__":
    main()
