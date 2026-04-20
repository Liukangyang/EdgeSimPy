import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from torch.nn.functional import softmax

from .net import Net
from .replay_buffer import  ReplayBuffer
from .net import PolicyNet
from .net import CriticNet
'''
DDPG定义
'''
class DDPG:
    ''' DDPG算法 '''
    def __init__(self, state_dim, hidden_dim, action_dim, action_bound, sigma, actor_lr, critic_lr, tau, gamma,memory_size,batch_size,device):
        self.actor = PolicyNet(state_dim, hidden_dim, action_dim, action_bound).to(device)
        self.critic = CriticNet(state_dim+action_dim, hidden_dim, action_dim).to(device)
        self.target_actor = PolicyNet(state_dim, hidden_dim, action_dim, action_bound).to(device)
        self.target_critic = CriticNet(state_dim+action_dim, hidden_dim, action_dim).to(device)
        # 初始化目标价值网络并设置和价值网络相同的参数
        self.target_critic.load_state_dict(self.critic.state_dict())
        # 初始化目标策略网络并设置和策略相同的参数
        self.target_actor.load_state_dict(self.actor.state_dict())

        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=critic_lr)
        self.gamma = gamma
        self.sigma = sigma  # 高斯噪声的标准差,均值直接设为0
        self.tau = tau  # 目标网络软更新参数
        self.action_dim = action_dim
        self.device = device

        #经验池
        self.memory = ReplayBuffer(memory_size)
        self.batch_size = batch_size

    def choose_action(self, state):
        state = torch.tensor([state], dtype=torch.float).to(self.device)
        action_tensor = self.actor(state) #输出概率值
        # 给动作添加噪声，增加探索
        #TODO：待考虑sigma衰减
        action = (action_tensor.detach().cpu().numpy() + self.sigma * np.random.randn(self.action_dim))[0]
        #动作映射
        probs = torch.softmax(action_tensor, dim=1).detach().cpu().numpy()[0]
        map_action = np.argmax(probs) #选取概率最大的动作
        return action,map_action #返回动作概率和当前概率最大动作

    # 存储样本
    def store_transition(self, s, a, r, s_,done):
        self.memory.add(s, a, r, s_,done)

    def soft_update(self, net, target_net):
        for param_target, param in zip(target_net.parameters(), net.parameters()):
            param_target.data.copy_(param_target.data * (1.0 - self.tau) + param.data * self.tau)

    def learn(self):
        transition_dict = self.memory.sample(batch_size=self.batch_size)
        states = torch.tensor(np.array(transition_dict['states']), dtype=torch.float).to(self.device)
        actions = torch.tensor(np.array(transition_dict['actions']), dtype=torch.float).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'], dtype=torch.float).view(-1, 1).to(self.device)
        next_states = torch.tensor(np.array(transition_dict['next_states']), dtype=torch.float).to(self.device)
        dones = torch.tensor(transition_dict['dones'], dtype=torch.float).view(-1, 1).to(self.device)

        #在计算目标值的Q值时，最新状态的动作是由当前的actor目标网络得到的
        next_q_values = self.target_critic(next_states, self.target_actor(next_states))
        q_targets = rewards + self.gamma * next_q_values * (1 - dones)
        critic_loss = torch.mean(F.mse_loss(self.critic(states, actions), q_targets))
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # - Q(s,a)  ,a为当前策略函数的输出
        actor_loss = -torch.mean(self.critic(states, self.actor(states)))
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        self.soft_update(self.actor, self.target_actor)  # 软更新策略网络
        self.soft_update(self.critic, self.target_critic)  # 软更新价值网络

        return critic_loss.item(),actor_loss.item()


    # 保存模型
    def save_model(self,model_path):
        torch.save(self.actor.state_dict(), model_path)

    # 导入模型
    def load_model(self,model_path):
        state_dict = torch.load(model_path,map_location=torch.device('cpu'))
        self.actor.load_state_dict(state_dict)
