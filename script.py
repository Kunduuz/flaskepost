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


def normalize_shift(text):
    # 👉 macht aus " 12.04   14:00 - 22:00 " → sauberen String
    return " ".join(text.split()).strip()


def get_shifts(page):
    shifts = page.query_selector_all(".offer-item-date-time")

    results = []
    for s in shifts:
        text = s.inner_text()
        results.append(normalize_shift(text))

    return results


def find_login_input(page, selectors):
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() and locator.first.is_visible():
            return locator.first
    return None


def main():
    if not EMAIL or not PASSWORD:
        raise ValueError("LOGIN_EMAIL and LOGIN_PASSWORD environment variables must be set")
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("BOT_TOKEN and CHAT_ID environment variables must be set")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://portal.flaschenpost.de/")
        page.wait_for_load_state("networkidle")

        username_selectors = [
            'input[type="email"]',
            'input[type="text"]',
            'input[name*="email"]',
            'input[name*="user"]',
            'input[name*="login"]',
            'input[name*="Mitarbeiter"]',
        ]

        password_selectors = [
            'input[type="password"]',
            'input[name*="password"]',
            'input[name*="Passwort"]',
        ]

        username_input = find_login_input(page, username_selectors)
        password_input = find_login_input(page, password_selectors)

        if not username_input or not password_input:
            raise RuntimeError("Login-Felder wurden nicht gefunden.")

        username_input.fill(EMAIL)
        password_input.fill(PASSWORD)

        submit_button = page.locator('button[type="submit"], button.blue.button').first
        if submit_button.count() and submit_button.is_visible():
            submit_button.click()
        else:
            page.keyboard.press("Enter")

        page.wait_for_timeout(2000)
        page.wait_for_selector(".offer-item-date-time", timeout=15000)

        shifts = get_shifts(page)

        # =========================
        # 🧠 SMART CHANGE DETECTION
        # =========================

        try:
            with open("shifts.txt", "r") as f:
                old = set(f.read().splitlines())
        except:
            old = set()

        new = set(shifts)

        # 👉 echte neue Schichten (nicht nur set diff)
        diff = [s for s in new if s not in old]

        # =========================
        # 📩 TELEGRAM
        # =========================

        if diff:
            msg = "🚐 Neue Schichten scurr scurr:\n\n" + "\n\n".join(diff)
            send_telegram(msg)

        # =========================
        # 💾 SPEICHERN
        # =========================

        with open("shifts.txt", "w") as f:
            f.write("\n".join(new))

        browser.close()


if __name__ == "__main__":
    main()
