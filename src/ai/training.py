#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import torch
import requests
import time
import numpy as np
from torch.utils.tensorboard import SummaryWriter

from web_env import WebEnv
from agent import DQNAgent

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def gobuster_scan(base_url, wordlist_path="bin/wordlists/common.txt"):
    discovered_urls = []
    if not os.path.isfile(wordlist_path):
        print(f"[!] Wordlist not found: {wordlist_path}")
        return discovered_urls
    with open(wordlist_path, "r", encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]
    base_url = base_url.rstrip("/")
    print("[*] Starting Gobuster scan...")
    for path in paths:
        url = base_url + (path if path.startswith("/") else "/" + path)
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                if "<form" in response.text.lower():
                    print(f"[+] Form detected at {url}")
                    discovered_urls.append(url)
                else:
                    print(f"[-] No form at {url}")
            else:
                print(f"[-] {url} => Status {response.status_code}")
        except Exception as e:
            print(f"[!] Error while scanning {url}: {e}")
    print("[*] Gobuster scan completed.")
    return discovered_urls

def train_dqn_agent_on_url(env, agent, url, num_episodes=20, max_steps=200,
                           save_checkpoint_interval=5, checkpoint_dir="bin/checkpoints",
                           log_dir="bin/runs/experiment_mutillidae"):
    writer = SummaryWriter(log_dir=log_dir)
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    env.driver.get(url)
    time.sleep(1)
    env.current_url = url

    total_reward_all_episodes = 0.0

    for episode in range(num_episodes):
        env.driver.get(url)
        time.sleep(1)
        state = env._get_observation()
        episode_reward = 0.0

        for step in range(max_steps):
            action = agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store_transition(state, action, reward, next_state, done)
            agent.update()
            state = next_state
            episode_reward += reward
            if done:
                break

        total_reward_all_episodes += episode_reward
        print(f"[URL: {url}] [Episode {episode+1}/{num_episodes}] Total reward: {episode_reward}")
        writer.add_scalar("EpisodeReward", episode_reward, episode)
        
        if (episode + 1) % save_checkpoint_interval == 0:
            ckpt_name = url.replace("http://", "").replace("/", "_")
            checkpoint_path = os.path.join(checkpoint_dir, f"model_{ckpt_name}_ep{episode+1}.pth")
            torch.save(agent.model.state_dict(), checkpoint_path)
            print(f"[*] Checkpoint saved: {checkpoint_path}")

    average_reward = total_reward_all_episodes / num_episodes
    print(f"\n=== Training Summary for URL: {url} ===")
    print(f"Total accumulated score: {total_reward_all_episodes}")
    print(f"Average score per episode: {average_reward:.2f}")

    if average_reward < 10:
        print("Insufficient performance. SQLPaf will need to do better next time.")
    elif average_reward < 30:
        print("Average performance. There is room for improvement.")
    else:
        print("Excellent performance! SQLPaf learned well on this URL.")

    writer.close()

def main():
    base_url = "http://192.168.81.129/mutillidae"
    discovered_urls = gobuster_scan(base_url, wordlist_path="bin/wordlists/common.txt")
    if not discovered_urls:
        print("[!] No URL with a form was detected during the scan.")
        return

    env = WebEnv(start_url=base_url)
    num_actions = env.action_space.n
    image_shape = (3, 84, 84)
    feature_dim = 4  # [form_detected, nb_forms, nb_links, normalized_page_length]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("[*] Training on device:", device)
    agent = DQNAgent(image_shape, feature_dim, num_actions, device)

    for url in discovered_urls:
        print(f"[*] Training on URL: {url}")
        train_dqn_agent_on_url(env, agent, url, num_episodes=20, max_steps=200,
                               save_checkpoint_interval=5,
                               checkpoint_dir="bin/checkpoints",
                               log_dir="bin/runs/experiment_mutillidae")
    
    env.close()

if __name__ == "__main__":
    main()
