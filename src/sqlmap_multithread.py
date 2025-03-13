# sqlmap_multithread.py
import concurrent.futures
from sqlmap_integration import run_sqlmap

def run_sqlmap_multithread(urls, max_workers=5):
    """
    Exécute SQLMap en multi-thread sur une liste d'URLs.
    Retourne un dictionnaire avec pour clé l'URL et pour valeur le résultat de SQLMap.
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(run_sqlmap, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
            except Exception as exc:
                result = f"Erreur: {exc}"
            results[url] = result
    return results
