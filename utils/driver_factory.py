"""
DriverFactory — membuat instance Chrome WebDriver.
Dipakai oleh conftest.py (fixture) dan runner.py (GUI mode).
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import HEADLESS, WINDOW_SIZE, SESSION_DIR


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

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    driver.set_page_load_timeout(30)

    return driver
