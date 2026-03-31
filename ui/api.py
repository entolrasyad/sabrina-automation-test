"""
ui/api.py — HTTP bot API calls and Selenium login flow
"""

import re
import json
import time
import requests
from urllib.parse import unquote_plus

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils.driver_factory import create_driver
from config.settings import LOGIN_URL, BASE_URL, ACTION_TIMEOUT
from config import credential_manager


# ── HTTP API ────────────────────────────────────────────────────────────────────

def _extract_cdata_text(xml: str, update_id: str) -> str:
    pattern = rf'<update id="{re.escape(update_id)}"[^>]*>.*?<!\[CDATA\[.*?>(.*?)</label>'
    m = re.search(pattern, xml, re.DOTALL)
    return m.group(1).strip() if m else ""


def call_bot_api(cookie_str: str, view_state: str, user_says: str) -> dict:
    try:
        resp = requests.post(
            f"{BASE_URL}/dolphin/bot",
            headers={
                "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
                "Accept":           "application/xml, text/xml, */*; q=0.01",
                "Accept-Language":  "en-US,en;q=0.9",
                "Accept-Encoding":  "gzip, deflate, br, zstd",
                "Referer":          f"{BASE_URL}/dolphin/bot",
                "Origin":           BASE_URL,
                "Connection":       "keep-alive",
                "Cookie":           cookie_str,
                "Faces-Request":    "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type":     "application/x-www-form-urlencoded; charset=UTF-8",
                "Pragma":           "no-cache",
                "Cache-Control":    "no-cache",
            },
            data={
                "javax.faces.partial.ajax":    "true",
                "javax.faces.source":          "formBot:j_id_ns",
                "javax.faces.partial.execute": "formBot:userSays formBot:emulatorModule formBot:emulatorContext formBot:j_id_ns",
                "javax.faces.partial.render":  "formBot:userSays formBot:message formBot:lblScore formBot:lblDialog formBot:suggestionScorePanel formBot:emulatorModule formBot:growl",
                "formBot:j_id_ns":             "formBot:j_id_ns",
                "formBot:userSays":            user_says,
                "formBot:emulatorModule":      "",
                "formBot:emulatorContext":     "",
                "javax.faces.ViewState":       view_state,
            },
            verify=False,
            timeout=30,
        )
        score  = _extract_cdata_text(resp.text, "formBot:lblScore")
        dialog = _extract_cdata_text(resp.text, "formBot:lblDialog")
        return {"dialog": dialog, "score": score}
    except requests.exceptions.Timeout:
        return {"dialog": "ERROR: Request timeout", "score": ""}
    except requests.exceptions.ConnectionError as e:
        return {"dialog": f"ERROR: Connection error — {e}", "score": ""}


# ── Selenium Login ──────────────────────────────────────────────────────────────

def selenium_login(on_progress, on_done, on_error) -> None:
    """
    Runs Selenium login flow in a background thread.
    Callbacks must schedule UI updates via app.after(0, ...).
    """
    driver = None
    try:
        on_progress("Proses Login sedang berjalan. Step (1/9)") # on_progress("Memulai browser...")
        driver = create_driver()
        wait = WebDriverWait(driver, ACTION_TIMEOUT)

        on_progress("Proses Login sedang berjalan. Step (2/9)") # on_progress("Membuka halaman login...")
        creds = credential_manager.load()
        driver.get(LOGIN_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:emailDisplay"))).send_keys(creds["username"])
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:password"))).send_keys(creds["password"])
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:btnDoLogin"))).click()

        on_progress("Proses Login sedang berjalan. Step (3/9)") # on_progress("Menunggu redirect setelah login...")
        try:
            WebDriverWait(driver, 15).until(lambda d: LOGIN_URL not in d.current_url)
        except TimeoutException:
            growl = driver.find_elements(By.CSS_SELECTOR, ".ui-growl-item")
            msg = growl[0].text if growl else "Timeout — credentials salah atau session aktif"
            driver.quit()
            on_error(f"Login gagal: {msg}")
            return

        on_progress("Proses Login sedang berjalan. Step (4/9)") # on_progress("Mengambil cookie session...")
        cookies    = {c["name"]: c["value"] for c in driver.get_cookies()}
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())

        on_progress("Proses Login sedang berjalan. Step (5/9)") # on_progress("Navigasi ke Bot Settings...")
        wait_menu = WebDriverWait(driver, 5)
        try:
            wait_menu.until(EC.element_to_be_clickable((By.ID, "menuform:mainMenu_7"))).click()
            submenu_id = "menuform:mainMenu_7_0"
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.ID, "menuform:mainMenu_4"))).click()
            submenu_id = "menuform:mainMenu_4_0"
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (6/9)") # on_progress("Masuk ke halaman /dolphin/bot...")
        wait.until(EC.element_to_be_clickable((By.ID, submenu_id))).click()
        WebDriverWait(driver, 15).until(lambda d: "/dolphin/bot" in d.current_url)
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (7/9)") # on_progress("Klik tombol Emulator...")
        wait.until(EC.element_to_be_clickable((By.ID, "formBot:bot:4:btnEmulator"))).click()
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (8/9)") # on_progress("Mengirim pesan warm-up untuk mendapatkan ViewState...")
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "formBot:userSays")))
        textarea.clear()
        textarea.send_keys("test")
        time.sleep(0.5)
        driver.get_log("performance")

        wait.until(EC.element_to_be_clickable((By.ID, "formBot:j_id_ns"))).click()
        time.sleep(3)

        on_progress("Proses Login sedang berjalan. Step (9/9)") # on_progress("Mengekstrak ViewState dari network log...")
        view_state = ""
        for entry in driver.get_log("performance"):
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") == "Network.requestWillBeSent":
                req = msg["params"].get("request", {})
                if "/dolphin/" in req.get("url", "") and req.get("method") == "POST":
                    for pair in req.get("postData", "").split("&"):
                        if "=" in pair:
                            k, _, v = pair.partition("=")
                            if unquote_plus(k) == "javax.faces.ViewState":
                                view_state = unquote_plus(v)
                                break
                if view_state:
                    break

        if not view_state:
            driver.quit()
            on_error("ViewState tidak ditemukan. Coba jalankan Login lagi.")
            return

        on_done(driver, cookie_str, view_state)

    except Exception as exc:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        on_error(str(exc))
