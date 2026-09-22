"""
Cross-test SSU_02 (Prijava / login) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
Pokretanje (iz root foldera projekta):
    python crosstestovi/ssu02_prijava_webdriver.py

Napomena: svaki test prvo registruje SVEŽ nalog pa se odjavi (brisanje kolačića)
i tek onda testira prijavu -> ne zavisi od postojećih naloga u bazi.
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


def registruj_pa_odjavi(d, email, password):
    """Napravi svež aktivan nalog i odjavi se (obrisi kolacice = session)."""
    d.get(BASE + "/register/")
    d.find_element(By.NAME, "first_name").send_keys("Login")
    d.find_element(By.NAME, "last_name").send_keys("Test")
    d.find_element(By.NAME, "email").send_keys(email)
    d.find_element(By.NAME, "password").send_keys(password)
    d.find_element(By.NAME, "confirm_password").send_keys(password)
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    d.delete_all_cookies()  # odjava


def test_legalno_uspesna_prijava():
    """LEGALNO: tačan email + lozinka -> uspešna prijava (izlazi sa /login)."""
    d = novi_driver()
    try:
        email = jedinstven_email("login")
        registruj_pa_odjavi(d, email, "lozinka123")
        d.get(BASE + "/accounts/login/")
        d.find_element(By.NAME, "email").send_keys(email)
        d.find_element(By.NAME, "password").send_keys("lozinka123")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "login" not in d.current_url, "FAIL: prijava nije uspela"
        print("PASS  legalno: uspesna prijava ->", d.current_url)
    finally:
        d.quit()


def test_nelegalno_pogresna_lozinka():
    """NELEGALNO: tačan email, pogrešna lozinka -> ostaje na /login."""
    d = novi_driver()
    try:
        email = jedinstven_email("login")
        registruj_pa_odjavi(d, email, "lozinka123")
        d.get(BASE + "/accounts/login/")
        d.find_element(By.NAME, "email").send_keys(email)
        d.find_element(By.NAME, "password").send_keys("pogresna456")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "login" in d.current_url, "FAIL: prijava prosla sa pogresnom lozinkom"
        print("PASS  nelegalno: pogresna lozinka odbijena")
    finally:
        d.quit()


def test_nelegalno_nepostojeci_nalog():
    """NELEGALNO: email koji ne postoji -> ostaje na /login."""
    d = novi_driver()
    try:
        d.get(BASE + "/accounts/login/")
        d.find_element(By.NAME, "email").send_keys(jedinstven_email("nepostoji"))
        d.find_element(By.NAME, "password").send_keys("lozinka123")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "login" in d.current_url, "FAIL: prijava prosla sa nepostojecim nalogom"
        print("PASS  nelegalno: nepostojeci nalog odbijen")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_uspesna_prijava()
    test_nelegalno_pogresna_lozinka()
    test_nelegalno_nepostojeci_nalog()
    print("\nSSU_02 WebDriver testovi zavrseni.")
