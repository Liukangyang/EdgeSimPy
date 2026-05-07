#将根目录添加到系统路径中
 # 获取当前文件的绝对路径
import os
import sys
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
project_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_dir)

from edge_sim_py.environments import CpnEnvironment
from edge_sim_py.drl_model import PPO,DoublePPO
import numpy as np
import random
import torch
import os
import pickle
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
import yaml
from edge_sim_py.components import *
from edge_sim_py import MySimulator
from tqdm import tqdm
from edge_sim_py.drl_model.rl_utils import *


np.random.seed(0)

#导入文件
with open("../config.yaml", 'r',encoding='utf-8') as f:
   config = yaml.safe_load(f)

#创建仿真器
# TODO:停止标准，达到指定数量任务且所有认为均完成
def Stop_func() -> bool:
    return all(user.task_count > int(config['ppo']['MAX_STEPS_PER_EPISODE']) for user in MyUser.all())

params = MySimulator.get_ParamsFromFile(input_file='../file/params.json')

simulator = MySimulator(
    stopping_criterion=Stop_func,
    scheduler=MyScheduler,
    params=params
)
simulator.setUp(input_file='../file/test1.json')
print(f"policy:{simulator.policy}")



#构建环境
device=torch.device( "cuda:0" if torch.cuda.is_available() else "cpu")
Cpn_env = CpnEnvironment(num_task=config['user']['task_num'],num_node=config['server']['nums'],
                         simulator=simulator, device=device)
#状态空间维度
state_dim = Cpn_env.state_dim
#动作空间维度
action_dim = Cpn_env.action_dim

agent_params=config['ppo']
#构建智能体
# agent = DoublePPO(state_dim=state_dim, hidden_dim=int(agent_params['HIDDEN_SIZE']), action_dim=action_dim,
#               actor1_lr=float(agent_params['ACTOR1_LR']),actor2_lr=float(agent_params['ACTOR2_LR']), critic_lr=float(agent_params['CRITIC_LR']),
#               lmbda=float(agent_params['LAMBDA']), epochs=int(agent_params['EPOCHS']), eps=float(agent_params['EPS']),
#               gamma=float(agent_params['GAMMA']),batch_size=int(agent_params['BATCH_SIZE']), device=device)
agent = PPO(state_dim=state_dim, hidden_dim=int(agent_params['HIDDEN_SIZE']), action_dim=action_dim,
              actor_lr=float(agent_params['ACTOR_LR']), critic_lr=float(agent_params['CRITIC_LR']),
              lmbda=float(agent_params['LAMBDA']), epochs=int(agent_params['EPOCHS']), eps=float(agent_params['EPS']),
              gamma=float(agent_params['GAMMA']),batch_size=int(agent_params['BATCH_SIZE']), device=device)
# 统计量
episode_rewards_custom = []
episode_losses_custom = []

if __name__ == '__main__':
    #训练迭代
    #TODO:使用tqdm,循环50次，将总迭代次数除以50，每次循环迭代10次
    num_episodes = int(agent_params['NUM_EPISODES'])
    for i in range(50):
        with tqdm(total=int(num_episodes / 50), desc='Iteration %d' % i) as pbar:
            for i_episode in range(int(num_episodes/50)):
                #设置随机数种子
                np.random.seed(int(num_episodes / 50 * i + i_episode + 1))
                random.seed(int(num_episodes / 50 * i + i_episode + 1))
                torch.random.manual_seed(int(num_episodes / 50 * i + i_episode + 1))

                #在线策略
                transition_dict = {'states': [], 'actions': [],'action2':[],'next_states': [], 'rewards': [], 'dones': []}

                #重置环境
                state  = Cpn_env.reset()
                done = False
                total_reward = 0
                while not done:
                    # print(f"step:{MyUser.all()[0].task_count}")
                    combined_action = agent.take_action(state)
                    next_state, reward, done = Cpn_env.step(combined_action)
                    total_reward += reward
                    #存储样本
                    transition_dict['states'].append(state)
                    transition_dict['actions'].append(combined_action)
                    # transition_dict['action2'].append(combined_action[1])
                    transition_dict['next_states'].append(next_state)
                    transition_dict['rewards'].append(reward)
                    transition_dict['dones'].append(done)

                    Cpn_env.simulator.schedule.steps += 1
                    Cpn_env.simulator.schedule.time += 1

                    if done:
                        break
                    state = next_state

                avg_actor_loss = agent.update(transition_dict)
                #存储每次迭代的结果
                episode_rewards_custom.append(total_reward)
                episode_losses_custom.append(avg_actor_loss.item())
                pbar.update(1)
                # 每 10 次迭代打印一次进度
                # TODO：改用tdqm显示,每5次迭代更新一次最近5次累计奖励的平均值
                if (i_episode + 1) % 5 == 0:
                    pbar.set_postfix({'episode': '%d' % (num_episodes / 50 * i + i_episode + 1),
                                      'return': '%.3f' % np.mean(episode_rewards_custom[-5:]),
                                      'loss': '%.3f' % np.mean(episode_losses_custom[-5:])})



