"""DashboardPage — Page Object untuk halaman utama setelah login."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config.settings import ACTION_TIMEOUT, LOGIN_URL


class Locators:
    # Tombol profile di topbar (untuk buka dropdown)
    PROFILE_BTN = (By.CSS_SELECTOR, "li.profile-item a")
    # Tombol Sign Out — pakai onclick karena ID JSF bisa berubah
    SIGN_OUT    = (By.CSS_SELECTOR, "a[onclick*='doLogoutTeam']")


class DashboardPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait   = WebDriverWait(driver, ACTION_TIMEOUT)

    def is_loaded(self) -> bool:
        """Cek apakah sudah di dashboard (bukan di halaman login)."""
        return LOGIN_URL not in self.driver.current_url

    def logout(self):
        """Klik profile → tunggu dropdown muncul → klik Sign Out → validasi redirect."""
        import time

        for attempt in range(1, 4):
            try:
                # Klik profile untuk buka dropdown
                self.wait.until(EC.element_to_be_clickable(Locators.PROFILE_BTN)).click()

                # Tunggu Sign Out benar-benar visible di DOM (dropdown terbuka)
                sign_out = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(Locators.SIGN_OUT))

                # Klik via JavaScript untuk hindari overlap elemen lain
                self.driver.execute_script("arguments[0].click();", sign_out)

                # Validasi redirect ke login page
                WebDriverWait(self.driver, 15).until(
                    EC.url_contains("faces-redirect=true"))
                print("[INFO] Logout berhasil.")
                return
            except TimeoutException:
                print(f"[WARN] Logout attempt {attempt} gagal, coba lagi...")
                time.sleep(1)

        print(f"[ERROR] Logout gagal setelah 3 percobaan. URL: {self.driver.current_url}")
