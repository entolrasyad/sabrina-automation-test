"""
DriverFactory — membuat instance Chrome WebDriver.
Dipakai oleh conftest.py (fixture) dan runner.py (GUI mode).
"""

import os
import sys
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import HEADLESS, WINDOW_SIZE, SESSION_DIR

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WA_SESSION_DIR = os.path.join(_PROJECT_ROOT, "session", "whatsapp")

# Deteksi arsitektur OS untuk force download ChromeDriver yang benar
_OS_TYPE = "win64" if (sys.platform == "win32" and sys.maxsize > 2**32) else \
           "win32" if sys.platform == "win32" else None


def _make_chromedriver_manager(force=False):
    kwargs = {"cache_valid_range": 0} if force else {}
    if _OS_TYPE:
        try:
            from webdriver_manager.core.os_manager import OperationSystemManager
            kwargs["os_system_manager"] = OperationSystemManager(_OS_TYPE)
        except Exception:
            pass
    return ChromeDriverManager(**kwargs)


def _install_driver(force=False):
    return Service(_make_chromedriver_manager(force).install())


def _clear_wdm_cache():
    wdm_cache = os.path.join(os.path.expanduser("~"), ".wdm")
    shutil.rmtree(wdm_cache, ignore_errors=True)


def create_driver() -> webdriver.Chrome:
    """
    Buat dan kembalikan Chrome WebDriver yang sudah dikonfigurasi.
    - SSL dev certificate di-bypass (ignore-certificate-errors)
    - Notifikasi browser dimatikan
    - Webdriver flag disembunyikan dari JS
    """
    options = Options()

    # Tampilan
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")

    # SSL — dev environment pakai self-signed cert
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")

    # Stabilitas
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    # Session (opsional)
    if SESSION_DIR:
        options.add_argument(f"--user-data-dir={SESSION_DIR}")

    # Sembunyikan automation flag
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Aktifkan performance log untuk network capture (CDP)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    try:
        service = _install_driver()
        driver  = webdriver.Chrome(service=service, options=options)
    except (WebDriverException, OSError):
        _clear_wdm_cache()
        service = _install_driver(force=True)
        driver  = webdriver.Chrome(service=service, options=options)

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
    options.add_argument("--kiosk")                          # fullscreen, hapus semua UI Chrome
    options.add_argument("--window-position=-10000,-10000")  # sembunyikan sebelum di-embed
    options.add_argument("--disable-features=MediaQueryPrefersDarkMode")  # paksa light mode
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        service = _install_driver()
        driver  = webdriver.Chrome(service=service, options=options)
    except (WebDriverException, OSError):
        _clear_wdm_cache()
        service = _install_driver(force=True)
        driver  = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(30)
    return driver
