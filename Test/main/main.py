#将根目录添加到系统路径中
 # 获取当前文件的绝对路径
import os
import sys

from sympy.strategies.core import switch

current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
project_dir = os.path.abspath(os.path.join(current_dir, ".."))
root_dir = os.path.abspath(os.path.join(project_dir, ".."))
sys.path.append(root_dir)

from edge_sim_py.environments import CpnEnvironment
from edge_sim_py.drl_model import PPO, DoublePPO, DQN
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
from edge_sim_py.argumentParse import parse_args


np.random.seed(0)
#先导入参数并解析
args = parse_args()
config_file = args.configfile
topo_file = args.topofile
params_file = args.paramsfile
device = torch.device(args.device)
EPISODES = args.episodes
model  = args.model
strategy = args.strategy
if_train = args.train

model_file = args.modelparams
reward_file = args.reward
loss_file = args.loss

#导入文件
with open(args.configfile, 'r',encoding='utf-8') as f:
   config = yaml.safe_load(f)

#创建仿真器
def Stop_func() -> bool:
    return all(user.task_count > int(config['user']['max_tasks']) for user in MyUser.all())

params = MySimulator.get_ParamsFromFile(input_file=params_file)

simulator = MySimulator(
    stopping_criterion=Stop_func,
    scheduler=MyScheduler,
    params=params
)
#设置策略
simulator.policy = strategy
simulator.setUp(input_file=topo_file)
print(f"policy:{simulator.policy}")

#构建环境
Cpn_env = CpnEnvironment(num_task=config['user']['task_num'],num_node=config['server']['nums'],
                         simulator=simulator, device=device)
#状态空间维度
state_dim = Cpn_env.state_dim
#动作空间维度
action_dim = Cpn_env.action_dim


#根据类型构建构建智能体
match model:
    case 'none':
        agent = None
    case 'ppo':
        agent_params = config[model]
        agent = PPO(state_dim=state_dim, hidden_dim=int(agent_params['HIDDEN_SIZE']), action_dim=action_dim,
            actor_lr=float(agent_params['ACTOR_LR']), critic_lr=float(agent_params['CRITIC_LR']),
            lmbda=float(agent_params['LAMBDA']), epochs=int(agent_params['EPOCHS']), eps=float(agent_params['EPS']),
            gamma=float(agent_params['GAMMA']), batch_size=int(agent_params['BATCH_SIZE']), device=device)
    case 'dqn':
        agent_params = config[model]
        agent = DQN(n_actions=action_dim, n_features=state_dim, n_hidden=int(agent_params['HIDDEN_SIZE']),
            update_T=int(agent_params['TARGET_UPDATE_FREQ']), memory_size=int(agent_params['MEMORY_CAPACITY']),
            batch_size=int(agent_params['BATCH_SIZE']),
            epsilon_start=float(agent_params['EPS_START']), epsilon_end=float(agent_params['EPS_END']),
            epsilon_decay=float(agent_params['EPS_DECAY']),
            learning_rate=float(agent_params['LR']), device=device)
    case 'none':
        agent = None


#训练函数
def train(model_file,reward_file,loss_file,agent,online:bool = False):
    # 统计量
    episode_rewards_custom = []
    episode_losses_custom = []
    num_episodes = EPISODES
    dirname =  'Test/'
    for i in range(50):
        with tqdm(total=int(num_episodes / 50), desc='Iteration %d' % i) as pbar:
            for i_episode in range(int(num_episodes/50)):
                #设置随机数种子
                np.random.seed(int(num_episodes / 50 * i + i_episode + 1))
                random.seed(int(num_episodes / 50 * i + i_episode + 1))
                torch.random.manual_seed(int(num_episodes / 50 * i + i_episode + 1))

                #在线策略
                transition_dict = {'states': [], 'actions': [],'next_states': [], 'rewards': [], 'dones': []}

                #重置环境
                state  = Cpn_env.reset()
                done = False
                total_reward = 0
                while not done:
                    action = agent.take_action(state)
                    next_state, reward, done = Cpn_env.step(action)
                    total_reward += reward
                    total_loss = []
                    #存储样本
                    if online:
                            transition_dict['states'].append(state)
                            transition_dict['actions'].append(action)
                            transition_dict['next_states'].append(next_state)
                            transition_dict['rewards'].append(reward)
                            transition_dict['dones'].append(done)
                    else:
                            agent.store_transition(state, action, reward, next_state,done)


                    Cpn_env.simulator.schedule.steps += 1
                    Cpn_env.simulator.schedule.time += 1
                    if not online:
                        if agent.memory.counter > agent_params['MEMORY_THRESHOLD']:
                            loss = agent.learn()
                            if loss is not None:
                                total_loss += loss
                    if done:
                        break
                    state = next_state
                if online:
                    total_loss = agent.update(transition_dict)
                else: total_loss /=  Cpn_env.simulator.schedule.steps
                #存储每次迭代的结果
                episode_rewards_custom.append(total_reward)
                episode_losses_custom.append(total_loss)
                pbar.update(1)
                # 每 10 次迭代打印一次进度
                # TODO：改用tdqm显示,每5次迭代更新一次最近5次累计奖励的平均值
                if (i_episode + 1) % 5 == 0:
                    pbar.set_postfix({'episode': '%d' % (num_episodes / 50 * i + i_episode + 1),
                                      'return': '%.3f' % np.mean(episode_rewards_custom[-5:]),
                                      'loss': '%.3f' % np.mean(episode_losses_custom[-5:])})
                #TODO:保存数据
                if int(num_episodes / 50 * i + i_episode + 1) % 50 == 0:
                    agent.save_model(dirname+model_file)
                    with open(dirname+reward_file,"wb") as f:
                        pickle.dump(episode_rewards_custom, f)
                    with open(dirname+loss_file,"wb") as f:
                        pickle.dump(episode_losses_custom, f)

#测试函数
def test(strategy,agent:object=None):
    episode_total_delay = []
    episode_total_E = []
    episode_success_rate = []
    episode_max_delay = []
    for i_episode in range(EPISODES):
        np.random.seed(i_episode)
        random.seed(i_episode)
        torch.random.manual_seed(i_episode)

        #TODO：静态策略与动态策略的主要区别
        if strategy != "dynamic": #静态策略
            # 每次重置环境
            simulator.reset()
            while simulator.running:
                # 由用户生成任务并上传到CPNRouter中
                time_intervals = 0
                for user in MyUser.all():
                    time_intervals = user.step()
                # 将任务上传到调度器
                for router in CpnRouter.all():
                    router.step()
                # 所有服务器步进，更新到当前时刻最新状态
                for node in CpnNode.all():
                    node.step(time_intervals)
                # 控制器进行决策
                for controller in Controller.all():
                    controller.step()
                # 步数+1
                simulator.schedule.steps += 1
                simulator.running = not simulator.stopping_criterion()
        else:#'dynamic'
            # 重置环境
            state = Cpn_env.reset()
            done = False
            total_reward = 0
            while not done:
                action = agent.take_action(state)  # 测试评估时使用evaluate
                next_state, reward, done = Cpn_env.step(action)
                total_reward += reward
                Cpn_env.simulator.schedule.steps += 1
                Cpn_env.simulator.schedule.time += 1

                if done:
                    break
                state = next_state

        # #打印数据
        simulator.monitor()
        episode_total_delay.append(simulator.total_delay)
        episode_total_E.append(simulator.total_E)
        episode_success_rate.append(simulator.success_ratio)
        episode_max_delay.append(simulator.max_delay)
        # 打印单次的结果
        print(f'episode:{i_episode + 1} | total_delay:{round(simulator.total_delay, 2)}s |'
              f'total_E:{round(simulator.total_E, 2)}J | '
              f'success_ratio:{round(simulator.success_ratio * 100, 2)}% |'
              f'max_delay:{round(simulator.max_delay, 2)}')

    # 迭代结束后计算平均值
    avg_delay = np.mean(episode_total_delay)
    avg_E = np.mean(episode_total_E)
    avg_success_rate = np.mean(episode_success_rate)
    avg_max_delay = np.mean(episode_max_delay)
    print("avg_delay(s):", avg_delay)
    print("avg_E(J):", avg_E)
    print("avg_success_rate(%):", round(avg_success_rate * 100, 2))
    print("avg_max_delay(s):", round(avg_max_delay, 2))
    pass

if __name__ == '__main__':
    #训练 or 测试
    if strategy == "dynamic":
        train(model_file='model/'+model+'/'+model_file,reward_file='result/'+model+'/reward/'+reward_file,
              loss_file='result/'+model+'/loss/'+loss_file,agent=agent,online = True if model=='ppo' else False)
    else:
        test(strategy,agent)
