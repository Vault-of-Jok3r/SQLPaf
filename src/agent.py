# agent.py
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class DQN(nn.Module):
    def __init__(self, input_shape, num_actions):
        super(DQN, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(input_shape[0], 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU()
        )
        conv_out_size = self._get_conv_out(input_shape)
        self.fc = nn.Sequential(
            nn.Linear(conv_out_size, 512),
            nn.ReLU(),
            nn.Linear(512, num_actions)
        )
        
    def _get_conv_out(self, shape):
        # Calcul de la taille de sortie après les couches convolutionnelles
        o = self.conv(torch.zeros(1, *shape))
        return int(np.prod(o.size()))
    
    def forward(self, x):
        x = x / 255.0  # Normalisation
        conv_out = self.conv(x).reshape(x.size()[0], -1)  # Utilisation de reshape au lieu de view
        return self.fc(conv_out)

class DQNAgent:
    def __init__(self, state_shape, num_actions, device):
        self.device = device
        self.num_actions = num_actions
        self.model = DQN(state_shape, num_actions).to(device)
        self.target_model = DQN(state_shape, num_actions).to(device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.1
        self.update_target_every = 1000
        self.step_count = 0
        
    def choose_action(self, state):
        self.step_count += 1
        if random.random() < self.epsilon:
            return random.randint(0, self.num_actions - 1)
        # Conversion de l'observation en tenseur (de HWC à CHW)
        state = torch.FloatTensor(state).to(self.device).unsqueeze(0).permute(0,3,1,2)
        with torch.no_grad():
            q_values = self.model(state)
        return q_values.argmax().item()
        
    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        
    def update(self):
        if len(self.memory) < self.batch_size:
            return
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.device).permute(0,3,1,2)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device).permute(0,3,1,2)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        q_values = self.model(states)
        q_value = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        with torch.no_grad():
            next_q_values = self.target_model(next_states)
            next_q_value = next_q_values.max(1)[0]
            expected_q_value = rewards + self.gamma * next_q_value * (1 - dones)
            
        loss = nn.MSELoss()(q_value, expected_q_value)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        if self.step_count % self.update_target_every == 0:
            self.target_model.load_state_dict(self.model.state_dict())
