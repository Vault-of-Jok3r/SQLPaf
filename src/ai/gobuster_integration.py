# gobuster_integration.py
import subprocess

def run_gobuster(target_url, wordlist_path, mode="dir", additional_args=None):
    """
    Lance GoBuster sur l'URL cible en utilisant le dictionnaire spécifié.
    Retourne une liste d'URLs complètes découvertes.
    """
    gobuster_exe = r"/usr/bin/gobuster"
    
    command = [
        gobuster_exe, mode, 
        "-u", target_url, 
        "-w", wordlist_path
    ]
    if additional_args:
        command.extend(additional_args)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        output = result.stdout
    except Exception as e:
        print(f"Erreur lors de l'exécution de GoBuster : {e}")
        return []
    
    urls = []
    for line in output.splitlines():
        if "Found:" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("/"):
                    if target_url.endswith("/") and part.startswith("/"):
                        full_url = target_url[:-1] + part
                    else:
                        full_url = target_url + part
                    urls.append(full_url)
                    break
    return urls