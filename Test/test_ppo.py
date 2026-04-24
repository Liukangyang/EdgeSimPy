import unittest
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
import numpy as np
import random
import gymnasium as gym
import torch
from edge_sim_py.drl_model import PPO
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
        capacity=1000
        batch_size = 64
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        env_name = 'CartPole-v1'
        env = gym.make(env_name)
        # env.seed(0)
        torch.manual_seed(0)
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n
        print(f"state_dim:{state_dim}, action_dim:{action_dim}")
        agent = PPO(state_dim, hidden_dim, action_dim, actor_lr, critic_lr, lmbda,
            epochs, eps, gamma, device)

        #训练
        return_list = train_on_policy_agent(env, agent, num_episodes)


