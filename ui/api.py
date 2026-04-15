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


def _parse_last_bot_messages(xml: str) -> list:
    """
    Ambil teks balasan bot dari exchange TERAKHIR di formBot:message.
    Mengembalikan list string — satu elemen per bubble.
    """
    m = re.search(r'<update id="formBot:message"[^>]*>(.*?)</update>', xml, re.DOTALL)
    if not m:
        return []
    html = re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))

    # Pisahkan tiap exchange — speech-bubble-left menandai awal turn baru
    # Bagian setelah left-bubble TERAKHIR = respons bot terkini
    parts = re.split(r'<div class="speech-bubble-left', html)
    if len(parts) < 2:
        return []
    last_section = parts[-1]

    # Kumpulkan semua span di dalam speech-bubble-right
    spans = re.findall(
        r'<div class="speech-bubble-right[^>]*>.*?<span[^>]*>(.*?)</span>',
        last_section, re.DOTALL,
    )

    results = []
    for raw in spans:
        text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = (text.replace("&amp;", "&").replace("&lt;", "<")
                    .replace("&gt;", ">").replace("&nbsp;", " ")
                    .replace("\u201a", ","))
        text = re.sub(r"\*([^*]+)\*", r"\1", text)   # hapus *bold* marker
        text = text.strip()
        if text:
            results.append(text)
    return results


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
        score    = _extract_cdata_text(resp.text, "formBot:lblScore")
        dialog   = _extract_cdata_text(resp.text, "formBot:lblDialog")
        messages = _parse_last_bot_messages(resp.text)
        return {"dialog": dialog, "score": score, "messages": messages}
    except requests.exceptions.Timeout:
        return {"dialog": "ERROR: Request timeout", "score": "", "messages": []}
    except requests.exceptions.ConnectionError as e:
        return {"dialog": f"ERROR: Connection error — {e}", "score": "", "messages": []}


# ── Selenium Login ──────────────────────────────────────────────────────────────

def _selenium_login_impl(username: str, password: str,
                         on_progress, on_done, on_error) -> None:
    driver = None
    try:
        on_progress("Proses Login sedang berjalan. Step (1/9)")
        driver = create_driver()
        wait = WebDriverWait(driver, ACTION_TIMEOUT)

        on_progress("Proses Login sedang berjalan. Step (2/9)")
        driver.get(LOGIN_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:emailDisplay"))).send_keys(username)
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:password"))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, "formLogin:btnDoLogin"))).click()

        on_progress("Proses Login sedang berjalan. Step (3/9)")
        try:
            WebDriverWait(driver, 15).until(lambda d: LOGIN_URL not in d.current_url)
        except TimeoutException:
            growl = driver.find_elements(By.CSS_SELECTOR, ".ui-growl-item")
            msg = growl[0].text if growl else "Timeout — credentials salah atau session aktif"
            driver.quit()
            on_error(f"Login gagal: {msg}")
            return

        on_progress("Proses Login sedang berjalan. Step (4/9)")
        cookies    = {c["name"]: c["value"] for c in driver.get_cookies()}
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())

        on_progress("Proses Login sedang berjalan. Step (5/9)")
        wait_menu = WebDriverWait(driver, 5)
        try:
            wait_menu.until(EC.element_to_be_clickable((By.ID, "menuform:mainMenu_7"))).click()
            submenu_id = "menuform:mainMenu_7_0"
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.ID, "menuform:mainMenu_4"))).click()
            submenu_id = "menuform:mainMenu_4_0"
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (6/9)")
        wait.until(EC.element_to_be_clickable((By.ID, submenu_id))).click()
        WebDriverWait(driver, 15).until(lambda d: "/dolphin/bot" in d.current_url)
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (7/9)")
        wait.until(EC.element_to_be_clickable((By.ID, "formBot:bot:4:btnEmulator"))).click()
        time.sleep(1)

        on_progress("Proses Login sedang berjalan. Step (8/9)")
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "formBot:userSays")))
        textarea.clear()
        textarea.send_keys("test")
        time.sleep(0.5)
        driver.get_log("performance")

        wait.until(EC.element_to_be_clickable((By.ID, "formBot:j_id_ns"))).click()
        time.sleep(3)

        on_progress("Proses Login sedang berjalan. Step (9/9)")
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


def selenium_login(on_progress, on_done, on_error) -> None:
    """Login menggunakan credentials dari credential_manager (akun utama)."""
    creds = credential_manager.load()
    _selenium_login_impl(creds["username"], creds["password"],
                         on_progress, on_done, on_error)


def selenium_login_with_creds(username: str, password: str,
                               on_progress, on_done, on_error) -> None:
    """Login dengan credentials eksplisit (untuk additional workers)."""
    _selenium_login_impl(username, password, on_progress, on_done, on_error)
