# gobuster_integration.py
import subprocess

def run_gobuster(target_url, wordlist_path, mode="dir", additional_args=None):
    """
    Runs GoBuster on the target URL using the specified wordlist.
    Returns a list of discovered full URLs.
    """
    gobuster_exe = r"/bin/gobuster"
    
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
        print(f"Error while running GoBuster: {e}")
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
