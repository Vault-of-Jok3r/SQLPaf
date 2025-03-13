# web_env.py
import gym
from gym import spaces
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  # Import nécessaire pour Selenium 4+
from PIL import Image
import io
import time

class WebEnv(gym.Env):
    """
    Environnement Gym pour l'exploration web via Selenium.
    L'état est défini par un screenshot redimensionné (84x84 pixels, 3 canaux).
    Les actions (espace discret) sont :
      0 : Suivre le premier lien de la page.
      1 : Faire défiler la page vers le bas.
      2 : Vérifier la présence d'un formulaire et déclencher SQLMap si détecté.
      3 : Revenir à la page précédente.
    """
    def __init__(self, start_url="http://quotes.toscrape.com", headless=True):
        super(WebEnv, self).__init__()
        self.start_url = start_url
        self.current_url = start_url
        
        # Configuration de Selenium avec Chrome en mode headless
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.start_url)
        time.sleep(1)  # Attente du chargement
        
        # Définition des espaces d'actions et d'observations
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=0, high=255, shape=(84, 84, 3), dtype=np.uint8)
    
    def _get_observation(self):
        # Capture d'écran et redimensionnement à 84x84
        png = self.driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(png)).convert("RGB")
        image = image.resize((84,84))
        return np.array(image)
    
    def _detect_form(self):
        # Détection heuristique d'un formulaire par la présence de la balise "<form"
        html = self.driver.page_source.lower()
        return "<form" in html
    
    def step(self, action):
        done = False  # Pour ce prototype, l'épisode se termine sur un nombre fixe d'étapes
        reward = 0
        info = {}
        
        if action == 0:
            # Suivre le premier lien trouvé sur la page
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")  # Récupération de tous les liens
                if links:
                    links[0].click()
                    time.sleep(1)
                    self.current_url = self.driver.current_url
                else:
                    info['error'] = "No link element found."
                    reward = -1  # Pénaliser l'absence de lien
            except Exception as e:
                info['error'] = str(e)
        elif action == 1:
            # Faire défiler la page vers le bas
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        elif action == 2:
            # Vérifier la présence d'un formulaire et déclencher SQLMap si trouvé
            if self._detect_form():
                reward = 10  # Récompense positive
                info['form_detected'] = True
                from sqlmap_integration import run_sqlmap
                sqlmap_result = run_sqlmap(self.current_url)
                info['sqlmap'] = sqlmap_result
            else:
                reward = -1  # Pénalité en cas d'absence de formulaire
        elif action == 3:
            # Revenir à la page précédente
            self.driver.back()
            time.sleep(1)
            self.current_url = self.driver.current_url
        
        obs = self._get_observation()
        return obs, reward, done, info
    
    def reset(self):
        # Réinitialiser l'environnement en rechargeant l'URL de départ
        self.driver.get(self.start_url)
        time.sleep(1)
        self.current_url = self.start_url
        return self._get_observation()
    
    def close(self):
        # Fermer le driver Selenium
        self.driver.quit()
