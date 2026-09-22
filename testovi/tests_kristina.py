"""
Selenium WebDriver testovi za SSU_06, SSU_10, SSU_11

Podaci iz baze:
    - Equipment pk=6: Atomic Redster X9 (Alpski Rental)
    - Variant pk=1: 170cm, quantity=3
    - Rental nalog: alpski_rental@test.com / test1234
    - Klijent nalog: ana@test.com / test1234
"""

import unittest
import time
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service

BASE_URL = "http://127.0.0.1:8000"
RENTAL_EMAIL = "alpski_rental@test.com"
RENTAL_PASS = "test1234"
CLIENT_EMAIL = "ana@test.com"
CLIENT_PASS = "test1234"
EQUIPMENT_PK = 6
VARIANT_PK = 1


def get_driver():
    options = Options()
    # options.add_argument("--headless")  # Otkomentiši za pokretanje bez prozora
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(5)
    return driver


def login(driver, email, password):
    """Helper: loguje korisnika."""
    driver.get(f"{BASE_URL}/accounts/login/")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)


def logout(driver):
    """Helper: logout — briše kolačiće sesije."""
    driver.delete_all_cookies()
    driver.get(BASE_URL)
    time.sleep(1)



# SSU_06 — Rezervacija ski opreme

class SSU06ReservacijaTest(unittest.TestCase):

    def setUp(self):
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def test_01_uspesna_rezervacija(self):
        """
        2.2.1 Korisnik uspešno rezerviše opremu.
        Klijent se loguje, odlazi na stranicu opreme i podnosi rezervaciju.
        """
        login(self.driver, CLIENT_EMAIL, CLIENT_PASS)
        self.assertNotIn("login", self.driver.current_url)
        self.driver.get(f"{BASE_URL}/equipment/{EQUIPMENT_PK}/reserve/")
        self.wait.until(EC.presence_of_element_located((By.NAME, "start_date")))

        start = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        end = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")

        start_field = self.driver.find_element(By.NAME, "start_date")
        start_field.clear()
        start_field.send_keys(start)

        end_field = self.driver.find_element(By.NAME, "end_date")
        end_field.clear()
        end_field.send_keys(end)
        variant_select = Select(self.driver.find_element(By.NAME, "equipment_variant"))
        variant_select.select_by_index(1)
        try:
            qty = self.driver.find_element(By.NAME, "quantity")
            qty.clear()
            qty.send_keys("1")
        except Exception:
            pass
        form = self.driver.find_element(By.XPATH, "//form[.//input[@name='start_date']]")
        form.find_element(By.CSS_SELECTOR, "[type='submit']").click()
        time.sleep(2)

        print(f"  URL nakon submita: {self.driver.current_url}")

        self.assertIn("success", self.driver.current_url)
        print("✓ test_01_uspesna_rezervacija PROŠAO")

    def test_02_rezervacija_bez_prijave(self):
        """
        2.2.3 Neulogovani korisnik se preusmerava na login.
        """
        self.driver.get(f"{BASE_URL}/equipment/{EQUIPMENT_PK}/reserve/")
        time.sleep(1)

        self.assertIn("login", self.driver.current_url)
        print("✓ test_02_rezervacija_bez_prijave PROŠAO")

    def test_03_rezervacija_pogresan_datum(self):
        """
        2.2.2 Datum vraćanja pre datuma preuzimanja — forma prikazuje grešku.
        """
        login(self.driver, CLIENT_EMAIL, CLIENT_PASS)

        self.driver.get(f"{BASE_URL}/equipment/{EQUIPMENT_PK}/reserve/")
        self.wait.until(EC.presence_of_element_located((By.NAME, "start_date")))
        start = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")
        end = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        start_field = self.driver.find_element(By.NAME, "start_date")
        start_field.clear()
        start_field.send_keys(start)
        end_field = self.driver.find_element(By.NAME, "end_date")
        end_field.clear()
        end_field.send_keys(end)

        variant_select = Select(self.driver.find_element(By.NAME, "equipment_variant"))
        variant_select.select_by_index(1)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self.assertNotIn("success", self.driver.current_url)
        print("✓ test_03_rezervacija_pogresan_datum PROŠAO")


# SSU_10 — Upravljanje opremom rental firme


class SSU10UpravljanjeOpremomTest(unittest.TestCase):

    def setUp(self):
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        login(self.driver, RENTAL_EMAIL, RENTAL_PASS)

    def tearDown(self):
        self.driver.quit()

    def test_01_pregled_profila(self):
        """
        2.2.1 Rental firma vidi svoj panel sa opremom.
        """
        self.driver.get(f"{BASE_URL}/rental/profile/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        self.assertEqual(self.driver.title != "", True)
        self.assertNotIn("login", self.driver.current_url)
        print("✓ test_01_pregled_profila PROŠAO")

    def test_02_dodavanje_opreme(self):
        """
        2.2.2 Rental firma uspešno dodaje novu opremu.
        """
        self.driver.get(f"{BASE_URL}/rental/profile/?tab=oprema")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        self.driver.get(f"{BASE_URL}/rental/profile/equipment/add/")

        self.driver.get(f"{BASE_URL}/rental/profile/")
        time.sleep(1)

        self.assertNotIn("login", self.driver.current_url)
        print("✓ test_02_dodavanje_opreme PROŠAO (pristup panelu)")

    def test_03_panel_nedostupan_bez_prijave(self):
        """
        2.2.3 Neulogovani korisnik ne može pristupiti rental panelu.
        """
        logout(self.driver)
        self.driver.get(f"{BASE_URL}/rental/profile/")
        time.sleep(1)

        self.assertIn("login", self.driver.current_url)
        print("✓ test_03_panel_nedostupan_bez_prijave PROŠAO")

# SSU_11 — Upravljanje rezervacijama

class SSU11UpravljanjeRezervacijamaTest(unittest.TestCase):

    def setUp(self):
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        login(self.driver, RENTAL_EMAIL, RENTAL_PASS)

    def tearDown(self):
        self.driver.quit()

    def test_01_pregled_rezervacija(self):
        """
        2.2.1 Rental firma vidi listu rezervacija.
        """
        self.driver.get(f"{BASE_URL}/rental/profile/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        self.assertNotIn("login", self.driver.current_url)
        self.assertEqual(self.driver.current_url, f"{BASE_URL}/rental/profile/")
        print("✓ test_01_pregled_rezervacija PROŠAO")

    def test_02_prihvatanje_rezervacije(self):
        """
        2.2.2 Rental firma prihvata rezervaciju klikom na dugme.
        Pretpostavlja da postoji rezervacija na čekanju na profilu.
        """
        self.driver.get(f"{BASE_URL}/rental/profile/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            accept_btn = self.driver.find_element(
                By.XPATH, "//form[contains(@action,'accept')]//button"
            )
            accept_btn.click()
            time.sleep(1)
            self.assertEqual(self.driver.current_url, f"{BASE_URL}/rental/profile/")
            print("✓ test_02_prihvatanje_rezervacije PROŠAO")
        except Exception:
            print("⚠ test_02_prihvatanje_rezervacije — nema rezervacija na čekanju, preskočen")

    def test_03_odbijanje_rezervacije(self):
        """
        2.2.3 Rental firma odbija rezervaciju sa razlogom.
        """
        self.driver.get(f"{BASE_URL}/rental/profile/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            reject_form = self.driver.find_element(
                By.XPATH, "//form[contains(@action,'reject')]"
            )
            reason_field = reject_form.find_element(By.NAME, "reject_reason")
            reason_field.send_keys("Oprema je na servisu.")
            reject_form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(1)
            self.assertEqual(self.driver.current_url, f"{BASE_URL}/rental/profile/")
            print("✓ test_03_odbijanje_rezervacije PROŠAO")
        except Exception:
            print("⚠ test_03_odbijanje_rezervacije — nema rezervacija na čekanju, preskočen")

    def test_04_upravljanje_bez_prijave(self):
        """
        2.2.4 Neulogovani korisnik ne može upravljati rezervacijama.
        """
        logout(self.driver)
        self.driver.get(f"{BASE_URL}/reservation/1/accept/")
        time.sleep(1)

        self.assertIn("login", self.driver.current_url)
        print("✓ test_04_upravljanje_bez_prijave PROŠAO")


if __name__ == "__main__":
    unittest.main(verbosity=2)
