# form_checker.py
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def url_has_form(url, headless=True):
    """
    Loads the URL and returns True if the page contains a <form> tag, False otherwise.
    """
    firefox_options = Options()
    if headless:
        firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-gpu")
    
    driver = webdriver.Firefox(options=firefox_options)
    try:
        driver.get(url)
        # Wait for the page to load properly
        time.sleep(2)
        html = driver.page_source.lower()
        return "<form" in html
    except Exception as e:
        print(f"Error while checking {url}: {e}")
        return False
    finally:
        driver.quit()
