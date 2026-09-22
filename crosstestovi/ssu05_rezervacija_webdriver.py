"""
Cross-test SSU_05 (Rezervacija casa) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
    - U bazi POSTOJI bar jedan instruktor sa BAR JEDNIM slobodnim buducim
      terminom (stranica /instructor/ -> profil instruktora -> "Slobodni termini").
      Rezervacija se pravi kroz stvarni UI, pa mora postojati termin za klik.

Pokretanje (iz root foldera projekta):
    python crosstestovi/ssu05_rezervacija_webdriver.py

Napomena: svaki test registruje SVEZ klijentski nalog (osim testa "nije
prijavljen") kako testovi ne bi zavisili od konkretnih naloga u bazi.
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
    """Napravi svez aktivan klijentski nalog (registracija automatski uloguje)."""
    email = jedinstven_email("klijent")
    d.get(BASE + "/register/")
    d.find_element(By.NAME, "first_name").send_keys("Rez")
    d.find_element(By.NAME, "last_name").send_keys("Klijent")
    d.find_element(By.NAME, "email").send_keys(email)
    d.find_element(By.NAME, "password").send_keys("lozinka123")
    d.find_element(By.NAME, "confirm_password").send_keys("lozinka123")
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    return email


def nadji_profil_sa_terminom(d):
    """
    Prolazi kroz listu instruktora (/instructor/) i vraca URL prvog javnog
    profila koji ima bar jedan slobodan termin (.avail-slot). Vraca None ako
    nijedan nema slobodnih termina.
    """
    d.get(BASE + "/instructor/")
    time.sleep(1)
    linkovi = [a.get_attribute("href")
               for a in d.find_elements(By.CSS_SELECTOR, "a[href*='/instructor/']")
               if a.get_attribute("href") and a.get_attribute("href").rstrip("/").split("/")[-1].isdigit()]
    linkovi = list(dict.fromkeys(linkovi))  # bez duplikata, cuva redosled
    # dijagnostika: koliko instruktora ima i kod koga ima slobodnih termina
    print(f"      [info] nadjeno instruktora u listi: {len(linkovi)}")
    for url in linkovi:
        d.get(url)
        time.sleep(0.6)
        broj_termina = len(d.find_elements(By.CSS_SELECTOR, ".avail-slot"))
        print(f"      [info] {url} -> slobodnih termina: {broj_termina}")
        if broj_termina:
            return url
    print("      [info] nijedan instruktor nema slobodan BUDUCI termin "
          "(is_booked=False i datum >= danas).")
    return None


def test_legalno_uspesna_rezervacija():
    """LEGALNO (2.2.1): prijavljen klijent rezervise slobodan termin -> poruka o uspehu."""
    d = novi_driver()
    try:
        registruj_i_prijavi_klijenta(d)
        url = nadji_profil_sa_terminom(d)
        if url is None:
            print("SKIP  legalno: nema instruktora sa slobodnim terminom u bazi "
                  "(dodaj termin pa pokreni ponovo).")
            return
        # izbor termina -> dugme "Rezervisi cas" -> modal "Potvrdi rezervaciju"
        d.find_element(By.CSS_SELECTOR, ".avail-slot").click()
        time.sleep(0.4)
        d.find_element(By.ID, "btn-book").click()
        time.sleep(0.4)
        d.find_element(By.CSS_SELECTOR, "#modal-confirm .btn-primary").click()
        time.sleep(2)
        assert "uspešno" in d.page_source or "uspesno" in d.page_source, \
            "FAIL: nema poruke o uspesnoj rezervaciji"
        print("PASS  legalno: rezervacija uspesno kreirana")
    finally:
        d.quit()


def test_nelegalno_nije_prijavljen():
    """
    NELEGALNO (2.2.4): gost (neprijavljen) na profilu instruktora ne vidi dugme
    za rezervaciju, vec link 'Prijavi se' koji vodi na stranicu za prijavu.
    """
    d = novi_driver()
    try:
        url = nadji_profil_sa_terminom(d)  # kao gost, bez prijave
        if url is None:
            print("SKIP  nelegalno(gost): nema instruktora sa slobodnim terminom u bazi.")
            return
        # kod gosta ne postoji #btn-book; postoji link ka prijavi
        assert not d.find_elements(By.ID, "btn-book"), \
            "FAIL: gost vidi dugme za rezervaciju"
        link = d.find_element(By.CSS_SELECTOR, "a[href*='/accounts/login/']")
        link.click()
        time.sleep(1.5)
        assert "login" in d.current_url, "FAIL: gost nije preusmeren na prijavu"
        print("PASS  nelegalno: gost preusmeren na prijavu")
    finally:
        d.quit()


def test_nelegalno_get_metoda():
    """
    NELEGALNO: rezervacija je POST akcija. Direktan GET na /slot/<id>/book/
    ne sme da kreira rezervaciju -> korisnik zavrsi na javnom profilu,
    a termin ostaje slobodan (i dalje se vidi u listi termina).
    """
    d = novi_driver()
    try:
        registruj_i_prijavi_klijenta(d)
        url = nadji_profil_sa_terminom(d)
        if url is None:
            print("SKIP  nelegalno(GET): nema instruktora sa slobodnim terminom u bazi.")
            return
        slot_id = d.find_element(By.CSS_SELECTOR, ".avail-slot").get_attribute("data-slot-id")
        d.get(f"{BASE}/slot/{slot_id}/book/")  # GET
        time.sleep(1.5)
        assert "uspešno" not in d.page_source and "uspesno" not in d.page_source, \
            "FAIL: GET je kreirao rezervaciju"
        print("PASS  nelegalno: GET metoda nije kreirala rezervaciju")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_uspesna_rezervacija()
    test_nelegalno_nije_prijavljen()
    test_nelegalno_get_metoda()
    print("\nSSU_05 WebDriver testovi zavrseni.")
