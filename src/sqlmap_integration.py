# sqlmap_integration.py
import subprocess
import sys

def run_sqlmap(url):
    """
    Déclenche SQLMap sur l'URL fournie en utilisant le chemin absolu vers sqlmap.py.
    """
    try:
        # Utilisation de sys.executable pour invoquer l'interpréteur Python
        cmd = [
            sys.executable,
            r"C:\Users\adrie\Documents\SQLPaf V2.0\sqlmap\sqlmap.py",  # Chemin absolu vers sqlmap.py
            "-u", url,
            "--batch",
            "--crawl=1"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
    except Exception as e:
        output = f"Erreur lors de l'exécution de SQLMap : {e}"
    return output
