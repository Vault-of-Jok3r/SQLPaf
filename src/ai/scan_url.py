#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import requests
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Désactivation des avertissements SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Chemins des fichiers de configuration
SQL_ERRORS_FILE = "bin/payloads/sql_errors.txt"
SQL_PAYLOADS_FILE = "bin/payloads/sql_payloads.txt"

# --- Gestion Dynamique des Erreurs SQL ---

def load_known_errors():
    """
    Lit le fichier sql_errors.txt et renvoie la liste des erreurs SQL connues.
    Ignore les lignes vides ou commençant par '#'.
    """
    known_errors = []
    if os.path.isfile(SQL_ERRORS_FILE):
        with open(SQL_ERRORS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    known_errors.append(line.lower())
    return known_errors

def add_error_to_file(new_error):
    """
    Ajoute la nouvelle erreur au fichier sql_errors.txt si elle n'existe pas déjà.
    """
    new_error_lower = new_error.lower()
    current_errors = load_known_errors()
    if new_error_lower not in current_errors:
        with open(SQL_ERRORS_FILE, "a", encoding="utf-8") as f:
            f.write(new_error_lower + "\n")
        print(f"[+] Nouvelle erreur SQL ajoutée dans {SQL_ERRORS_FILE}: {new_error_lower}")
    else:
        print(f"[-] Erreur SQL déjà connue: {new_error_lower}")

def detect_sql_errors(page_content, known_errors):
    """
    Recherche les erreurs SQL connues dans le contenu de la page.
    Renvoie une liste des erreurs détectées.
    """
    content_lower = page_content.lower()
    found_errors = []
    for err in known_errors:
        if err in content_lower:
            found_errors.append(err)
    return found_errors

def analyze_page(page_content):
    """
    Analyse le contenu de la page pour détecter des erreurs SQL.
    Si aucune erreur connue n'est détectée mais que le mot 'error' est présent,
    une nouvelle signature est ajoutée (exemple simplifié).
    """
    known_errors = load_known_errors()
    detected_errors = detect_sql_errors(page_content, known_errors)
    
    if detected_errors:
        for err in detected_errors:
            print(f"[!] Erreur SQL détectée : {err}")
    else:
        print("[-] Aucune erreur SQL connue détectée.")
    
    if "error" in page_content.lower() and not detected_errors:
        new_error = "unlisted new error"
        add_error_to_file(new_error)
    
    return len(detected_errors)

# --- Chargement des Payloads à partir du fichier texte ---

def load_payloads():
    """
    Lit le fichier sql_payloads.txt et renvoie deux listes :
      - error_payloads pour les injections basées sur les erreurs
      - blind_payloads pour les injections basées sur le temps (blind)
    Les lignes vides et celles commençant par '#' sont ignorées.
    La séparation se fait à l'aide de marqueurs dans le fichier.
    """
    error_payloads = []
    blind_payloads = []
    mode = None  # 'error' ou 'blind'
    
    if os.path.isfile(SQL_PAYLOADS_FILE):
        with open(SQL_PAYLOADS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    if "Payloads Error-Based" in line:
                        mode = "error"
                    elif "Payloads Blind" in line:
                        mode = "blind"
                    continue
                if mode == "error":
                    error_payloads.append(line)
                elif mode == "blind":
                    blind_payloads.append(line)
    else:
        print(f"[!] Fichier de payloads non trouvé : {SQL_PAYLOADS_FILE}")
    
    return error_payloads, blind_payloads

# --- Simulation de la Soumission d'un Formulaire via Requests ---

def simulate_form_submission(form, payload, base_url):
    """
    Simule la soumission d'un formulaire HTML avec un payload donné.
    Reconstruit l'URL d'action (en gérant les liens relatifs) et récupère
    tous les champs <input> du formulaire en affectant le payload aux champs
    modifiables (en ignorant les boutons ou champs cachés).
    Retourne le contenu de la réponse et le temps écoulé.
    """
    method = form.get("method", "get").lower()
    action = form.get("action")
    if action:
        action_url = urljoin(base_url, action)
    else:
        action_url = base_url

    data = {}
    # Parcours des champs input
    inputs = form.find_all("input")
    if not inputs:
        return "", 0
    for inp in inputs:
        input_type = inp.get("type", "text").lower()
        input_name = inp.get("name")
        if not input_name:
            continue
        if input_type in ["submit", "button", "hidden"]:
            # On garde la valeur par défaut le cas échéant
            data[input_name] = inp.get("value", "")
        else:
            data[input_name] = payload

    try:
        start_time = time.time()
        if method == "get":
            resp = requests.get(action_url, params=data, timeout=10, verify=False)
        else:
            resp = requests.post(action_url, data=data, timeout=10, verify=False)
        elapsed = time.time() - start_time
        return resp.text, elapsed
    except Exception as e:
        print(f"[!] Exception lors de la soumission du formulaire : {e}")
        return "", 0

# --- Tests d'Injection sur les Formulaires via Requests ---

def test_injections_on_forms(url):
    print(f"[*] Démarrage des tests d'injection sur : {url}")
    score = {
        "form_detected": 0,
        "form_not_detected": 0,
        "injection_success": 0,
        "injection_failure": 0,
        "error_messages": 0
    }
    
    try:
        resp = requests.get(url, timeout=10, verify=False)
    except Exception as e:
        print(f"[!] Erreur lors de la récupération de {url} : {e}")
        return score
    
    page_content = resp.text
    soup = BeautifulSoup(page_content, "html.parser")
    forms = soup.find_all("form")
    
    if not forms:
        print(f"[+] Aucun formulaire détecté sur {url}")
        score["form_not_detected"] += 1
        return score
    
    score["form_detected"] += len(forms)
    
    error_payloads, blind_payloads = load_payloads()
    if not error_payloads:
        print("[!] Aucun payload d'erreur trouvé.")
    if not blind_payloads:
        print("[!] Aucun payload time-based (blind) trouvé.")
    
    for form_index, form in enumerate(forms, start=1):
        print(f"[*] Test du formulaire {form_index} sur {url}")
        inputs = form.find_all("input")
        if not inputs:
            print(f"[!] Aucun champ input trouvé dans le formulaire {form_index}")
            continue
        
        injection_successful = False
        # Test basé sur les erreurs SQL
        for payload in error_payloads:
            print(f"[*] Test error-based avec le payload : {payload}")
            resp_text, _ = simulate_form_submission(form, payload, url)
            errors_count = analyze_page(resp_text)
            score["error_messages"] += errors_count
            if errors_count > 0:
                print(f"[!] Injection error-based réussie avec le payload : {payload}")
                injection_successful = True
                score["injection_success"] += 1
                break
        if not injection_successful:
            score["injection_failure"] += 1
        
        # Test en blind (time-based)
        for payload in blind_payloads:
            print(f"[*] Test blind avec le payload : {payload}")
            resp_text, elapsed = simulate_form_submission(form, payload, url)
            print(f"[+] Test blind pour le formulaire {form_index} avec '{payload}' a duré {elapsed:.2f} secondes")
            if elapsed > 4:
                print(f"[!] Injection blind possible détectée avec '{payload}' dans le formulaire {form_index} !")
                score["injection_success"] += 1
            else:
                score["injection_failure"] += 1
            errors_count = analyze_page(resp_text)
            score["error_messages"] += errors_count

    print(f"--- Score pour {url} ---")
    print(f"Formulaires détectés     : {score['form_detected']}")
    print(f"Formulaires non détectés : {score['form_not_detected']}")
    print(f"Injections réussies      : {score['injection_success']}")
    print(f"Injections échouées      : {score['injection_failure']}")
    print(f"Total messages d'erreur  : {score['error_messages']}")
    return score

async def async_test_injections(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, test_injections_on_forms, url)

# --- Modes d'Exécution ---

def single_url_mode():
    domain_path = "bin/temp/domain.txt"
    if not os.path.isfile(domain_path):
        print("[!] Fichier non trouvé : bin/temp/domain.txt")
        return
    with open(domain_path, "r", encoding="utf-8") as f:
        url = f.read().strip()
    print("=========================================")
    print(f"[*] Test d'injection sur l'URL unique : {url}")
    score = test_injections_on_forms(url)
    print(f"--- Résumé pour {url} ---")
    print(score)

def url_list_mode():
    global_score = {
        "form_detected": 0,
        "form_not_detected": 0,
        "injection_success": 0,
        "injection_failure": 0,
        "error_messages": 0
    }
    
    domain_path = "bin/temp/domain.txt"
    if not os.path.isfile(domain_path):
        print(f"[!] Fichier non trouvé : {domain_path}")
        return
    with open(domain_path, "r", encoding="utf-8") as f:
        domain = f.read().strip()

    wordlist_path_file = "bin/temp/wordlist.txt"
    if not os.path.isfile(wordlist_path_file):
        print(f"[!] Fichier non trouvé : {wordlist_path_file}")
        return
    with open(wordlist_path_file, "r", encoding="utf-8") as f:
        wordlist_path = f.read().strip()

    if not wordlist_path:
        print("[!] Wordlist vide, merci de choisir le mode URL unique.")
        return

    try:
        with open(wordlist_path, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[!] Erreur lors de la lecture de la wordlist : {e}")
        return

    print(f"[+] Domaine   : {domain}")
    print(f"[+] Wordlist  : {wordlist_path}")
    print(f"[+] Nombre de chemins à tester : {len(paths)}")
    print("=========================================")

    domain = domain.rstrip("/")
    injection_tasks = []
    for path in paths:
        if path.startswith("/"):
            url = domain + path
        else:
            url = domain + "/" + path

        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"[+] URL valide : {url} (HTTP 200)")
                if "<form" in response.text.lower():
                    print(f"[*] Formulaire détecté à {url}, planification du test d'injection...")
                    injection_tasks.append(async_test_injections(url))
                else:
                    print(f"[-] Aucun formulaire détecté à {url} (vérification rapide).")
            else:
                print(f"[-] {url} => Statut {response.status_code}")
        except requests.RequestException as req_err:
            print(f"[!] Erreur réseau pour {url} : {req_err}")

    if injection_tasks:
        print("=========================================")
        print("[*] Démarrage des tests d'injection SQL asynchrones sur les URLs avec formulaire...")
        async def run_all_injections():
            return await asyncio.gather(*injection_tasks)
        results = asyncio.run(run_all_injections())
        for res in results:
            global_score["form_detected"] += res.get("form_detected", 0)
            global_score["form_not_detected"] += res.get("form_not_detected", 0)
            global_score["injection_success"] += res.get("injection_success", 0)
            global_score["injection_failure"] += res.get("injection_failure", 0)
            global_score["error_messages"] += res.get("error_messages", 0)
    else:
        print("[+] Aucune URL avec formulaire n'a été détectée dans ce scan.")
    
    print("=========================================")
    print("--- Score Global ---")
    print(f"Formulaires détectés     : {global_score['form_detected']}")
    print(f"Formulaires non détectés : {global_score['form_not_detected']}")
    print(f"Injections réussies      : {global_score['injection_success']}")
    print(f"Injections échouées      : {global_score['injection_failure']}")
    print(f"Total messages d'erreur  : {global_score['error_messages']}")

def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("[!] No mode specified. Usage: scan_url.py [basic|ml]")
        sys.exit(1)
    if mode == "basic":
        single_url_mode()
    elif mode == "ml":
        url_list_mode()
    else:
        print(f"[!] Unknown mode: {mode}. Please use 'basic' or 'ml'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
