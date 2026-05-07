import numpy as np
from matplotlib import pyplot as plt
import pickle
import unittest
from edge_sim_py.drl_model import rl_utils

class TestPlot(unittest.TestCase):
    def test_plot_reward_losss(self):
        reward_file ='Test/result/ppo-single/reward/ppo_single_reward_300_delay+E_nodecay.pkl'
        loss_file = 'Test/result/ppo-single/loss/ppo_single_loss_300_delay+E_nodecay.pkl'
        reward = pickle.load(open(reward_file,'rb'))
        loss = pickle.load(open(loss_file,'rb'))

        # filter_reward = rl_utils.moving_average(reward,31)
        plt.figure(1)
        plt.plot(range(1,501),reward[:500],'c-',label = 'reward')
        # plt.plot(range(1,501),filter_reward[:500],'b-',label = 'filter_reward')
        plt.xlabel('Episode')
        plt.ylabel('Episode Avg Reward')
        # plt.legend()

        filter_loss = rl_utils.moving_average(loss,31)
        plt.figure(2)
        plt.plot(range(1,501),filter_loss[:500],'c-')
        plt.xlabel('Episode')
        plt.ylabel('Episode Avg loss')

        plt.show()