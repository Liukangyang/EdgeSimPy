import unittest

from edge_sim_py import CpnEnvironment
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.drl_model import DQN
import torch
import numpy as np
from edge_sim_py import config

HIDDEN_SIZE = 64 # 隐藏层大小
BATCH_SIZE_CUSTOM = 10 #训练样本批大小
GAMMA_CUSTOM = 0.99  # 折扣因子（鼓励向前看）
EPS_START_CUSTOM = 1.0  # 从完全探索开始
EPS_END_CUSTOM = 0.1  # 探索率最终值
EPS_DECAY_CUSTOM = 500
TAU_CUSTOM = 0.05  # 用于软更新的 Tau（备用，这里不使用）
LR_CUSTOM = 5e-3  # 学习率（可能需要调整）
MEMORY_CAPACITY_CUSTOM = 10000
MEMORY_THRESHOLD = 20
TARGET_UPDATE_FREQ_CUSTOM = 20  # 目标网络更新频率
NUM_EPISODES_CUSTOM = 500  # 训练迭代次数
MAX_STEPS_PER_EPISODE_CUSTOM = 200  # 每次迭代的最大步数

# 其他参数
Jain_MIN = 0.75
NUM_TASK = 1
NUM_NODE = 3
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

    def testLoad(self):
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
            dqn_model.store_transiton(state,action,reward,next_state)
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

    #不同策略的对比
    def testRandomPolicy(self):
        print("random policy")
        simulator = self.load_initialize()
        simulator.run_model()



    def testStaticPolicy(self):
        print("static policy")
        simulator = self.load_initialize()
        simulator.run_model()


    def testDynamicPolicy(self):
        print("dynamic policy")

