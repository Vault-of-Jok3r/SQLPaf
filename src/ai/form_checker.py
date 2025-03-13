# form_checker.py
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def url_has_form(url, headless=True):
    """
    Charge l'URL et retourne True si la page contient une balise <form>, False sinon.
    """
    firefox_options = Options()
    if headless:
        firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-gpu")
    
    driver = webdriver.firefox(options=firefox_options)
    try:
        driver.get(url)
        # Attente pour que la page se charge correctement
        time.sleep(2)
        html = driver.page_source.lower()
        return "<form" in html
    except Exception as e:
        print(f"Erreur lors de la vérification de {url}: {e}")
        return False
    finally:
        driver.quit()