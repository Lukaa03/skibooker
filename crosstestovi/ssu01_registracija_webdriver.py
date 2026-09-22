"""
Cross-test SSU_01 (Registracija) - Selenium WebDriver.

Preduslovi:
    - Django server pokrenut:  python manage.py runserver   (http://127.0.0.1:8000)
    - pip install selenium webdriver-manager
Pokretanje:
    python ssu01_registracija_webdriver.py

Napomena: koristi Firefox. Za Chrome zameni Firefox/Gecko sa Chrome/Chromedriver.
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


def test_legalno_registracija_klijenta():
    """LEGALNO: validan klijent -> registracija prolazi (izlazi sa /register)."""
    d = novi_driver()
    try:
        d.get(BASE + "/register/")
        d.find_element(By.NAME, "first_name").send_keys("Selenium")
        d.find_element(By.NAME, "last_name").send_keys("Klijent")
        d.find_element(By.NAME, "email").send_keys(jedinstven_email("klijent"))
        d.find_element(By.NAME, "password").send_keys("lozinka123")
        d.find_element(By.NAME, "confirm_password").send_keys("lozinka123")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "/register" not in d.current_url, "FAIL: ostao na registraciji"
        print("PASS  legalno: klijent registrovan ->", d.current_url)
    finally:
        d.quit()


def test_nelegalno_kratka_lozinka():
    """NELEGALNO: lozinka < 8 -> forma ne prolazi (ostaje na /register)."""
    d = novi_driver()
    try:
        d.get(BASE + "/register/")
        d.find_element(By.NAME, "first_name").send_keys("Selenium")
        d.find_element(By.NAME, "last_name").send_keys("Kratka")
        d.find_element(By.NAME, "email").send_keys(jedinstven_email("kratka"))
        d.find_element(By.NAME, "password").send_keys("123")
        d.find_element(By.NAME, "confirm_password").send_keys("123")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "/register" in d.current_url, "FAIL: prosla registracija sa kratkom sifrom"
        print("PASS  nelegalno: kratka lozinka odbijena")
    finally:
        d.quit()


def test_nelegalno_nepoklapanje_lozinki():
    """NELEGALNO: password != confirm -> forma ne prolazi."""
    d = novi_driver()
    try:
        d.get(BASE + "/register/")
        d.find_element(By.NAME, "first_name").send_keys("Selenium")
        d.find_element(By.NAME, "last_name").send_keys("Nepoklapanje")
        d.find_element(By.NAME, "email").send_keys(jedinstven_email("nepoklapanje"))
        d.find_element(By.NAME, "password").send_keys("lozinka123")
        d.find_element(By.NAME, "confirm_password").send_keys("druga456")
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        assert "/register" in d.current_url, "FAIL: prosla registracija sa neuskladjenim lozinkama"
        print("PASS  nelegalno: nepoklapanje lozinki odbijeno")
    finally:
        d.quit()


if __name__ == "__main__":
    test_legalno_registracija_klijenta()
    test_nelegalno_kratka_lozinka()
    test_nelegalno_nepoklapanje_lozinki()
    print("\nSSU_01 WebDriver testovi zavrseni.")
