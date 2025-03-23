#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import requests
import asyncio
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from pathlib import Path

# Configuration file paths
SQL_ERRORS_FILE = "bin/payloads/sql_errors.txt"
SQL_PAYLOADS_FILE = "bin/payloads/sql_payloads.txt"

# --- Dynamic Management of SQL Errors ---

def load_known_errors():
    """
    Reads the sql_errors.txt file and returns the list of already known SQL errors.
    Ignores empty lines or commented lines (those that start with '#').
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
    Adds the new_error string to sql_errors.txt if it is not already in there.
    """
    new_error_lower = new_error.lower()
    current_errors = load_known_errors()
    if new_error_lower not in current_errors:
        with open(SQL_ERRORS_FILE, "a", encoding="utf-8") as f:
            f.write(new_error_lower + "\n")
        print(f"[+] New SQL error added to {SQL_ERRORS_FILE}: {new_error_lower}")
    else:
        print(f"[-] SQL error already known: {new_error_lower}")

def detect_sql_errors(page_content, known_errors):
    """
    Searches for known SQL errors in page_content.
    Returns a list of detected errors.
    """
    content_lower = page_content.lower()
    found_errors = []
    for err in known_errors:
        if err in content_lower:
            found_errors.append(err)
    return found_errors

def analyze_page(page_content):
    """
    Analyzes the page content to detect known SQL errors.
    If no known error is detected but the word 'error' is present,
    a new signature is added (in this simplified example).
    """
    known_errors = load_known_errors()
    detected_errors = detect_sql_errors(page_content, known_errors)
    
    if detected_errors:
        for err in detected_errors:
            print(f"[!] SQL error detected: {err}")
    else:
        print("[-] No known SQL error detected.")
    
    if "error" in page_content.lower() and not detected_errors:
        new_error = "unlisted new error"
        add_error_to_file(new_error)
    
    return len(detected_errors)

# --- Loading Payloads from the Text File ---

def load_payloads():
    """
    Reads the sql_payloads.txt file and returns two lists:
      - error_payloads for error-based injections
      - blind_payloads for time-based (blind) injections
    Empty lines and those starting with '#' are ignored.
    Separation is based on markers in the file.
    """
    error_payloads = []
    blind_payloads = []
    mode = None  # 'error' or 'blind'
    
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
        print(f"[!] Payloads file {SQL_PAYLOADS_FILE} not found.")
    
    return error_payloads, blind_payloads

def submit_form(form):
    """
    Attempts to submit the form by clicking the first 'submit' button;
    otherwise, uses form.submit().
    """
    try:
        submit_buttons = form.find_elements(By.XPATH, ".//input[@type='submit'] | .//button[@type='submit']")
        if submit_buttons:
            submit_buttons[0].click()
        else:
            form.submit()
    except Exception as e:
        print(f"[!] Error during form submission: {e}")

# --- Injection Testing with Score per URL ---

def test_injections_on_forms(url):
    print(f"[*] Starting injection tests on: {url}")
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    
    score = {
        "form_detected": 0,
        "form_not_detected": 0,
        "injection_success": 0,
        "injection_failure": 0,
        "error_messages": 0
    }
    
    try:
        driver.get(url)
        time.sleep(2)
        forms = driver.find_elements(By.TAG_NAME, "form")
        if not forms:
            print(f"[+] No form found on {url}")
            score["form_not_detected"] += 1
            driver.quit()
            print(f"--- Score for {url} ---")
            print(score)
            return score
        
        score["form_detected"] += len(forms)
        error_payloads, blind_payloads = load_payloads()
        if not error_payloads:
            print("[!] No error-based payload found.")
        if not blind_payloads:
            print("[!] No time-based (blind) payload found.")
        
        for form_index, form in enumerate(forms, start=1):
            print(f"[*] Testing form {form_index} on {url}")
            # Retrieve inputs from the form
            inputs = form.find_elements(By.TAG_NAME, "input")
            if not inputs:
                print(f"[!] No input fields found in form {form_index}")
                continue
            
            injection_successful = False
            # Error-based test
            for payload in error_payloads:
                print(f"[*] Error-based test with payload: {payload}")
                try:
                    current_inputs = form.find_elements(By.TAG_NAME, "input")
                    for inp in current_inputs:
                        if inp.get_attribute("type") in ["submit", "button", "hidden"]:
                            continue
                        try:
                            inp.clear()
                            inp.send_keys(payload)
                        except Exception as e:
                            print(f"[!] Error while filling an input field: {e}")
                    submit_form(form)
                    time.sleep(3)
                    page_content = driver.page_source
                    errors_count = analyze_page(page_content)
                    score["error_messages"] += errors_count
                    if errors_count > 0:
                        print(f"[!] Error-based injection successful with payload: {payload}")
                        injection_successful = True
                        score["injection_success"] += 1
                        break
                except Exception as e:
                    print(f"[!] Exception during error-based test: {e}")
            if not injection_successful:
                score["injection_failure"] += 1
            
            # Blind test
            for payload in blind_payloads:
                print(f"[*] Blind test with payload: {payload}")
                try:
                    # Re-fetch inputs to avoid stale elements
                    current_inputs = form.find_elements(By.TAG_NAME, "input")
                    for inp in current_inputs:
                        if inp.get_attribute("type") in ["submit", "button", "hidden"]:
                            continue
                        try:
                            inp.clear()
                            inp.send_keys(payload)
                        except Exception as e:
                            print(f"[!] Error while filling an input field (blind): {e}")
                            # In case of an error, try re-fetching inputs
                            current_inputs = form.find_elements(By.TAG_NAME, "input")
                            for inp in current_inputs:
                                if inp.get_attribute("type") in ["submit", "button", "hidden"]:
                                    continue
                                try:
                                    inp.clear()
                                    inp.send_keys(payload)
                                except Exception as e2:
                                    print(f"[!] Persistent error while filling (blind): {e2}")
                    start_time = time.time()
                    submit_form(form)
                    time.sleep(7)
                    elapsed = time.time() - start_time
                    print(f"[+] Blind test with payload '{payload}' for form {form_index} took {elapsed:.2f} seconds")
                    if elapsed > 4:
                        print(f"[!] Possible blind injection detected with payload '{payload}' in form {form_index}!")
                        score["injection_success"] += 1
                    else:
                        score["injection_failure"] += 1
                    errors_count = analyze_page(driver.page_source)
                    score["error_messages"] += errors_count
                except Exception as e:
                    print(f"[!] Exception during blind test with payload '{payload}': {e}")
                    score["injection_failure"] += 1
                driver.get(url)
                time.sleep(2)
                forms = driver.find_elements(By.TAG_NAME, "form")
                if len(forms) >= form_index:
                    form = forms[form_index - 1]
                    
    except Exception as e:
        print(f"[!] Error during injection tests on {url}: {e}")
    finally:
        driver.quit()
    
    print(f"--- Score for {url} ---")
    print(f"Forms detected           : {score['form_detected']}")
    print(f"Forms not detected       : {score['form_not_detected']}")
    print(f"Successful injections    : {score['injection_success']}")
    print(f"Failed injections        : {score['injection_failure']}")
    print(f"Total error messages     : {score['error_messages']}")
    return score

async def async_test_injections(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, test_injections_on_forms, url)

# --- Execution Modes ---

def single_url_mode():
    domain_path = "bin/temp/domain.txt"
    if not os.path.isfile(domain_path):
        print("[!] File not found: bin/temp/domain.txt")
        return
    with open(domain_path, "r", encoding="utf-8") as f:
        url = f.read().strip()
    print("=========================================")
    print(f"[*] Injection test on single URL: {url}")
    score = test_injections_on_forms(url)
    print(f"--- Summary for {url} ---")
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
        print(f"[!] File not found: {domain_path}")
        return
    with open(domain_path, "r", encoding="utf-8") as f:
        domain = f.read().strip()

    wordlist_path_file = "bin/temp/wordlist.txt"
    if not os.path.isfile(wordlist_path_file):
        print(f"[!] File not found: {wordlist_path_file}")
        return
    with open(wordlist_path_file, "r", encoding="utf-8") as f:
        wordlist_path = f.read().strip()

    if not wordlist_path:
        print("[!] Empty wordlist, please choose single URL mode.")
        return

    try:
        with open(wordlist_path, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[!] Error reading the wordlist: {e}")
        return

    print(f"[+] Domain : {domain}")
    print(f"[+] Wordlist : {wordlist_path}")
    print(f"[+] Number of paths to test : {len(paths)}")
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
                print(f"[+] Valid URL: {url} (HTTP 200)")
                if "<form" in response.text.lower():
                    print(f"[*] Form detected at {url}, scheduling injection test...")
                    injection_tasks.append(async_test_injections(url))
                else:
                    print(f"[-] No form detected at {url} (quick check).")
            else:
                print(f"[-] {url} => Status {response.status_code}")
        except requests.RequestException as req_err:
            print(f"[!] Network error for {url}: {req_err}")

    if injection_tasks:
        print("=========================================")
        print("[*] Starting asynchronous SQL injection tests on URLs with forms...")
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
        print("[+] No URL with a form was detected in this scan.")
    
    print("=========================================")
    print("--- Global Score ---")
    print(f"Forms detected           : {global_score['form_detected']}")
    print(f"Forms not detected       : {global_score['form_not_detected']}")
    print(f"Successful injections    : {global_score['injection_success']}")
    print(f"Failed injections        : {global_score['injection_failure']}")
    print(f"Total error messages     : {global_score['error_messages']}")

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
