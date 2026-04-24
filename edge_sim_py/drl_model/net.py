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


# '''
# AC基础网络
# '''
# #策略网络
# class PolicyNet(nn.Module):
#     def __init__(self, n_features, n_hiddens, n_actions, action_bound):
#         super(PolicyNet, self).__init__()
#
#         self.fc1 = nn.Linear(n_features, n_hiddens)
#         # self.fc2 = nn.Linear(n_hiddens, 32)
#         self.out = nn.Linear(n_hiddens, n_actions)
#         self.action_bound = action_bound
#
#     def forward(self, input):
#         x = F.relu(self.fc1(input))
#         # x = F.relu(self.fc2(x))
#         output = self.out(x)
#         return output
#
#
#
# #critic网络
# class CriticNet(nn.Module):
#     def __init__(self, n_features, n_hiddens, action_dim):
#         super(CriticNet, self).__init__()
#         self.fc1 = nn.Linear(n_features, n_hiddens)
#         # self.fc2 = nn.Linear(n_hiddens, 32)
#         self.out = nn.Linear(n_hiddens, 1)
#
#     def forward(self, state, action):
#             input = torch.cat([state, action], dim=1)
#             x = F.relu(self.fc1(input))
#             # x = F.relu(self.fc2(x))
#             return self.out(x)


'''
PPO基础网络定义
'''


class ActorNetwork(nn.Module):
    """独立的Actor网络，负责策略输出"""

    def __init__(self, state_dim: int, hidden_dim: int ,action_dim: int,):
        super(ActorNetwork, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, action_dim)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """输出动作logits"""
        x = F.relu(self.fc1(state))
        return F.softmax(self.fc2(x))

    def get_action(self, state: torch.Tensor):
        """获取动作和对应的log概率"""
        action_logits = self.forward(state)
        action_probs = F.softmax(action_logits, dim=-1)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()  #采用得动作
        log_prob = dist.log_prob(action) #获取采样动作的log概率值
        return action, log_prob

    def evaluate(self, state: torch.Tensor, action: torch.Tensor):
        """评估状态-动作对的log概率"""
        action_logits = self.forward(state)
        action_probs = F.softmax(action_logits, dim=-1)
        dist = torch.distributions.Categorical(action_probs)
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return log_prob, entropy

class CriticNetwork(nn.Module):
    """独立的Critic网络，负责价值函数估计"""

    def __init__(self, state_dim: int, hidden_dim: int = 64):
        super(CriticNetwork, self).__init__()

        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, 1)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """输出状态价值"""
        x = F.relu(self.fc1(state))
        return self.fc2(x)

    def evaluate(self, state: torch.Tensor) -> torch.Tensor:
        """评估状态价值"""
        return self.forward(state).squeeze(-1)




class PolicyNet(torch.nn.Module):
    def __init__(self, state_dim, hidden_dim, action_dim):
        super(PolicyNet, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return F.softmax(self.fc2(x), dim=1)


class ValueNet(torch.nn.Module):
    def __init__(self, state_dim, hidden_dim):
        super(ValueNet, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return self.fc2(x)