'''
定义工具函数
'''
import numpy as np
import scipy.signal
import torch
from tqdm import tqdm
import random


#滑动平均滤波
def moving_average(a, window_size):
    cumulative_sum = np.cumsum(np.insert(a, 0, 0))
    middle = (cumulative_sum[window_size:] - cumulative_sum[:-window_size]) / window_size
    r = np.arange(1, window_size-1, 2)
    begin = np.cumsum(a[:window_size-1])[::2] / r
    end = (np.cumsum(a[:-window_size:-1])[::2] / r)[::-1]
    return np.concatenate((begin, middle, end))
#S-G滤波
def SG_Filter(a,window_size,n):
    a = scipy.signal.savgol_filter(a,window_size,n)
    return a


def compute_advantage(gamma, lmbda, td_delta):
    # if lmbda == 0:
    #     return td_delta
    td_delta = td_delta.detach().numpy()
    advantage_list = []
    advantage = 0.0
    for delta in td_delta[::-1]:
        advantage = gamma * lmbda * advantage + delta
        advantage_list.append(advantage)
    advantage_list.reverse()
    return torch.tensor(advantage_list, dtype=torch.float)


def train_on_policy_agent(env, agent, num_episodes):
    return_list = []
    loss_list = []
    for i in range(10):
        with tqdm(total=int(num_episodes/10), desc='Iteration %d' % i) as pbar:
            for i_episode in range(int(num_episodes/10)):
                np.random.seed(i_episode)
                random.seed(i_episode)
                torch.random.manual_seed(i_episode)
                episode_return = 0
                transition_dict = {'states': [], 'actions': [], 'next_states': [], 'rewards': [], 'dones': []}
                state,_= env.reset()
                done = False
                while not done:
                    action = agent.take_action(state.tolist())
                    next_state, reward, done, _,info = env.step(action)
                    transition_dict['states'].append(state)
                    transition_dict['actions'].append(action)
                    transition_dict['next_states'].append(next_state)
                    transition_dict['rewards'].append(reward)
                    transition_dict['dones'].append(done)
                    state = next_state
                    episode_return += reward
                loss = agent.update(transition_dict)
                return_list.append(episode_return)
                loss_list.append(loss.item())
                if (i_episode+1) % 5 == 0:
                    pbar.set_postfix({'episode': '%d' % (num_episodes/10 * i + i_episode+1),
                                      'return': '%.3f' % np.mean(return_list[-10:]),
                                      'loss':'%.3f' % np.mean(loss_list[-10:])})
                pbar.update(1)
    return return_list


'''
状态向量归一化
'''

class RunningMeanStd:
    # Dynamically calculate mean and std
    def __init__(self, shape):  # shape:the dimension of input data
        self.n = 0
        self.mean = np.zeros(shape)
        self.S = np.zeros(shape)
        self.std = np.sqrt(self.S)

    def update(self, x):
        x = np.array(x)
        self.n += 1
        if self.n == 1:
            self.mean = x
            self.std = x
        else:
            old_mean = self.mean.copy()
            self.mean = old_mean + (x - old_mean) / self.n
            self.S = self.S + (x - old_mean) * (x - self.mean)
            self.std = np.sqrt(self.S / self.n)

    def normalized(self, x):
        self.update(x)
        x = (x - self.mean) / (self.std + 1e-8)
        return x


'''
PPO-memory类
'''


# Memory to store experiences
class Memory:  # Class to store agent's experience
    def __init__(self):  # Initialize memory
        self.states = []  # List to store states
        self.actions = []  # List to store actions
        self.logprobs = []  # List to store log probabilities of actions
        self.rewards = []  # List to store rewards
        self.next_states = []
        self.dones = []  # List to store terminal state flags

    def clear(self):  # Clear memory after an update
        self.states = []  # Clear stored states
        self.actions = []  # Clear stored actions
        self.logprobs = []  # Clear stored log probabilities
        self.rewards = []  # Clear stored rewards
        self.next_states = []
        self.dones = []  # Clear terminal state flags