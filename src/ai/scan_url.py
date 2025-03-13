import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from ai.sqlmap_integration import run_sqlmap

def scan_url_for_form(url, headless=True):
    # Configuration du navigateur en mode headless
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    
    print(f"Chargement de la page : {url}")
    driver.get(url)
    time.sleep(2)  # Attendre le chargement complet
    
    # Récupérer le contenu HTML de la page
    html = driver.page_source.lower()
    
    # Vérifier si un formulaire est présent
    if "<form" in html:
        # Optionnel : pour être plus spécifique, vérifier des indices du formulaire d'inscription
        if "register" in html or "signup" in html or "inscription" in html:
            print("Formulaire d'inscription détecté. Lancement de SQLMap...")
        else:
            print("Un formulaire a été détecté, lancement de SQLMap...")
        # Lancer SQLMap
        result = run_sqlmap(url)
        print("Résultat de SQLMap :")
        print(result)
    else:
        print("Aucun formulaire détecté sur cette page.")
    
    driver.quit()

if __name__ == "__main__":
    target_url = "http://quotes.toscrape.com/"
    scan_url_for_form(target_url)
