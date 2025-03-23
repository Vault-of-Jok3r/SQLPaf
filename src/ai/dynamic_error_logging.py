#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

SQL_ERRORS_FILE = "sql_errors.txt"

def load_known_errors():
    """
    Reads the sql_errors.txt file and returns a list of known errors.
    Ignores empty lines or lines starting with '#' (comments).
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
    Adds the new error (string) to sql_errors.txt,
    if it's not already there. Converts to lowercase to avoid duplicates.
    """
    new_error_lower = new_error.lower()
    # Re-read the file first to ensure the error isn't already present
    current_errors = load_known_errors()
    if new_error_lower not in current_errors:
        with open(SQL_ERRORS_FILE, "a", encoding="utf-8") as f:
            f.write(new_error_lower + "\n")
        print(f"[+] New SQL error added to {SQL_ERRORS_FILE}: {new_error_lower}")
    else:
        print(f"[-] SQL error already known: {new_error_lower}")

def detect_sql_errors(page_content, known_errors):
    """
    Searches page_content for known SQL error strings.
    Returns the list of errors found.
    """
    content_lower = page_content.lower()
    errors_found = []

    for err in known_errors:
        if err in content_lower:
            errors_found.append(err)

    return errors_found

def analyze_page(page_content):
    """
    Example analysis of a page after form submission:
    1) Loads the known error list.
    2) Detects which errors are present in the content.
    3) Optionally logs new errors if unexpected patterns are detected.
    """
    known_errors = load_known_errors()
    detected_errors = detect_sql_errors(page_content, known_errors)

    if detected_errors:
        for err in detected_errors:
            print(f"[!] SQL error detected: {err}")
    else:
        print("[-] No known SQL errors detected.")

    # Simple heuristic example for potentially detecting new error messages:
    # Searches for the word "error" in the page, and if an unknown occurrence is found,
    # adds it as a new error. 
    # WARNING: This approach is very basic and might generate noise.
    if "error" in page_content.lower() and not detected_errors:
        # You could extract a portion of text around "error" for improvement
        new_error = "some new error signature"
        add_error_to_file(new_error)

def main():
    """
    Demo: assuming we've retrieved the page content
    after injecting an SQL payload and submitting a form.
    """
    simulated_page_content = """
    <html>
      <body>
        <h1>Error executing query: You have an error in your MySQL syntax</h1>
        <p>Failure is always an option and this situation proves it</p>
      </body>
    </html>
    """
    # Analyze this content to detect and potentially log
    # new error messages.
    analyze_page(simulated_page_content)

if __name__ == "__main__":
    main()
