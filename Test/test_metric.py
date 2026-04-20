import unittest
from cProfile import label
from email import policy

from edge_sim_py import CpnEnvironment
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.drl_model import DQN
from edge_sim_py.drl_model import DDQN
from edge_sim_py import config
import torch
import numpy as np
import random
from matplotlib import pyplot as plt
import pickle


HIDDEN_SIZE = 128 # 隐藏层大小
MEMORY_CAPACITY_CUSTOM = 10000 # 经验池大小
BATCH_SIZE_CUSTOM = 64 #训练样本批大小
MEMORY_THRESHOLD = 256 # 经验池训练阈值
GAMMA_CUSTOM = 0.98  # 折扣因子
EPS_START_CUSTOM = 0  # 探索初始值
EPS_END_CUSTOM = 0   # 探索率最终值
EPS_DECAY_CUSTOM = 1000 # epsilon衰减系数
TAU_CUSTOM = 0.05  # 用于软更新的 Tau（备用，这里不使用）
LR_CUSTOM = 1e-2  # 学习率
TARGET_UPDATE_FREQ_CUSTOM = 50 # 目标网络更新频率
NUM_EPISODES_CUSTOM = 500  # 训练迭代次数
TEST_EPISODES_CUSTOM = 100  # 测试迭代次数
MAX_STEPS_PER_EPISODE_CUSTOM = 30  # 每次迭代的最大步数


#其他参数
Jain_MIN=0.8
NUM_TASK=1
NUM_NODE=3

'''
测试多轮迭代
每轮迭代步进一定步数，每步生成随机任务
最后统计每轮迭代中的优化目标平均值，以及再对迭代次数取平均值
'''
class MetricTestCase(unittest.TestCase):
    # 强化学习决策测试
    def testDynamicPolicy(self):
        device = torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

        # 记录每次迭代的指标
        episode_rewards_custom = []  # 单次迭代的奖励和
        episode_delay_custom = []  # 单次迭代的总时延
        episode_cost_custom = []  # 单次迭代的总成本
        episode_jain_custom = []  # 单次迭代的负载均衡总和
        episode_success_custom = [] # 单次迭代的满足时延要求的任务比例
        print("Dynamic policy test")
        policy = "dynamic"
        print(f"policy:{policy}")
        params = MySimulator.get_ParamsFromFile(input_file='Test/params.json')

        def Stop_func() -> bool:
            return len(Task.all()) == params["max_tasks"] and len(Controller.all()[0].schedule_services) == 0

        my_simulator = MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        my_simulator.policy = policy
        my_simulator.setUp(input_file='Test/test1.json')


        Cpn_env = CpnEnvironment(num_task=NUM_TASK, num_node=NUM_NODE, Jain_min=Jain_MIN,
                                 state_min=config.state_min, state_max=config.state_max,
                                 simulator=my_simulator, device=device)

        # 状态空间维度
        n_observations_custom = Cpn_env.state_dim
        # 动作空间维度
        n_actions_custom = Cpn_env.action_dim

        # 初始化策略网络（主Q网络）和目标网络
        network_mode = 'dqn'
        if network_mode == 'dqn':
            model = DQN(n_actions=n_actions_custom, n_features=n_observations_custom, n_hidden=HIDDEN_SIZE,
                            batch_size=BATCH_SIZE_CUSTOM,
                            reward_decay=GAMMA_CUSTOM, epsilon_start=EPS_START_CUSTOM, epsilon_end=EPS_END_CUSTOM,
                            epsilon_decay=EPS_DECAY_CUSTOM, learning_rate=LR_CUSTOM, memory_size=MEMORY_CAPACITY_CUSTOM,
                            update_T=TARGET_UPDATE_FREQ_CUSTOM, device=device)
        elif network_mode == 'ddqn':
            model = DDQN(n_actions=n_actions_custom, n_features=n_observations_custom, n_hidden=HIDDEN_SIZE,
                            batch_size=BATCH_SIZE_CUSTOM,
                            reward_decay=GAMMA_CUSTOM, epsilon_start=EPS_START_CUSTOM, epsilon_end=EPS_END_CUSTOM,
                            epsilon_decay=EPS_DECAY_CUSTOM, learning_rate=LR_CUSTOM, memory_size=MEMORY_CAPACITY_CUSTOM,
                            update_T=TARGET_UPDATE_FREQ_CUSTOM, device=device)
        else:
            print("Unknown network mode!")
            return
        print(f"network mode:{network_mode}")
        # 导入训练好的参数
        model.load_model("Test/model_file/dqn/cpn_dqn_params_100_4.pth")
        print("load model params!")

        print("test start")
        for i_episode in range(TEST_EPISODES_CUSTOM):
            random.seed(i_episode)
            np.random.seed(i_episode)
            torch.manual_seed(i_episode)
            state = Cpn_env.reset()


            total_reward = 0
            total_delay = 0
            total_cost = 0
            total_jain = 0
            total_success = 0
            total_provision = 0

            # 单次迭代步进
            for t in range(MAX_STEPS_PER_EPISODE_CUSTOM):
                    action = model.choose_action(state)

                    # 在环境中执行动作
                    next_state, reward, done = Cpn_env.step(action)
                    # 记录指标
                    # 奖励值
                    total_reward += reward
                    # Jain指数
                    total_jain += Cpn_env.simulator.get_D()
                    Cpn_env.simulator.schedule.steps += 1
                    Cpn_env.simulator.schedule.time += 1
                    # 如果本地迭代结束，则跳出循环
                    if done: break
                    # 转移到下一个状态
                    state = next_state

            for service in Task.all():
                total_delay += service.trans_sustain_steps + service.comp_sustain_steps
                total_cost += service.resource_cost
                if service.being_provisioned and  service.trans_sustain_steps+service.comp_sustain_steps <= service.max_delay:
                    total_success += 1
                if service.being_provisioned:
                    total_provision += 1

            episode_rewards_custom.append(total_reward / Cpn_env.simulator.schedule.steps)
            episode_delay_custom.append(total_delay / total_provision)
            episode_cost_custom.append(total_cost / total_provision)
            episode_jain_custom.append(total_jain / Cpn_env.simulator.schedule.steps)
            episode_success_custom.append(total_success / len(Task.all()))

            # 每 10 次迭代打印一次进度
            if (i_episode + 1) % 10 == 0:
                avg_delay = np.mean(episode_delay_custom[-10:])
                print(
                    f"迭代 {i_episode + 1}/{TEST_EPISODES_CUSTOM} | "
                    f"最近 10 次迭代的平均时延：{avg_delay:.2e} | "
                )
        print("test finished")

        print(f"avg_delay:{np.mean(episode_delay_custom)}")
        print(f"avg_cost:{np.mean(episode_cost_custom)}")
        print(f"avg_jain:{np.mean(episode_jain_custom)}")
        print(f"avg_success:{np.mean(episode_success_custom)}")

        # 保存数据
        print("save result")
        with open("Test/result/dqn/reward.pkl", 'wb') as f:
            pickle.dump(episode_rewards_custom, f)
        with open("Test/result/dqn/delay.pkl", 'wb') as f:
            pickle.dump(episode_delay_custom, f)
        with open("Test/result/dqn/cost.pkl", 'wb') as f:
            pickle.dump(episode_cost_custom, f)
        with open("Test/result/dqn/jain.pkl", 'wb') as f:
            pickle.dump(episode_jain_custom, f)
        with open("Test/result/dqn/success.pkl", 'wb') as f:
            pickle.dump(episode_success_custom, f)
        # # 作图
        # plt.figure(1)
        # plt.plot(range(1, len(episode_rewards_custom) + 1), episode_rewards_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Reward")
        #
        # plt.figure(2)
        # plt.plot(range(1, len(episode_delay_custom) + 1), episode_delay_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Delay")
        #
        # plt.figure(3)
        # plt.plot(range(1, len(episode_cost_custom) + 1), episode_cost_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Cost")
        #
        # plt.figure(4)
        # plt.plot(range(1, len(episode_jain_custom) + 1), episode_jain_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Jain")
        #
        # plt.figure(5)
        # plt.plot(range(1,len(episode_success_custom)+1),episode_success_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Success Ratio")
        #
        # plt.show()

    # 随机或静态决策测试
    def testOtherpolicy(self):
        # 记录每次迭代的指标
        episode_delay_custom = []  # 单次迭代的总时延
        episode_cost_custom = []  # 单次迭代的总成本
        episode_jain_custom = []  # 单次迭代的负载均衡总和
        episode_success_custom = [] # 单次迭代的满足时延要求的任务比例
        policy = "random"
        params = MySimulator.get_ParamsFromFile(input_file='Test/params.json')

        def Stop_func() -> bool:
            return len(Task.all()) == params["max_tasks"] and len(Controller.all()[0].schedule_services) == 0

        print(f"policy:{policy}")
        my_simulator = MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        my_simulator.policy = policy
        my_simulator.setUp(input_file='Test/test1.json')

        for i_episode in range(TEST_EPISODES_CUSTOM):
            random.seed(i_episode)
            np.random.seed(i_episode)

            total_delay = 0
            total_cost = 0
            total_jain = 0
            total_success = 0
            total_provision = 0
            my_simulator.reset()
            my_simulator.initialize_Users()

            while my_simulator.running:
                my_simulator.step()
                total_jain += my_simulator.get_D()
                my_simulator.running = False if my_simulator.stopping_criterion() else True

            for service in Task.all():
                total_delay += service.trans_sustain_steps + service.comp_sustain_steps
                total_cost += service.resource_cost
                if service.being_provisioned and service.trans_sustain_steps + service.comp_sustain_steps <= service.max_delay:
                    total_success += 1
                if service.being_provisioned:
                    total_provision += 1
            episode_delay_custom.append(total_delay /total_provision)
            episode_cost_custom.append(total_cost / total_provision)
            episode_jain_custom.append(total_jain /  my_simulator.schedule.steps)
            episode_success_custom.append(total_success/len(Task.all()))

            # 每 10 次迭代打印一次进度
            if (i_episode + 1) % 10 == 0:
                avg_delay = np.mean(episode_delay_custom[-10:])
                print(
                    f"迭代 {i_episode + 1}/{TEST_EPISODES_CUSTOM} | "
                    f"最近 10 次迭代的平均时延：{avg_delay:.2e} | "
                )
        print(f"avg_delay:{np.mean(episode_delay_custom)}")
        print(f"avg_cost:{np.mean(episode_cost_custom)}")
        print(f"avg_jain:{np.mean(episode_jain_custom)}")
        print(f"avg_success:{np.mean(episode_success_custom)}")

        # 保存数据
        print("save result")
        with open("Test/result/"+policy+"/delay.pkl", 'wb') as f:
            pickle.dump(episode_delay_custom, f)
        with open("Test/result/"+policy+"/cost.pkl", 'wb') as f:
            pickle.dump(episode_cost_custom, f)
        with open("Test/result/"+policy+"/jain.pkl", 'wb') as f:
            pickle.dump(episode_jain_custom, f)
        with open("Test/result/"+policy+"/success.pkl", 'wb') as f:
            pickle.dump(episode_success_custom, f)

        # #作图
        # plt.figure(1)
        # plt.plot(range(1, len(episode_delay_custom) + 1), episode_delay_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Delay")
        #
        # plt.figure(2)
        # plt.plot(range(1, len(episode_cost_custom) + 1), episode_cost_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Cost")
        #
        # plt.figure(3)
        # plt.plot(range(1, len(episode_jain_custom) + 1), episode_jain_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Jain")
        #
        #
        # plt.figure(4)
        # plt.plot(range(1, len(episode_success_custom) + 1), episode_success_custom)
        # plt.xlabel("episode")
        # plt.ylabel("Episode Success Ratio")
        # plt.show()

    def testPlot(self):
    # 作图比较各算法在各类指标上的差距
        #delay
          with open("Test/result/dqn/delay.pkl", 'rb') as f:
             model_delay = pickle.load(f)
          with open("Test/result/random/delay.pkl", 'rb') as f:
            random_delay = pickle.load(f)
          with open("Test/result/static/delay.pkl", 'rb') as f:
            static_delay = pickle.load(f)
          plt.figure(1)
          plt.plot(range(1,len(model_delay) + 1), model_delay,'r-',label="DQN")
          plt.plot(range(1,len(random_delay) + 1), random_delay,'b-',label="Random")
          plt.plot(range(1,len(static_delay) + 1), static_delay,'g-',label="Static")
          plt.xlabel("episode")
          plt.ylabel("Episode Delay")
          plt.legend()
          plt.ylim([20,50])
          print(f"Avg delay-dqn:{np.mean(model_delay)},random:{np.mean(random_delay)},static:{np.mean(static_delay)}")

    #cost
          with open("Test/result/dqn/cost.pkl", 'rb') as f:
            model_cost = pickle.load(f)
          with open("Test/result/random/cost.pkl", 'rb') as f:
            random_cost = pickle.load(f)
          with open("Test/result/static/cost.pkl", 'rb') as f:
            static_cost = pickle.load(f)
          plt.figure(2)
          plt.plot(range(1, len(model_cost) + 1), model_cost, 'r-', label="DQN")
          plt.plot(range(1, len(random_cost) + 1), random_cost, 'b-', label="Random")
          plt.plot(range(1, len(static_cost) + 1), static_cost, 'g-', label="Static")
          plt.xlabel("episode")
          plt.ylabel("Episode Cost")
          plt.legend()
          plt.ylim([0, 30])
          print(f"Avg cost-dqn:{np.mean(model_cost)},random:{np.mean(random_cost)},static:{np.mean(static_cost)}")

        #jain
          with open("Test/result/dqn/jain.pkl", 'rb') as f:
            model_jain = pickle.load(f)
          with open("Test/result/random/jain.pkl", 'rb') as f:
            random_jain = pickle.load(f)
          with open("Test/result/static/jain.pkl", 'rb') as f:
            static_jain = pickle.load(f)
          plt.figure(3)
          plt.plot(range(1, len(model_jain) + 1), model_jain, 'r-', label="DQN")
          plt.plot(range(1, len(random_jain) + 1), random_jain, 'b-', label="Random")
          plt.plot(range(1, len(static_jain) + 1), static_jain, 'g-', label="Static")
          plt.xlabel("episode")
          plt.ylabel("Episode Jain")
          plt.legend()
          plt.ylim([0, 30])
          print(f"Avg Jain:dqn:{np.mean(model_jain)},random:{np.mean(random_jain)},static:{np.mean(static_jain)}")
          # print(static_jain)
          # success_ratio
          with open("Test/result/dqn/success.pkl", 'rb') as f:
            model_success = pickle.load(f)
          with open("Test/result/random/success.pkl", 'rb') as f:
            random_success = pickle.load(f)
          with open("Test/result/static/success.pkl", 'rb') as f:
            static_success = pickle.load(f)
          # plt.figure(4)
          # plt.plot(range(1, len(model_success) + 1), model_success, 'r-', label="DQN")
          # plt.plot(range(1, len(random_success) + 1), random_success, 'b-', label="Random")
          # plt.plot(range(1, len(static_success) + 1), static_success, 'g-', label="Static")
          # plt.xlabel("episode")
          # plt.ylabel("Episode Success Ration")
          # plt.legend()
          # plt.ylim([0, 1])
          print(f"Avg Success Ration:dqn:{np.mean(model_success)},random:{np.mean(random_success)},static:{np.mean(static_success)}")

          plt.show()

if __name__ == '__main__':
    unittest.main()










