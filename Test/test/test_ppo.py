#将根目录添加到系统路径中
 # 获取当前文件的绝对路径
import os
import sys
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
project_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_dir)

import unittest
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
import numpy as np
import random
import gymnasium as gym
import torch
from edge_sim_py.drl_model import PPO,PPO2
from edge_sim_py.drl_model.rl_utils import *

torch.autograd.set_detect_anomaly(True)  # 启用异常检测
class TestPPOSimulator(unittest.TestCase):
    def testCartPole(self):
        actor_lr = 1e-3
        critic_lr = 1e-2
        num_episodes = 500
        hidden_dim = 128
        gamma = 0.98
        lmbda = 0
        epochs = 10
        eps = 0.2
        batch_size = 32
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        env_name = 'CartPole-v1'
        env = gym.make(env_name)

        torch.manual_seed(0)
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n
        print(f"state_dim:{state_dim}, action_dim:{action_dim}")
        agent = PPO(state_dim, hidden_dim, action_dim, actor_lr, critic_lr, lmbda,
            epochs, eps, gamma, batch_size,device)

        #训练
        return_list = train_on_policy_agent(env, agent, num_episodes)

    def testCartPole2(self):
        actor_lr = 1e-5
        critic_lr = 2e-5
        num_episodes = 500
        hidden_dim = 64
        gamma = 0.98
        lmbda = 0
        epochs = 10
        eps = 0.2
        batch_size = 64
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        env_name = 'CartPole-v1'
        env = gym.make(env_name)
        # env.seed(0)
        torch.manual_seed(0)
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n
        print(f"state_dim:{state_dim}, action_dim:{action_dim}")
        agent = PPO2(state_dim, hidden_dim, action_dim, actor_lr, critic_lr, lmbda,
            epochs, eps, gamma, batch_size,device)

        #经验池
        memory = Memory()

        return_list = []
        loss_list = []
        #训练
        for i_episode in range(num_episodes):
            np.random.seed(i_episode)
            random.seed(i_episode)
            torch.random.manual_seed(i_episode)
            episode_return = 0
            state, _ = env.reset()
            done = False

            while not done:
                action = agent.take_action(state,memory)
                next_state, reward, done, _, info = env.step(action)
                memory.next_states.append(torch.tensor(next_state, dtype=torch.float))
                memory.rewards.append(torch.tensor(reward,dtype=torch.float))
                memory.dones.append(torch.tensor(done))
                state = next_state
                episode_return += reward

            loss = agent.update(memory)
            return_list.append(episode_return)
            loss_list.append(loss.item())
            memory.clear()
            if (i_episode + 1) % 5 == 0:
                print({'episode': '%d' % (i_episode + 1),
                                  'return': '%.3f' % np.mean(return_list[-10:]),
                                  'loss': '%.3f' % np.mean(loss_list[-10:])})
