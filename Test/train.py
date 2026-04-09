from platform import system

from edge_sim_py import CpnEnvironment, Task, MySimulator
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.drl_model import DQN
import numpy as np
import torch
import os
from edge_sim_py import config
import pickle


np.random.seed(1)

# 定义网络
HIDDEN_SIZE = 32 # 隐藏层大小
MEMORY_CAPACITY_CUSTOM = 2000 # 经验池大小
MEMORY_THRESHOLD = 128 # 经验池训练阈值
BATCH_SIZE_CUSTOM = 64 #训练样本批大小
GAMMA_CUSTOM = 0.99  # 折扣因子
EPS_START_CUSTOM = 0.9  # 探索初始值
EPS_END_CUSTOM = 0.05  # 探索率最终值
EPS_DECAY_CUSTOM = 1000 # epsilon衰减系数
TAU_CUSTOM = 0.05  # 用于软更新的 Tau（备用，这里不使用）
LR_CUSTOM = 1e-3  # 学习率
TARGET_UPDATE_FREQ_CUSTOM = 40  # 目标网络更新频率
NUM_EPISODES_CUSTOM = 500  # 训练迭代次数
MAX_STEPS_PER_EPISODE_CUSTOM = 50  # 每次迭代的最大步数


#其他参数
Jain_MIN=0.9
NUM_TASK=1
NUM_NODE=3
device=torch.device("xpu") if torch.xpu.is_available() else torch.device("cpu")

params = MySimulator.get_ParamsFromFile(input_file=config.params_file)


#TODO：停止函数-当产生指定数量任务且均完成部署决策
def Stop_func() -> bool:
    return len(Task.all()) == params["max_tasks"]

#构建仿真器
my_simulator = MySimulator(
    stopping_criterion=Stop_func,
    scheduler=MyScheduler,
    params=params
)

my_simulator.setUp(input_file=config.initialize_file)
print("Controller policy:" + my_simulator.policy)

# 初始化
Cpn_env = CpnEnvironment(num_task=NUM_TASK,num_node=NUM_NODE,Jain_min=Jain_MIN,
                         state_min=config.state_min,state_max=config.state_max,
                         simulator=my_simulator, device=device)

#状态空间维度
n_observations_custom=Cpn_env.state_dim
#动作空间维度
n_actions_custom=Cpn_env.action_dim

# 初始化策略网络（主Q网络）和目标网络

dqn_model= DQN(n_actions=n_actions_custom,n_features=n_observations_custom,n_hidden=HIDDEN_SIZE,batch_size=BATCH_SIZE_CUSTOM,
                         reward_decay=GAMMA_CUSTOM,epsilon_start=EPS_START_CUSTOM,epsilon_end=EPS_END_CUSTOM,
                         epsilon_decay=EPS_DECAY_CUSTOM,learning_rate=LR_CUSTOM,memory_size=MEMORY_CAPACITY_CUSTOM,
                         update_T=TARGET_UPDATE_FREQ_CUSTOM,device=device)  # 主Q网络

# 将策略网络的权重复制到目标网络
dqn_model.update_Target()

# 用于绘图的列表
episode_rewards_custom = []
episode_lengths_custom = []
episode_epsilons_custom = []
episode_losses_custom = []

'''
开始训练过程
'''

if __name__ == '__main__':
    print("Training process-------")

    # 训练循环迭代次数
    for i_episode in range(NUM_EPISODES_CUSTOM):
        # 以每次迭代次数作为每次迭代的随机数种子
        np.random.seed(i_episode)
        # 重置环境并获取初始状态张量
        state = Cpn_env.reset()
        total_reward = 0 #记录当前次迭代的累计值
        current_losses = [] #记录当前次迭代的总损失值

        #循环步进
        for t in range(MAX_STEPS_PER_EPISODE_CUSTOM):
            # 使用 \(\epsilon\)-贪婪策略选择动作
            action = dqn_model.choose_action(state)

            # 在环境中执行动作
            next_state, reward, done = Cpn_env.step(action)
            total_reward += reward

            # 将转移存储在回放缓存中(s,a,r,s')
            dqn_model.store_transiton(state, action, reward, next_state)
            # 对策略网络执行一步优化
            if dqn_model.memory_counter > MEMORY_THRESHOLD:
                loss = dqn_model.learn()
                if loss is not None:
                    current_losses.append(loss)

            Cpn_env.simulator.schedule.steps += 1
            Cpn_env.simulator.schedule.time += 1
            # 如果本地迭代结束，则跳出循环
            if done:
                break
            # 转移到下一个状态
            state = next_state

        # 存储一次迭代的统计信息
        episode_rewards_custom.append(total_reward)
        # episode_lengths_custom.append(t + 1)
        # episode_epsilons_custom.append(current_epsilon) #贪婪策略参数的变化
        episode_losses_custom.append(np.mean(current_losses) if current_losses else 0)

        # 每 50 次迭代打印一次进度
        if (i_episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards_custom[-10:])
            # avg_length = np.mean(episode_lengths_custom[-50:])
            avg_loss = np.mean([l for l in episode_losses_custom[-10:] if l > 0])
            print(
                f"迭代 {i_episode+1}/{NUM_EPISODES_CUSTOM} | "
                f"最近 10 次迭代的平均奖励：{avg_reward:.2e} | "
                f"平均损失：{avg_loss:.2e} |"
            )
        # 每100步保存一次模型
        if (i_episode + 1) % 100 == 0:
            print("Save model-------")
            torch.save(dqn_model, "model_file/dqn_model.pth")

    print("Training process finished!")

    #暂停
    os.system("pause")

    #保存数据
    print("Save results------")
    # 每次迭代的奖励
    with open("reward.pkl","wb") as f:
        pickle.dump(episode_rewards_custom,f)
    # 每次迭代的损失
    with open("losses.pkl","wb") as f:
        pickle.dump(episode_losses_custom,f)

    #保存模型
    print("Save model-------")
    torch.save(dqn_model,"model_file/dqn_model.pth")







