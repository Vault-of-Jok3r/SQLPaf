#%% Cellule 1 : Imports, configuration et définition du Spider & Pipeline
import nest_asyncio
nest_asyncio.apply()

import scrapy
from scrapy.crawler import CrawlerProcess
import csv
import re

# Variable globale pour stocker les items collectés
SCRAPED_ITEMS = []

# Liste d'extensions à ignorer pour éviter de crawler des ressources non HTML
IGNORED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico",
                      ".css", ".js", ".pdf", ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx"]

def is_html_url(url):
    # Ignorer les URL indésirables comme mailto:, javascript: etc.
    if url.lower().startswith("mailto:") or url.lower().startswith("javascript:"):
        return False
    # Pour les URL absolues (commençant par http), vérifier qu'elles ne se terminent pas par une extension non désirée
    if url.lower().startswith("http"):
        return not any(url.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)
    # Pour les URL relatives, on considère qu'elles pointent vers du HTML
    return True

# Spider pour la collecte de données et détection de formulaires sur quotes.toscrape.com
class FormDetectionSpider(scrapy.Spider):
    name = "form_detection"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["http://quotes.toscrape.com"]

    def parse(self, response):
        # Vérifier que la réponse est du HTML
        content_type = response.headers.get('Content-Type', b'').decode('utf-8')
        if "html" not in content_type.lower():
            self.logger.info("Réponse ignorée (non HTML): %s", response.url)
            return

        # Suivre les liens internes en filtrant ceux qui ne semblent pas être des pages HTML
        for href in response.css('a::attr(href)').getall():
            href = href.strip()
            if not is_html_url(href):
                continue
            # On autorise les URL relatives ou celles contenant "quotes.toscrape.com"
            if (not href.startswith("/")) and ("quotes.toscrape.com" not in href):
                continue
            yield response.follow(href, self.parse)
        
        # Récupérer le contenu HTML de la page
        html_content = response.text

        # Analyse heuristique pour détecter des formulaires
        forms = response.xpath('//form')
        label = "no_form"  # Par défaut : aucun formulaire détecté
        
        # Si l'URL contient "login", on considère qu'il s'agit d'une page de connexion
        if "login" in response.url.lower():
            label = "login_form"
        elif forms:
            for form in forms:
                form_html = form.get().lower()
                if "register" in form_html or "signup" in form_html:
                    label = "registration_form"
                elif "login" in form_html:
                    label = "login_form"
                else:
                    label = "form_detected"
                # On s'intéresse uniquement au premier formulaire détecté
                break

        # Stocker l'URL, le HTML et le label (issu des règles heuristiques) pour feedback ultérieur
        yield {"url": response.url, "html": html_content, "label": label}

# Pipeline pour stocker les items dans la variable globale
class GlobalStorePipeline:
    def process_item(self, item, spider):
        SCRAPED_ITEMS.append(item)
        return item
    
#%% Cellule 2 : Fonctions d'entraînement, de feedback interactif et création du CSV de sortie
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import pickle

def train_model():
    """
    Entraîne un modèle de régression logistique sur le dataset validé.
    Vérifie que le dataset contient au moins deux classes.
    Sauvegarde ensuite le modèle et le vectorizer.
    """
    # Charger le dataset validé créé par le feedback
    data = pd.read_csv("bin/train_forms/final_dataset.csv")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X = vectorizer.fit_transform(data['html'])
    y = data['label']
    
    # Vérifier que le dataset contient au moins deux classes
    unique_classes = set(y)
    if len(unique_classes) < 2:
        print("Erreur : Le dataset ne contient qu'une seule classe:", unique_classes)
        print("Veuillez ajouter des exemples pour au moins une autre classe avant d'entraîner le modèle.")
        return
    
    # Séparation en ensembles d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    print("Précision du modèle sur le test :", clf.score(X_test, y_test))
    
    # Sauvegarder le modèle et le vectorizer pour usage ultérieur
    with open("bin/train_forms/form_detector_model.pkl", "wb") as f:
        pickle.dump(clf, f)
    with open("bin/train_forms/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

def manual_feedback_and_create_dataset():
    """
    Effectue un feedback interactif sur les items collectés pour valider ou corriger le label.
    Sauvegarde ensuite le dataset final (conservant le HTML pour l'entraînement) dans un CSV.
    """
    validated_items = []
    # SCRAPED_ITEMS doit être définie dans votre code de crawl (variable globale)
    for item in SCRAPED_ITEMS:
        print("\nURL :", item['url'])
        print("Label proposé :", item['label'])
        feedback = input("Validez-vous ce label ? (o/n) : ").strip().lower()
        if feedback != "o":
            new_label = input("Entrez le nouveau label (ex: registration_form, login_form, form_detected, no_form) : ")
            item['label'] = new_label
        validated_items.append(item)
    df = pd.DataFrame(validated_items)
    df.to_csv("bin/train_forms/final_dataset.csv", index=False)
    print("\nDataset final créé avec", len(validated_items), "items.")

def predict_page(html_content):
    """
    Retourne la prédiction du modèle supervisé pour le contenu HTML fourni.
    """
    with open("bin/train_forms/vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    with open("bin/train_forms/form_detector_model.pkl", "rb") as f:
        clf = pickle.load(f)
    X = vectorizer.transform([html_content])
    return clf.predict(X)[0]

def create_output_csv():
    """
    Crée un CSV de sortie contenant :
     - url
     - page_status (le label validé manuellement)
     - supervised_response (la prédiction du modèle supervisé)
    """
    data = pd.read_csv("bin/train_forms/final_dataset.csv")
    output_data = []
    for idx, row in data.iterrows():
        # Prédiction du modèle supervisé en utilisant le HTML de la page
        prediction = predict_page(row['html'])
        output_data.append({
            "url": row["url"],
            "page_status": row["label"],
            "supervised_response": prediction
        })
    df_output = pd.DataFrame(output_data)
    df_output.to_csv("bin/train_forms/output.csv", index=False)
    print("\nOutput CSV créé avec", len(output_data), "items.")

#%% Cellule 3 : Exécution du crawl, feedback interactif, entraînement du modèle et création du CSV de sortie
# Paramètres de Scrapy pour le crawl sur quotes.toscrape.com
settings = {
    "ITEM_PIPELINES": {"__main__.GlobalStorePipeline": 300},
    "LOG_LEVEL": "ERROR",   # Réduire la verbosité des logs
    "DOWNLOAD_DELAY": 1,    # Délai de 1 seconde entre les requêtes
}

process = CrawlerProcess(settings)
print("Lancement du crawl sur http://quotes.toscrape.com ...")
process.crawl(FormDetectionSpider)
process.start()  # Attend la fin du crawl

print("\nCrawl terminé. Nombre d'items collectés :", len(SCRAPED_ITEMS))
print("\nDémarrage du feedback interactif pour la validation des labels :")
manual_feedback_and_create_dataset()

print("\nEntraînement du modèle sur le dataset validé...")
train_model()

print("\nCréation du CSV de sortie (URL, page_status, supervised_response)...")
create_output_csv()
print("\nTerminé !")

# %%
