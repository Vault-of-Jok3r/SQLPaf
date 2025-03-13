# main.py
import numpy as np
import torch
from web_env import WebEnv
from agent import DQNAgent
import time

def preprocess_observation(obs):
    # Ici, l'observation est déjà sous forme d'image de taille 84x84 avec 3 canaux (HWC)
    return obs

def main():
    # Initialisation de l'environnement (URL de départ)
    env = WebEnv(start_url="http://quotes.toscrape.com/login")
    
    state = env.reset()
    state = preprocess_observation(state)
    num_actions = env.action_space.n
    # Correction : passez la forme avec les canaux en premier pour initialiser le DQN
    state_shape = (3, 84, 84)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = DQNAgent(state_shape, num_actions, device)
    
    num_episodes = 10      # Nombre d'épisodes pour l'entraînement
    max_steps = 50         # Nombre maximum d'étapes par épisode (pour ce prototype)
    
    for episode in range(num_episodes):
        state = env.reset()
        state = preprocess_observation(state)
        total_reward = 0
        for step in range(max_steps):
            action = agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            next_state = preprocess_observation(next_state)
            total_reward += reward
            agent.store_transition(state, action, reward, next_state, done)
            agent.update()
            state = next_state
            print(f"Episode {episode+1}, Step {step+1}, Action {action}, Reward {reward}, Info: {info}")
            if done:
                break
        print(f"Episode {episode+1} total reward: {total_reward}")
    env.close()

if __name__ == "__main__":
    main()
