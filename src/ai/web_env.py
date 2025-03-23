#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gym
from gym import spaces
import numpy as np
import logging
import os
import time
import io
from PIL import Image

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Logging configuration
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Paths to configuration files for SQL payloads and errors
SQL_ERRORS_FILE = "bin/payloads/sql_errors.txt"
SQL_PAYLOADS_FILE = "bin/payloads/sql_payloads.txt"

# --- Dynamic Management of SQL Errors ---

def load_known_errors():
    """
    Reads the SQL_ERRORS_FILE and returns a list of known SQL errors.
    Ignores empty lines and those starting with '#'.
    """
    known_errors = []
    if os.path.isfile(SQL_ERRORS_FILE):
        try:
            with open(SQL_ERRORS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        known_errors.append(line.lower())
        except Exception as e:
            logging.error(f"Error reading {SQL_ERRORS_FILE}: {e}")
    else:
        logging.warning(f"SQL errors file not found: {SQL_ERRORS_FILE}")
    return known_errors

def add_error_to_file(new_error):
    """
    Adds a new SQL error to the file if it doesn't already exist.
    """
    new_error_lower = new_error.lower()
    current_errors = load_known_errors()
    if new_error_lower not in current_errors:
        try:
            with open(SQL_ERRORS_FILE, "a", encoding="utf-8") as f:
                f.write(new_error_lower + "\n")
            logging.info(f"New SQL error added: {new_error_lower}")
        except Exception as e:
            logging.error(f"Error writing to {SQL_ERRORS_FILE}: {e}")
    else:
        logging.info(f"SQL error already known: {new_error_lower}")

def detect_sql_errors(page_content, known_errors):
    """
    Checks page_content for any known errors in known_errors.
    Returns a list of matched errors.
    """
    content_lower = page_content.lower()
    return [err for err in known_errors if err in content_lower]

def analyze_page(page_content):
    """
    Analyzes the page content for known SQL errors.
    If the word 'error' is present but no known error is matched,
    a new, unlisted error signature is added.
    """
    known_errors = load_known_errors()
    detected_errors = detect_sql_errors(page_content, known_errors)
    
    if detected_errors:
        for err in detected_errors:
            logging.warning(f"SQL error detected: {err}")
    else:
        logging.info("No known SQL errors detected.")
    
    if "error" in page_content.lower() and not detected_errors:
        new_error = "unlisted new error"
        add_error_to_file(new_error)
    
    return len(detected_errors)

# --- Loading Payloads from Text File ---

def load_payloads():
    """
    Reads the SQL_PAYLOADS_FILE and returns two lists: error_payloads and blind_payloads.
    Lines that are empty or start with '#' are ignored.
    The file is split into sections marked for error-based or blind payloads.
    """
    error_payloads = []
    blind_payloads = []
    mode = None  # 'error' or 'blind'
    
    if os.path.isfile(SQL_PAYLOADS_FILE):
        try:
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
        except Exception as e:
            logging.error(f"Error reading {SQL_PAYLOADS_FILE}: {e}")
    else:
        logging.error(f"Payloads file not found: {SQL_PAYLOADS_FILE}")
    
    return error_payloads, blind_payloads

def submit_form(form):
    """
    Attempts to submit the form by clicking the first submit button,
    or calling form.submit() if no buttons are found.
    """
    try:
        submit_buttons = form.find_elements(By.XPATH, ".//input[@type='submit'] | .//button[@type='submit']")
        if submit_buttons:
            submit_buttons[0].click()
        else:
            form.submit()
    except Exception as e:
        logging.error(f"Error submitting the form: {e}")

# --- Gym Environment for Web Exploration ---

class WebEnv(gym.Env):
    """
    Gym environment for web exploration using Selenium.

    Observation:
      - "image": resized screenshot (84x84) in RGB format (3 channels)
      - "features": a feature vector of size 4:
          [form_detected, number_of_forms, number_of_links, normalized_page_length]
    
    Discrete actions:
      0: Follow the first link.
      1: Scroll the page down.
      2: Check for a form and attempt an SQL injection.
      3: Go back to the previous page.
      4: Refresh the page.
    """
    def __init__(self, start_url="http://quotes.toscrape.com", headless=True, max_steps=100):
        super(WebEnv, self).__init__()
        self.start_url = start_url
        self.current_url = start_url
        self.max_steps = max_steps
        self.steps = 0
        self.max_links = 0  # For exploration bonus
        
        firefox_options = Options()
        if headless:
            firefox_options.add_argument("--headless")
        try:
            self.driver = webdriver.Firefox(options=firefox_options)
        except Exception as e:
            logging.error(f"Error launching Firefox driver: {e}")
            raise
        
        self.driver.get(self.start_url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        self.action_space = spaces.Discrete(5)
        # Observation: RGB image (84,84,3) + 4D feature vector
        self.observation_space = spaces.Dict({
            "image": spaces.Box(low=0, high=255, shape=(84,84,3), dtype=np.uint8),
            "features": spaces.Box(low=0, high=np.inf, shape=(4,), dtype=np.float32)
        })
    
    def _get_observation(self):
        """
        Captures a screenshot, resizes it to 84x84, converts it to an RGB array,
        and retrieves a 4D feature vector describing the page.
        """
        try:
            png = self.driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(png)).convert("RGB")
            image = image.resize((84,84))
            image = np.array(image)  # shape (84,84,3)
        except Exception as e:
            logging.error(f"Error capturing screenshot: {e}")
            image = np.zeros((84,84,3), dtype=np.uint8)
        features = self._get_features()
        return {"image": image, "features": features}
    
    def _get_features(self):
        """
        Computes the feature vector:
          - form_detected (1 or 0)
          - number of forms
          - number of links
          - normalized page length (length of HTML / 1000)
        """
        page_source = self.driver.page_source.lower()
        num_forms = page_source.count("<form")
        num_links = page_source.count("<a")
        form_detected = 1 if num_forms > 0 else 0
        page_length = len(page_source) / 1000.0
        return np.array([form_detected, num_forms, num_links, page_length], dtype=np.float32)
    
    def _detect_form(self):
        """
        Returns True if a <form> is present in the page source, otherwise False.
        """
        return "<form" in self.driver.page_source.lower()

    def perform_injection_test(self):
        """
        Attempts error-based SQL injection using payloads loaded from the file.
        Returns (success_bool, details_dict).
        """
        error_payloads, _ = load_payloads()
        known_sql_errors = load_known_errors()
        
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        if not forms:
            return False, "No form found"
        form = forms[0]
        inputs = form.find_elements(By.TAG_NAME, "input")
        if not inputs:
            return False, "No input fields in the form"
        
        injection_success = False
        injection_details = {}
        for payload in error_payloads:
            logging.info(f"Testing error-based payload: {payload}")
            for inp in inputs:
                input_type = inp.get_attribute("type")
                if input_type in ["submit", "button", "hidden"]:
                    continue
                try:
                    inp.clear()
                    inp.send_keys(payload)
                except Exception as e:
                    logging.error(f"Error filling an input field: {e}")
            submit_form(form)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except Exception as e:
                logging.warning(f"Timeout after form submission: {e}")
            page_content = self.driver.page_source.lower()
            for err in known_sql_errors:
                if err in page_content:
                    injection_success = True
                    injection_details = {"payload": payload, "error_detected": err}
                    break
            if injection_success:
                break
            # Reload the page to try the next payload
            self.driver.get(self.current_url)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except Exception as e:
                logging.warning(f"Error reloading the page: {e}")
        return injection_success, injection_details

    def step(self, action):
        """
        Executes the specified action. Returns (observation, reward, done, info).
        """
        done = False
        reward = 0
        info = {}
        self.steps += 1
        
        if action == 0:
            # Follow the first link
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                if links:
                    links[0].click()
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    self.current_url = self.driver.current_url
                    reward = 5
                else:
                    info['error'] = "No links found."
                    reward = -2
            except Exception as e:
                info['error'] = str(e)
                reward = -2
                logging.error(f"Error performing action 0: {e}")
        elif action == 1:
            # Scroll the page down
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                reward = 1
            except Exception as e:
                logging.error(f"Error scrolling the page: {e}")
                reward = -1
        elif action == 2:
            # Detect form and attempt SQL injection
            if self._detect_form():
                info['form_detected'] = True
                bonus_reward = 10  # Bonus for form detection
                injection_success, injection_details = self.perform_injection_test()
                info['injection'] = injection_details
                if injection_success:
                    reward = bonus_reward + 50
                    done = True
                else:
                    reward = bonus_reward - 3
            else:
                reward = -2
        elif action == 3:
            # Go back to the previous page
            try:
                self.driver.back()
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.current_url = self.driver.current_url
                reward = 2
            except Exception as e:
                logging.error(f"Error going back: {e}")
                reward = -2
        elif action == 4:
            # Refresh the page
            try:
                self.driver.refresh()
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.current_url = self.driver.current_url
                reward = 1
            except Exception as e:
                logging.error(f"Error refreshing the page: {e}")
                reward = -1

        # Exploration bonus: if the number of links exceeds the highest seen so far, grant a bonus.
        features = self._get_features()
        nb_links = features[2]
        if nb_links > self.max_links:
            bonus = 5
            reward += bonus
            logging.info(f"Exploration bonus (+{bonus}) because nb_links {nb_links} > max_links {self.max_links}")
            self.max_links = nb_links

        if self.steps >= self.max_steps:
            done = True
            logging.info("Maximum number of steps reached, ending episode.")

        obs = self._get_observation()
        return obs, reward, done, info
    
    def reset(self):
        """
        Resets the environment to the initial state (start_url).
        """
        self.steps = 0
        self.max_links = 0  # Reset exploration bonus
        self.driver.get(self.start_url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            logging.error(f"Error during reset: {e}")
        self.current_url = self.start_url
        return self._get_observation()
    
    def close(self):
        """
        Closes the Selenium browser session.
        """
        self.driver.quit()

if __name__ == "__main__":
    # Example of using the environment
    env = WebEnv(headless=True)
    obs = env.reset()
    done = False
    total_reward = 0
    while not done:
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        total_reward += reward
        logging.info(f"Action: {action}, Reward: {reward}, Info: {info}")
    logging.info(f"Total reward: {total_reward}")
    env.close()
