import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from .net import Net
from .replay_buffer import  ReplayBuffer


# DQN结构定义
'''
DQN网络类
主要定义DQN网络的结构和接口
'''
class DQN():
    def __init__(self, n_actions, n_features, n_hidden=40, learning_rate=0.01, gamma=0.9, e_greedy=0.9,
                 update_T=200, memory_size=10000, batch_size=500,
                 epsilon_start=1, epsilon_end=0.1,epsilon_decay=500,
                 device=None):

        self.device = device
        self.n_actions = n_actions  #动作维度
        self.n_features = n_features  #状态维度
        self.n_hidden = n_hidden  #隐藏层神经元数量
        self.lr = learning_rate  # 优化器使用
        self.gamma = gamma #折扣因子
        self.epsilon_max = e_greedy  #e贪婪策略
        self.update_T = update_T #评估网络训练周期
        self.memory_size = memory_size #经验池大小
        self.batch_size = batch_size   #批大小-每次训练的样本大小

        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.epsilon = epsilon_start

        # 训练步数
        self.learning_steps = 0

        # 初始化经验回放池(s,a,r,s')
        self.memory = ReplayBuffer(memory_size)

        # 评估网络，目标网络
        self.q_eval, self.q_target = self.build_net()

        # 优化器：Adam优化器
        self.optimizer = torch.optim.Adam(self.q_eval.parameters(), lr=self.lr)

        # 损失函数：MSE均方误差函数
        self.loss_func = nn.MSELoss().to(self.device)
        # 损失记录
        self.cost_list = []
        #计数器
        self.steps_done_custom = 0


    # 构建目标和评估网络
    def build_net(self):
        q_eval = Net(self.n_features, self.n_hidden, self.n_actions).to(self.device)
        q_target = Net(self.n_features, self.n_hidden, self.n_actions).to(self.device)
        q_target.load_state_dict(q_eval.state_dict())
        return q_eval, q_target

    # 存储样本
    def store_transition(self, s, a, r, s_,done):
        self.memory.add(s, a, r, s_,done)


    # 选择动作
    def take_action(self, observation):
        # 先转换observation的类型
        observation = torch.tensor(observation,dtype=torch.float).to(self.device)
        # e-贪婪策略
        #更新epsilon参数
        #根据衰减公式计算当前的 \(\epsilon\) 值
        self.epsilon = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
                                math.exp(-1. * self.steps_done_custom / self.epsilon_decay)
        if np.random.random() >= self.epsilon:
            # 选取Q值最大的动作(由评估网络选取动作)
            action = self.q_eval(observation).argmax().item()
        else:  # 随机选取
            action = np.random.randint(self.n_actions)

        self.steps_done_custom += 1  # 增加全局步数计数器
        return action

    #TODO：核心步骤-网络训练
    def learn(self):

        transition_dict = self.memory.sample(self.batch_size)
        # 转化为tensor
        states = torch.tensor(transition_dict['states'], dtype=torch.float).to(self.device)
        actions = torch.tensor(transition_dict['actions']).view(-1, 1).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'], dtype=torch.float).view(-1, 1).to(self.device)
        next_states = torch.tensor(transition_dict['next_states'], dtype=torch.float).to(self.device)
        dones = torch.tensor(transition_dict['dones'], dtype=torch.float).view(-1, 1).to(self.device)

        # 训练
        q_values = self.q_eval(states).gather(1,actions)  #Q(s,a)
        # 下个状态的最大Q值
        max_next_q_values = self.q_target(next_states).max(1)[0].view(-1,1)
        q_targets = rewards + self.gamma * max_next_q_values * (1 - dones)  # TD误差目标

        #计算损失值
        loss = torch.mean(F.mse_loss(q_values, q_targets)) #

        #梯度重置为0
        self.optimizer.zero_grad()
        #反向传播调整网络参数
        loss.backward()
        #梯度下降
        self.optimizer.step()


        self.learning_steps += 1
        # 判断是否对目标网络进行更新
        if (self.learning_steps ) % self.update_T == 0:
                self.update_Target()

        return loss.item()

    # 更新目标网络参数
    def update_Target(self):
        self.q_target.load_state_dict(self.q_eval.state_dict())


    # 保存模型
    def save_model(self,model_path):
        torch.save(self.q_eval.state_dict(), model_path)

    # 导入模型
    def load_model(self,model_path):
        state_dict = torch.load(model_path,map_location=torch.device('cpu'))
        self.q_eval.load_state_dict(state_dict)