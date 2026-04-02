"""
DriverFactory — membuat instance Chrome WebDriver.
Dipakai oleh conftest.py (fixture) dan runner.py (GUI mode).

Menggunakan Selenium built-in selenium-manager (Selenium 4.6+)
yang otomatis download ChromeDriver sesuai versi Chrome & arsitektur OS.
Tidak butuh webdriver-manager.
"""

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from config.settings import HEADLESS, WINDOW_SIZE, SESSION_DIR

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WA_SESSION_DIR = os.path.join(_PROJECT_ROOT, "session", "whatsapp")


def _make_driver(options: Options) -> webdriver.Chrome:
    """
    Buat Chrome driver. Selenium 4.6+ akan otomatis cari/download
    ChromeDriver yang sesuai via selenium-manager — tidak perlu Service manual.
    """
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as e:
        # Jika selenium-manager gagal, coba dengan Service kosong (fallback)
        raise e


def create_driver() -> webdriver.Chrome:
    """Chrome untuk login & test bot API."""
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")

    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    if SESSION_DIR:
        options.add_argument(f"--user-data-dir={SESSION_DIR}")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = _make_driver(options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    driver.set_page_load_timeout(30)
    return driver


def create_wa_driver() -> webdriver.Chrome:
    """Chrome terpisah untuk WhatsApp Web. Session disimpan di session/whatsapp/."""
    os.makedirs(WA_SESSION_DIR, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={os.path.abspath(WA_SESSION_DIR)}")
    options.add_argument("--kiosk")
    options.add_argument("--window-position=-10000,-10000")
    options.add_argument("--disable-features=MediaQueryPrefersDarkMode")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = _make_driver(options)
    driver.set_page_load_timeout(30)
    return driver
