import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class MultiModalDuelingDQN(nn.Module):
    def __init__(self, image_shape, feature_dim, num_actions):
        """
        image_shape: tuple, e.g., (3, 84, 84) for an RGB image
        feature_dim: dimension of the feature vector (e.g., 4)
        num_actions: number of possible actions
        """
        super(MultiModalDuelingDQN, self).__init__()
        # Convolutional part
        self.conv = nn.Sequential(
            nn.Conv2d(image_shape[0], 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU()
        )
        conv_out_size = self._get_conv_out(image_shape)
        # Feature processing
        self.feature_fc = nn.Sequential(
            nn.Linear(feature_dim, 64),
            nn.ReLU()
        )
        # Merge both vectors
        total_dim = conv_out_size + 64
        
        # Value branch
        self.fc_value = nn.Sequential(
            nn.Linear(total_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )
        # Advantage branch
        self.fc_advantage = nn.Sequential(
            nn.Linear(total_dim, 256),
            nn.ReLU(),
            nn.Linear(256, num_actions)
        )
        
    def _get_conv_out(self, shape):
        o = self.conv(torch.zeros(1, *shape))
        return int(np.prod(o.size()))
    
    def forward(self, image, features):
        image = image / 255.0  # Normalization
        conv_out = self.conv(image).reshape(image.size()[0], -1)
        feat_out = self.feature_fc(features)
        x = torch.cat([conv_out, feat_out], dim=1)
        value = self.fc_value(x)
        advantage = self.fc_advantage(x)
        # Combine Value and Advantage to obtain Q-values
        q = value + (advantage - advantage.mean(dim=1, keepdim=True))
        return q

class DQNAgent:
    def __init__(self, image_shape, feature_dim, num_actions, device):
        """
        image_shape: tuple, e.g., (3, 84, 84)
        feature_dim: dimension of features (e.g., 4)
        num_actions: number of possible actions
        device: 'cpu' or 'cuda'
        """
        self.device = device
        self.num_actions = num_actions
        self.feature_dim = feature_dim
        self.model = MultiModalDuelingDQN(image_shape, feature_dim, num_actions).to(device)
        self.target_model = MultiModalDuelingDQN(image_shape, feature_dim, num_actions).to(device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.95  # Gamma adjusted for immediate reward emphasis
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.1
        self.update_target_every = 1000
        self.step_count = 0
        
    def choose_action(self, state):
        self.step_count += 1
        if random.random() < self.epsilon:
            return random.randint(0, self.num_actions - 1)
        image = torch.FloatTensor(state["image"]).to(self.device).unsqueeze(0).permute(0,3,1,2)
        features = torch.FloatTensor(state["features"]).to(self.device).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(image, features)
        return q_values.argmax().item()
        
    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        
    def update(self):
        if len(self.memory) < self.batch_size:
            return
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        images = torch.FloatTensor(np.array([s["image"] for s in states])).to(self.device).permute(0,3,1,2)
        features = torch.FloatTensor(np.array([s["features"] for s in states])).to(self.device)
        
        next_images = torch.FloatTensor(np.array([s["image"] for s in next_states])).to(self.device).permute(0,3,1,2)
        next_features = torch.FloatTensor(np.array([s["features"] for s in next_states])).to(self.device)
        
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        q_values = self.model(images, features)
        q_value = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Double DQN: next action selected by the online model
        with torch.no_grad():
            next_actions = self.model(next_images, next_features).argmax(dim=1)
            next_q_values = self.target_model(next_images, next_features)
            next_q_value = next_q_values.gather(1, next_actions.unsqueeze(1)).squeeze(1)
            expected_q_value = rewards + self.gamma * next_q_value * (1 - dones)
            
        loss = nn.MSELoss()(q_value, expected_q_value)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        if self.step_count % self.update_target_every == 0:
            self.target_model.load_state_dict(self.model.state_dict())
