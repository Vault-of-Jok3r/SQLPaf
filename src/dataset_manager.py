# dataset_manager.py

# Dataset 1 : toutes les URLs découvertes par GoBuster
DATASET_URLS = []

# Dataset 2 : uniquement les URLs où un formulaire a été détecté
DATASET_FORM_URLS = []

def add_urls(new_urls):
    """
    Ajoute les URLs de new_urls au dataset global DATASET_URLS si elles n'y figurent pas déjà.
    Retourne le nombre de nouvelles URLs ajoutées.
    """
    global DATASET_URLS
    count_new = 0
    for url in new_urls:
        if url not in DATASET_URLS:
            DATASET_URLS.append(url)
            count_new += 1
    return count_new

def add_form_url(url):
    """
    Ajoute l'URL au dataset global DATASET_FORM_URLS si elle n'y est pas déjà.
    Retourne 1 si ajoutée, 0 sinon.
    """
    global DATASET_FORM_URLS
    if url not in DATASET_FORM_URLS:
        DATASET_FORM_URLS.append(url)
        return 1
    return 0

def get_dataset():
    """Retourne le dataset complet de toutes les URLs."""
    return DATASET_URLS

def get_form_dataset():
    """Retourne le dataset des URLs où un formulaire a été détecté."""
    return DATASET_FORM_URLS
