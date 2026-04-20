import unittest

from edge_sim_py.environment import CpnEnvironment
from edge_sim_py.environment import GridEnvironment
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.drl_model import DQN
import torch
import numpy as np
from edge_sim_py import config
import random
import pickle
from matplotlib import pyplot as plt
from edge_sim_py.drl_model import rl_utils


HIDDEN_SIZE = 128 # 隐藏层大小
MEMORY_CAPACITY_CUSTOM = 10000 # 经验池大小
BATCH_SIZE_CUSTOM = 64 #训练样本批大小
MEMORY_THRESHOLD = 256 # 经验池训练阈值
GAMMA_CUSTOM = 0.98  # 折扣因子
EPS_START_CUSTOM = 0.9  # 探索初始值
EPS_END_CUSTOM = 0.1  # 探索率最终值
EPS_DECAY_CUSTOM = 1000 # epsilon衰减系数
TAU_CUSTOM = 0.05  # 用于软更新的 Tau（备用，这里不使用）
LR_CUSTOM = 1e-4  # 学习率
TARGET_UPDATE_FREQ_CUSTOM = 50 # 目标网络更新频率
NUM_EPISODES_CUSTOM=500 # 训练迭代次数
MAX_STEPS_PER_EPISODE_CUSTOM = 30  # 每次迭代的最大步数


#其他参数
Jain_MIN=0.8
NUM_TASK=1

NUM_NODE=3
device=torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

params = MySimulator.get_ParamsFromFile(input_file=config.params_file)



class DqnTest(unittest.TestCase):

    def load_initialize(self)->object:
        params = MySimulator.get_ParamsFromFile(input_file=config.params_file)
        def Stop_func() -> bool:
            return len(Task.all()) == params["max_tasks"]

        # 构建仿真器
        my_simulator = MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )

        my_simulator.setUp(input_file=config.initialize_file)
        return my_simulator

    #Grid环境测试
    def testGridEnv(self):
        device = torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

        Grid_env=GridEnvironment()
        # 状态空间维度
        n_observations_custom = Grid_env.state_dim
        # 动作空间维度
        n_actions_custom = Grid_env.action_dim
        print(f"state_dim:{n_observations_custom}, action_dim:{n_actions_custom}")

        # 用于绘图的列表
        episode_rewards_custom = []
        episode_losses_custom = []
        # 初始化DQN
        dqn_model = DQN(n_actions=n_actions_custom,n_features=n_observations_custom,n_hidden=HIDDEN_SIZE,batch_size=BATCH_SIZE_CUSTOM,
                         reward_decay=GAMMA_CUSTOM,epsilon_start=EPS_START_CUSTOM,epsilon_end=EPS_END_CUSTOM,
                         epsilon_decay=EPS_DECAY_CUSTOM,learning_rate=LR_CUSTOM,memory_size=MEMORY_CAPACITY_CUSTOM,
                         update_T=TARGET_UPDATE_FREQ_CUSTOM,device=device)
        # 初始网络参数一致
        dqn_model.update_Target()

        print("Training process-------")
        # random.seed(1)
        # np.random.seed(1)
        # torch.manual_seed(1)
        # 训练循环迭代次数
        for i_episode in range(NUM_EPISODES_CUSTOM):
            # 以每次迭代次数作为每次迭代的随机数种子
            # np.random.seed(i_episode)
            # ==== seed
            random.seed(i_episode)
            np.random.seed(i_episode)
            torch.manual_seed(i_episode)
            # 重置环境并获取初始状态张量
            state = Grid_env.reset()
            total_reward = 0  # 记录当前次迭代的累计值
            current_losses = []  # 记录当前次迭代的总损失值

            # 循环步进
            for t in range(MAX_STEPS_PER_EPISODE_CUSTOM):
            # while True:
                # 使用 \(\epsilon\)-贪婪策略选择动作
                action = dqn_model.choose_action(state)

                # 在环境中执行动作
                next_state, reward, done= Grid_env.step(action)
                total_reward += reward

                # 将转移存储在回放缓存中(s,a,r,s')
                dqn_model.store_transition(state, action, reward, next_state,done)
                # 对策略网络执行一步优化
                if dqn_model.memory.counter > MEMORY_THRESHOLD:
                    loss = dqn_model.learn()
                    if loss is not None:
                        current_losses.append(loss)

                # 转移到下一个状态
                state = next_state

                # 如果本地迭代结束，则跳出循环
                if done:break

            # 存储一次迭代的统计信息
            episode_rewards_custom.append(total_reward)
            episode_losses_custom.append(np.mean(current_losses) if current_losses else 0)

            # 每 10 次迭代打印一次进度
            if (i_episode + 1) % 10 == 0:
                avg_reward = np.mean(episode_rewards_custom[-10:])
                avg_loss = np.mean([l for l in episode_losses_custom[-10:] if l > 0])
                print(
                    f"迭代 {i_episode+1}/{NUM_EPISODES_CUSTOM} | "
                    f"最近 10 次迭代的平均奖励：{avg_reward:.2e} | "
                    f"平均损失：{avg_loss:.2e} |"
                )
            if (i_episode+1) % 50 == 0:
                #保存数据
                print("Save results------")
                # 每次迭代的奖励
                with open("reward.pkl", "wb") as f:
                    pickle.dump(episode_rewards_custom, f)
                # 每次迭代的损失
                with open("losses.pkl", "wb") as f:
                    pickle.dump(episode_losses_custom, f)

                # 保存模型
                print("Save model-------")
                #保存模型
                dqn_model.save_model(model_path="Test/model_file/grid_model.pth")

    # Grid训练模型测试
    def testGridTest(self):
        device = torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

        Grid_env=GridEnvironment()
        # 导入模型

        # 状态空间维度
        n_observations_custom = Grid_env.state_dim
        # 动作空间维度
        n_actions_custom = Grid_env.action_dim
        print(f"state_dim:{n_observations_custom}, action_dim:{n_actions_custom}")

        # 用于绘图的列表
        # 初始化DQN
        dqn_model = DQN(n_actions=n_actions_custom,n_features=n_observations_custom,n_hidden=HIDDEN_SIZE,batch_size=BATCH_SIZE_CUSTOM,
                         reward_decay=GAMMA_CUSTOM,epsilon_start=EPS_START_CUSTOM,epsilon_end=EPS_END_CUSTOM,
                         epsilon_decay=EPS_DECAY_CUSTOM,learning_rate=LR_CUSTOM,memory_size=MEMORY_CAPACITY_CUSTOM,
                         update_T=TARGET_UPDATE_FREQ_CUSTOM,device=device)

        # 导入模型
        dqn_model.load_model("Test/model_file/grid_model.pth")

        # 重置环境并获取初始状态张量
        np.random.seed(10)
        state = Grid_env.reset()
        Grid_env.render()
        # 循环步进
        while True:
                # 使用 \(\epsilon\)-贪婪策略选择动作
                action = dqn_model.choose_action(state)

                # 在环境中执行动作
                next_state, reward, done = Grid_env.step(action)

                Grid_env.render()

                # 转移到下一个状态
                state = next_state

                # 如果本地迭代结束，则跳出循环
                if done: break

    #CPN训练模型测试
    def testCpnEnv(self):
        device = torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

        params = MySimulator.get_ParamsFromFile(input_file=config.params_file)
        def Stop_func() -> bool:
            return len(Task.all()) == params["max_tasks"]

        # 构建仿真器
        my_simulator = MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        my_simulator.setUp(input_file=config.initialize_file)
        print("Controller policy:"+my_simulator.policy)

        #初始化环境
        Cpn_env = CpnEnvironment(num_task=NUM_TASK,num_node=NUM_NODE,
                         Jain_min=Jain_MIN,simulator=my_simulator,
                         device=device)
        # 状态空间维度
        n_observations_custom = Cpn_env.state_dim
        # 动作空间维度
        n_actions_custom = Cpn_env.action_dim

        print(f"state_dim:{n_observations_custom}, action_dim:{n_actions_custom}")

        # 初始化DQN
        dqn_model = DQN(n_actions=n_actions_custom,n_features=n_observations_custom,n_hidden=HIDDEN_SIZE,batch_size=BATCH_SIZE_CUSTOM,
                         reward_decay=GAMMA_CUSTOM,epsilon_start=EPS_START_CUSTOM,epsilon_end=EPS_END_CUSTOM,
                         epsilon_decay=EPS_DECAY_CUSTOM,learning_rate=LR_CUSTOM,memory_size=MEMORY_CAPACITY_CUSTOM,
                         update_T=TARGET_UPDATE_FREQ_CUSTOM,device=device)

        # 初始网络参数一致
        dqn_model.update_Target()

        print("Training process-------")

        state = Cpn_env.reset()
        total_reward = 0  # 记录当前次迭代的累计值
        current_losses = []  # 记录当前次迭代的总损失值



        while True:
            action = dqn_model.choose_action(state)
            # 在环境中执行动作
            next_state, reward, done = Cpn_env.step(action)
            total_reward += reward

            # 将转移存储在回放缓存中
            # memory_next_state = next_state if not done else None
            dqn_model.store_transition(state,action,reward,next_state)
            # 对策略网络执行一步优化
            if dqn_model.memory_counter > MEMORY_THRESHOLD:
                loss = dqn_model.learn()
                if loss is not None:
                    current_losses.append(loss)
            Cpn_env.simulator.schedule.steps+=1
            Cpn_env.simulator.schedule.time+=1
            #判断退出
            if done:
                break
            # 继续转移到下一个状态
            state = next_state
        print("Training process finished!")
        print("---------Summary--------")
        MyScheduler.statistics()

        print("Save model-------")
        # torch.save(dqn_model, "dqn_model.pth")

    def testPlot(self):
        reward=None
        with open("Test/result/reward/dqn_reward_cpn4.pkl",'rb') as f:
            reward=pickle.load(f)
        # reward = rl_utils.moving_average(reward,window_size=5)
        filter_reward = rl_utils.SG_Filter(reward,31,3)
        plt.figure(1)
        plt.plot(range(1,len(reward)+1),reward,'c-',label="reward")
        plt.plot(range(1,len(filter_reward)+1),filter_reward,'g-',label="filter_reward")
        plt.xlabel("Episode")
        plt.ylabel("Episode Reward")
        plt.legend()

        # with open("Test/result/loss/dqn_loss_cpn2.pkl",'rb') as f:
        #    loss = pickle.load(f)
        # loss = rl_utils.moving_average(loss,window_size=11)
        # plt.figure(2)
        # plt.plot(range(1, len(loss) + 1), loss, label="loss")
        # plt.xlabel("Episode")
        # plt.ylabel("Episode Avg_loss")

        plt.show()


