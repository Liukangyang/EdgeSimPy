'''
神经网络定义
'''
# 定义网络架构
'''
n_features:状态向量特征维数
n_hidden:隐藏层神经元数量
n_actions:输出向量维数
'''
from torch import nn
class Net(nn.Module):
    # 定义网络
    def __init__(self, n_features, n_hidden, n_actions):
        super(Net, self).__init__()
        self.l1 = nn.Linear(n_features, n_hidden)
        self.l2 = nn.Linear(n_hidden, 16)
        self.l3 = nn.Linear(16, n_actions)
        self.Q_net = nn.Sequential(
            self.l1,
            nn.ReLU(), #隐藏层激活函数
            self.l2,
            nn.ReLU(),
            self.l3
            #
        )

    def forward(self, input):
        output = self.Q_net(input)
        return output
