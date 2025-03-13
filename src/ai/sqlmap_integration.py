# sqlmap_integration.py
import subprocess

def run_sqlmap(url):
    """
    Déclenche SQLMap sur l'URL fournie en utilisant le chemin absolu vers sqlmap.py.
    """
    try:
        cmd = [
            r"/usr/bin/sqlmap",
            "-u", url,
            "--batch",
            "--crawl=1"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
    except Exception as e:
        output = f"Erreur lors de l'exécution de SQLMap : {e}"
    return output
