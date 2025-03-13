# main.py
import time
from web_env import WebEnv
from agent import DQNAgent
from gobuster_integration import run_gobuster
from dataset_manager import add_urls, add_form_url, get_dataset, get_form_dataset
from form_checker import url_has_form
from sqlmap_multithread import run_sqlmap_multithread

def main():
    target_url = "http://quotes.toscrape.com"
    wordlist_path = r"C:\Users\adrie\Documents\SQLPaf V2.0\wordlist.txt"  # Chemin absolu vers votre wordlist

    # Lancer GoBuster pour alimenter initialement le dataset complet
    new_urls = run_gobuster(target_url, wordlist_path)
    count = add_urls(new_urls)
    print(f"Initialement, {count} nouvelles URLs ont été ajoutées au dataset complet.")
    
    # Vérifier pour chaque URL du dataset complet si un formulaire est présent
    dataset = get_dataset()
    for url in dataset:
        if url_has_form(url):
            add_form_url(url)
    print("Dataset des URLs avec formulaire détecté:", get_form_dataset())
    
    # Lancement multi-threadé de SQLMap sur le dataset des URLs avec formulaire
    form_dataset = get_form_dataset()
    if form_dataset:
        print("Lancement de SQLMap en multi-thread sur les URLs avec formulaire...")
        sqlmap_results = run_sqlmap_multithread(form_dataset, max_workers=5)
        for url, result in sqlmap_results.items():
            print(f"{url} : {result}")
    else:
        print("Aucune URL avec formulaire détecté dans le dataset.")

    # Exemple d'intégration avec l'agent RL (facultatif)
    env = WebEnv(start_url=target_url)
    state = env.reset()
    num_actions = env.action_space.n
    state_shape = (3, 84, 84)
    
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = DQNAgent(state_shape, num_actions, device)
    
    num_episodes = 10
    max_steps = 50
    
    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        for step in range(max_steps):
            action = agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store_transition(state, action, reward, next_state, done)
            agent.update()
            state = next_state
            print(f"Episode {episode+1}, Step {step+1}, Action {action}, Reward {reward}, Info: {info}")
            if done:
                break
        print(f"Episode {episode+1} total reward: {total_reward}")
        
        # Après chaque épisode, mettre à jour le dataset complet via GoBuster
        new_urls = run_gobuster(target_url, wordlist_path)
        count = add_urls(new_urls)
        print(f"Episode {episode+1}: {count} nouvelles URLs ajoutées au dataset complet.")
        
        # Vérifier les nouvelles URLs pour un formulaire et mettre à jour le dataset de formulaires
        dataset = get_dataset()
        for url in dataset:
            if url_has_form(url):
                add_form_url(url)
        print(f"Après l'épisode {episode+1}, dataset de formulaires : {get_form_dataset()}")
    
    env.close()
    
    # Lancement final de SQLMap en multi-thread sur l'ensemble du dataset de formulaires mis à jour
    form_dataset = get_form_dataset()
    if form_dataset:
        print("Lancement final de SQLMap en multi-thread sur l'ensemble du dataset de formulaires...")
        sqlmap_results = run_sqlmap_multithread(form_dataset, max_workers=5)
        for url, result in sqlmap_results.items():
            print(f"{url} : {result}")
    else:
        print("Aucune URL avec formulaire détecté dans le dataset final.")

if __name__ == "__main__":
    main()
