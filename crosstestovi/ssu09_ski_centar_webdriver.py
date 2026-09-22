"""
Cross-test SSU_09 (Upravljanje profilom ski centra) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
    - Pokrenut seed:  python crosstestovi/seed_ssu05.py
      (kreira ski centar nalog: centar@skibooker.rs / lozinka123)

Pokretanje (iz root foldera projekta):
    python crosstestovi/ssu09_ski_centar_webdriver.py
"""
import time
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

BASE = "http://127.0.0.1:8000"
CENTAR_EMAIL = "centar@skibooker.rs"
LOZINKA = "lozinka123"


def novi_driver():
    return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))


def prijavi_ski_centar(d):
    """Prijava postojeceg ski centar naloga (iz seed_ssu05.py)."""
    d.get(BASE + "/accounts/login/")
    d.find_element(By.NAME, "email").send_keys(CENTAR_EMAIL)
    d.find_element(By.NAME, "password").send_keys(LOZINKA)
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)


def test_legalno_dodavanje_staze():
    """LEGALNO (2.2.2): ski centar dodaje novu stazu -> staza vidljiva na profilu."""
    d = novi_driver()
    try:
        prijavi_ski_centar(d)
        d.get(BASE + "/ski-center/profil/")
        time.sleep(1)
        if "login" in d.current_url:
            print("SKIP  legalno: nalog ski centra ne postoji (pokreni seed_ssu05.py).")
            return
        naziv = "Test staza " + uuid.uuid4().hex[:5]
        # otvori modal za dodavanje staze (zaobilazi tab klik)
        d.execute_script("openModal('modal-slope')")
        time.sleep(0.5)
        modal = d.find_element(By.ID, "modal-slope")
        modal.find_element(By.NAME, "name").send_keys(naziv)
        modal.find_element(By.NAME, "length_km").send_keys("2.4")
        Select(modal.find_element(By.NAME, "difficulty")).select_by_value("plava")
        modal.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert naziv in d.page_source, "FAIL: nova staza se ne vidi na profilu"
        print("PASS  legalno: staza uspesno dodata i prikazana")
    finally:
        d.quit()


def test_nelegalno_neulogovan_pristup():
    """NELEGALNO: gost otvara /ski-center/profil/ -> preusmeren na prijavu."""
    d = novi_driver()
    try:
        d.get(BASE + "/ski-center/profil/")
        time.sleep(1.5)
        assert "login" in d.current_url, "FAIL: gost nije preusmeren na prijavu"
        print("PASS  nelegalno: gost preusmeren na prijavu")
    finally:
        d.quit()


def test_nelegalno_prazan_naziv_staze():
    """
    NELEGALNO: dodavanje staze bez naziva. Polje 'name' je 'required' ->
    browser blokira slanje forme, modal ostaje otvoren, staza nije dodata.
    """
    d = novi_driver()
    try:
        prijavi_ski_centar(d)
        d.get(BASE + "/ski-center/profil/")
        time.sleep(1)
        if "login" in d.current_url:
            print("SKIP  nelegalno(prazan naziv): nalog ski centra ne postoji.")
            return
        d.execute_script("openModal('modal-slope')")
        time.sleep(0.5)
        modal = d.find_element(By.ID, "modal-slope")
        # naziv NAMERNO prazan
        Select(modal.find_element(By.NAME, "difficulty")).select_by_value("crna")
        modal.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        # forma nije poslata -> modal je i dalje prikazan
        assert d.find_element(By.ID, "modal-slope").is_displayed(), \
            "FAIL: forma je poslata iako naziv nije unet"
        print("PASS  nelegalno: prazan naziv blokiran (staza nije dodata)")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_dodavanje_staze()
    test_nelegalno_neulogovan_pristup()
    test_nelegalno_prazan_naziv_staze()
    print("\nSSU_09 WebDriver testovi zavrseni.")
