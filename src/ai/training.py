#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import torch
from torch.utils.tensorboard import SummaryWriter

# Importe ton agent DQN existant
from agent import DQNAgent
# Importe ton environnement simulé ou local
from web_env import WebEnv

def train_dqn_agent(env, agent, num_episodes=10, max_steps=50,
                    save_checkpoint_interval=5, checkpoint_dir="checkpoints",
                    log_dir="runs/experiment1"):
    """
    Boucle d'entraînement DQN pour 'env' et 'agent'.
    - num_episodes : nombre d'épisodes d'entraînement
    - max_steps : nb de steps max par épisode
    - save_checkpoint_interval : fréquence (en épisodes) de sauvegarde du modèle
    - checkpoint_dir : dossier pour sauvegarder les checkpoints
    - log_dir : dossier pour les logs TensorBoard
    """

    writer = SummaryWriter(log_dir=log_dir)
    os.makedirs(checkpoint_dir, exist_ok=True)

    total_steps = 0

    for episode in range(num_episodes):
        # Réinitialisation de l'environnement, obtient l'état initial
        state = env.reset()
        episode_reward = 0.0

        for step in range(max_steps):
            total_steps += 1

            # L'agent choisit une action (epsilon-greedy)
            action = agent.choose_action(state)

            # Exécute l'action dans l'env
            next_state, reward, done, info = env.step(action)

            # Stocker la transition
            agent.store_transition(state, action, reward, next_state, done)

            # Mise à jour du réseau Q (batch training)
            agent.update()

            # Mettre à jour l'état et la récompense cumulée
            state = next_state
            episode_reward += reward

            # Fin d'épisode si done
            if done:
                break

        # Affiche la récompense totale de l'épisode
        print(f"[Episode {episode+1}/{num_episodes}] Reward total: {episode_reward}")
        # Log dans TensorBoard
        writer.add_scalar("EpisodeReward", episode_reward, episode)

        # Sauvegarde du modèle à intervalles réguliers
        if (episode + 1) % save_checkpoint_interval == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f"model_ep{episode+1}.pth")
            torch.save(agent.model.state_dict(), checkpoint_path)
            print(f"Checkpoint sauvegardé: {checkpoint_path}")

    # Sauvegarde finale
    final_path = os.path.join(checkpoint_dir, "model_final.pth")
    torch.save(agent.model.state_dict(), final_path)
    print(f"Modèle final sauvegardé: {final_path}")

    writer.close()


def main():
    """
    Script principal d'entraînement :
    - Création d'un WebEnv (lab local)
    - Instanciation de l'agent DQN
    - Entraînement sur num_episodes épisodes
    """

    # Exemple: un environnement local, ex. DVWA sur 127.0.0.1
    start_url = "http://127.0.0.1/dvwa"

    # Créer l'environnement
    env = WebEnv(start_url=start_url)
    num_actions = env.action_space.n

    # Selon l'agent, si l'état correspond à des images 84x84 en RGB : shape (3, 84, 84)
    # Sinon, adapter si l'état est un vecteur / features.
    state_shape = (3, 84, 84)

    # Choix CPU/GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Entraînement sur le device:", device)

    # Instancier ton DQNAgent déjà défini dans agent.py
    agent = DQNAgent(state_shape, num_actions, device)

    # Lancement de l'entraînement
    train_dqn_agent(
        env=env,
        agent=agent,
        num_episodes=10,         # Ajuste selon besoin
        max_steps=50,           # Ajuste le nb de steps max par épisode
        save_checkpoint_interval=5,
        checkpoint_dir="checkpoints",
        log_dir="runs/dqn_training"
    )

    env.close()

if __name__ == "__main__":
    main()

