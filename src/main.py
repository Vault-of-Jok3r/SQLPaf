import os
import sys
import subprocess
from pathlib import Path

# Affichage du logo
with open("bin/logo/logo.txt", "r", encoding="utf-8") as logo:
    print(logo.read())

# Demande du domaine
domain = input("Enter the domain: ")

# Définition du répertoire contenant les wordlists
wordlist_dir = "bin/wordlists"
wordlists = os.listdir(wordlist_dir)

# Affichage des wordlists disponibles
print("\nSelect a wordlist:\n")
for index, filename in enumerate(wordlists, 1):
    print(f"{index}. {filename}")

# Boucle jusqu'à obtenir un choix valide
while True:
    choice = input("\nSelect a wordlist: ")
    try:
        choice = int(choice)
        if 1 <= choice <= len(wordlists):
            # Construction du chemin avec os.path.join()
            selected_wordlist = os.path.join(wordlist_dir, wordlists[choice - 1])
            break
        else:
            print("\nInvalid input, please try again.")
    except ValueError:
        print("\nInvalid input, please try again.")

# Conversion du chemin en format POSIX pour avoir des '/'
selected_wordlist_posix = Path(selected_wordlist).as_posix()

print(f"\nSelected wordlist: {selected_wordlist_posix}\n")

# Création du répertoire bin/temp s'il n'existe pas
os.makedirs("bin/temp", exist_ok=True)

# Enregistrement du domaine dans bin/temp/domain.txt
with open("bin/temp/domain.txt", "w", encoding="utf-8") as domain_file:
    domain_file.write(domain)

# Enregistrement du chemin de la wordlist (format POSIX) dans bin/temp/wordlist.txt
with open("bin/temp/wordlist.txt", "w", encoding="utf-8") as wordlist_file:
    wordlist_file.write(selected_wordlist_posix)

print("Proceeding...\n")

# Lancement du script src/gobuster/gobuster.py
subprocess.run([sys.executable, "src/ai/main.py"])