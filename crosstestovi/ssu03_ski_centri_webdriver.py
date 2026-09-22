"""
Cross-test SSU_03 (Pregled ski centara) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
    - Pokrenut seed:  python crosstestovi/seed_ssu05.py
      (kreira ski centar "Ski Centar Kopaonik" na lokaciji Kopaonik)

Pokretanje (iz root foldera projekta):
    python crosstestovi/ssu03_ski_centri_webdriver.py

Napomena: pregled ski centara je JAVAN - testovi ne zahtevaju prijavu.
"""
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

BASE = "http://127.0.0.1:8000"


def novi_driver():
    return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))


def test_legalno_lista_i_detalj():
    """
    LEGALNO: gost otvara listu ski centara, vidi bar jednu karticu i
    otvara javni profil klikom na 'Pogledaj centar'.
    """
    d = novi_driver()
    try:
        d.get(BASE + "/ski-centri/")
        time.sleep(1.5)
        kartice = d.find_elements(By.CSS_SELECTOR, "a.btn-book")
        assert kartice, "FAIL: nema nijednog ski centra u listi (pokreni seed_ssu05.py)"
        print("PASS  legalno(lista): prikazane kartice ski centara")
        kartice[0].click()
        time.sleep(1.5)
        assert "/ski-centri/" in d.current_url and d.current_url.rstrip("/").split("/")[-1].isdigit(), \
            "FAIL: nije otvoren javni profil centra"
        print("PASS  legalno(detalj): otvoren javni profil ski centra")
    finally:
        d.quit()


def test_legalno_pretraga():
    """
    LEGALNO: pretraga po nazivu 'Kopaonik' vraca bar jedan rezultat koji
    sadrzi taj naziv.
    """
    d = novi_driver()
    try:
        d.get(BASE + "/ski-centri/")
        time.sleep(1)
        d.find_element(By.NAME, "q").send_keys("Kopaonik")
        d.find_element(By.CSS_SELECTOR, "form[method='GET'] button, form[method='GET'] [type='submit']").click()
        time.sleep(1.5)
        assert "Kopaonik" in d.page_source, "FAIL: pretraga ne vraca ocekivani centar"
        assert "q=Kopaonik" in d.current_url, "FAIL: q parametar nije u URL-u"
        print("PASS  legalno(pretraga): rezultat sadrzi 'Kopaonik'")
    finally:
        d.quit()


def test_nelegalno_pretraga_bez_rezultata():
    """
    NELEGALNO/RUBNO: pretraga besmislenog pojma -> prikazana poruka da
    nema pronadjenih ski centara.
    """
    d = novi_driver()
    try:
        d.get(BASE + "/ski-centri/?q=NePostoji123")
        time.sleep(1.5)
        assert "Nema pronađenih ski centara" in d.page_source, \
            "FAIL: nema poruke o praznom rezultatu pretrage"
        print("PASS  nelegalno(pretraga): ispravna poruka za prazan rezultat")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_lista_i_detalj()
    test_legalno_pretraga()
    test_nelegalno_pretraga_bez_rezultata()
    print("\nSSU_03 WebDriver testovi zavrseni.")
