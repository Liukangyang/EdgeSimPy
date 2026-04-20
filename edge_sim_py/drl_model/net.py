import torch.nn.functional as F
import torch

'''
DQN/DDQN基础网络
n_features:状态向量特征维数
n_hidden:隐藏层神经元数量
n_actions:输出向量维数
'''

from torch import nn
class Net(nn.Module):
    def __init__(self, state_dim, hidden_dim, action_dim):
        super(Net, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, 64)
        self.out = torch.nn.Linear(64, action_dim)

    def forward(self, x):
        #print(' ---- x.shape: ', x.shape)
        x = F.relu(self.fc1(x))  # 隐藏层使用ReLU激活函数
        x = F.relu(self.fc2(x))
        return self.out(x)


'''
AC基础网络
'''
#策略网络
class PolicyNet(nn.Module):
    def __init__(self, n_features, n_hiddens, n_actions, action_bound):
        super(PolicyNet, self).__init__()

        self.fc1 = nn.Linear(n_features, n_hiddens)
        # self.fc2 = nn.Linear(n_hiddens, 32)
        self.out = nn.Linear(n_hiddens, n_actions)
        self.action_bound = action_bound

    def forward(self, input):
        x = F.relu(self.fc1(input))
        # x = F.relu(self.fc2(x))
        output = self.out(x)
        return output



#critic网络
class CriticNet(nn.Module):
    def __init__(self, n_features, n_hiddens, action_dim):
        super(CriticNet, self).__init__()
        self.fc1 = nn.Linear(n_features, n_hiddens)
        # self.fc2 = nn.Linear(n_hiddens, 32)
        self.out = nn.Linear(n_hiddens, 1)

    def forward(self, state, action):
            input = torch.cat([state, action], dim=1)
            x = F.relu(self.fc1(input))
            # x = F.relu(self.fc2(x))
            return self.out(x)