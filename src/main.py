#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Display the logo
try:
    with open("bin/logo/logo.txt", "r", encoding="utf-8") as logo:
        print(logo.read())
except FileNotFoundError:
    print("Logo not found.")

# Welcome message
print("Welcome to the SQL Penetration Asistant Framework!\n")

# Choice of test mode
print("Choose the test mode:")
print("1. Test on a single URL (Basic)")
print("2. Test on a list of URLs (via Gobuster)")
mode_choice = input("Your choice (1 or 2): ").strip()

# Create the bin/temp directory if it doesn't exist
os.makedirs("bin/temp", exist_ok=True)

if mode_choice == "1":
    # Basic mode: test on a single URL
    url = input("Enter the URL to test: ").strip()
    # Save the URL to bin/temp/domain.txt
    with open("bin/temp/domain.txt", "w", encoding="utf-8") as f:
        f.write(url)
    # For this mode, the wordlist is not used: we save an empty file
    with open("bin/temp/wordlist.txt", "w", encoding="utf-8") as f:
        f.write("")
    mode = "basic"
elif mode_choice == "2":
    # URL list mode: test on a domain using a wordlist
    domain = input("Enter the domain: ").strip()
    with open("bin/temp/domain.txt", "w", encoding="utf-8") as f:
        f.write(domain)
    
    # Wordlist selection
    wordlist_dir = "bin/wordlists"
    try:
        wordlists = os.listdir(wordlist_dir)
    except FileNotFoundError:
        print("Wordlist directory not found.")
        sys.exit(1)
    
    print("\nSelect a wordlist:\n")
    for index, filename in enumerate(wordlists, 1):
        print(f"{index}. {filename}")
    
    while True:
        choice = input("\nYour choice: ").strip()
        try:
            choice_int = int(choice)
            if 1 <= choice_int <= len(wordlists):
                selected_wordlist = os.path.join(wordlist_dir, wordlists[choice_int - 1])
                break
            else:
                print("Invalid entry, please try again.")
        except ValueError:
            print("Invalid entry, please try again.")
    
    # Convert the path to POSIX format
    selected_wordlist_posix = Path(selected_wordlist).as_posix()
    with open("bin/temp/wordlist.txt", "w", encoding="utf-8") as f:
        f.write(selected_wordlist_posix)
    mode = "ml"
else:
    print("Invalid choice. Please rerun the script and choose 1 or 2.")
    sys.exit(1)

print("Starting the scan...\n")
subprocess.run([sys.executable, "src/ai/scan_url.py", mode])
