"""
Cross-test SSU_07 (Pregled i otkazivanje rezervacija) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
    - Pokrenut seed:  python crosstestovi/seed_ssu05.py
      (mora postojati instruktor sa slobodnim BUDUCIM terminom > 24h,
       jer legalni test prvo napravi rezervaciju pa je otkazuje)

Pokretanje (iz root foldera projekta):
    python crosstestovi/ssu07_pregled_webdriver.py

Napomena: svaki test registruje SVEZ klijentski nalog (osim testa "nije
prijavljen") pa ne zavisi od konkretnih naloga u bazi.
"""
import time
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

BASE = "http://127.0.0.1:8000"


def novi_driver():
    return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))


def jedinstven_email(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.rs"


def registruj_i_prijavi_klijenta(d):
    email = jedinstven_email("klijent")
    d.get(BASE + "/register/")
    d.find_element(By.NAME, "first_name").send_keys("Pregled")
    d.find_element(By.NAME, "last_name").send_keys("Klijent")
    d.find_element(By.NAME, "email").send_keys(email)
    d.find_element(By.NAME, "password").send_keys("lozinka123")
    d.find_element(By.NAME, "confirm_password").send_keys("lozinka123")
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    return email


def rezervisi_jedan_termin(d):
    """
    Prolazi kroz listu instruktora i rezervise prvi slobodan termin
    (isti tok kao SSU_05). Vraca True ako je rezervacija napravljena.
    """
    d.get(BASE + "/instructor/")
    time.sleep(1)
    linkovi = [a.get_attribute("href")
               for a in d.find_elements(By.CSS_SELECTOR, "a[href*='/instructor/']")
               if a.get_attribute("href") and a.get_attribute("href").rstrip("/").split("/")[-1].isdigit()]
    linkovi = list(dict.fromkeys(linkovi))
    for url in linkovi:
        d.get(url)
        time.sleep(0.6)
        if d.find_elements(By.CSS_SELECTOR, ".avail-slot"):
            d.find_element(By.CSS_SELECTOR, ".avail-slot").click()
            time.sleep(0.4)
            d.find_element(By.ID, "btn-book").click()
            time.sleep(0.4)
            d.find_element(By.CSS_SELECTOR, "#modal-confirm .btn-primary").click()
            time.sleep(2)
            return True
    return False


def test_legalno_pregled_i_otkazivanje():
    """
    LEGALNO (2.2.1 + 2.2.2): klijent vidi svoju rezervaciju na profilu
    pa je uspesno otkazuje (termin > 24h).
    """
    d = novi_driver()
    try:
        registruj_i_prijavi_klijenta(d)
        if not rezervisi_jedan_termin(d):
            print("SKIP  legalno: nema slobodnog termina u bazi "
                  "(pokreni seed_ssu05.py pa ponovo).")
            return
        # pregled (2.2.1)
        d.get(BASE + "/klijent/profil/")
        time.sleep(1)
        assert "Otkaži" in d.page_source or "Otka" in d.page_source, \
            "FAIL: rezervacija se ne vidi na profilu"
        print("PASS  legalno(pregled): rezervacija vidljiva na profilu")
        # otkazivanje (2.2.2) -> klik na 'Otkaži' + potvrda confirm dijaloga
        dugme = d.find_element(
            By.XPATH,
            "//form[contains(@action,'/booking/') and contains(@action,'/cancel/')]//button[@type='submit']")
        dugme.click()
        time.sleep(0.5)
        d.switch_to.alert.accept()  # potvrdi 'Da li ste sigurni...'
        time.sleep(2)
        assert "otkazana" in d.page_source.lower(), "FAIL: nema poruke o otkazivanju"
        print("PASS  legalno(otkazivanje): rezervacija uspesno otkazana")
    finally:
        d.quit()


def test_nelegalno_neulogovan_pristup():
    """NELEGALNO: gost otvara /klijent/profil/ -> preusmeren na prijavu."""
    d = novi_driver()
    try:
        d.get(BASE + "/klijent/profil/")
        time.sleep(1.5)
        assert "login" in d.current_url, "FAIL: gost nije preusmeren na prijavu"
        print("PASS  nelegalno: gost preusmeren na prijavu")
    finally:
        d.quit()


def test_scenario_nema_rezervacija():
    """
    SCENARIO (2.2.4): svez klijent bez rezervacija -> profil prikazuje
    poruku 'Nemate nijednu aktivnu rezervaciju.'
    """
    d = novi_driver()
    try:
        registruj_i_prijavi_klijenta(d)
        d.get(BASE + "/klijent/profil/")
        time.sleep(1)
        assert "Nemate nijednu aktivnu rezervaciju" in d.page_source, \
            "FAIL: nema poruke o praznom pregledu"
        print("PASS  scenario: prazan pregled prikazuje ispravnu poruku")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_pregled_i_otkazivanje()
    test_nelegalno_neulogovan_pristup()
    test_scenario_nema_rezervacija()
    print("\nSSU_07 WebDriver testovi zavrseni.")
