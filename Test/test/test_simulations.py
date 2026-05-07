import unittest
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.environments import CpnEnvironment
from edge_sim_py.drl_model import PPO
import numpy as np
import random
import torch
import yaml
import tqdm

TEST_EPISODES = 10
class SimulationTestCase(unittest.TestCase):
    def testSimulation(self):
        print("test simulation")
        np.random.seed(0)

        #TODO:停止标准，达到指定数量任务且所有认为均完成
        def Stop_func(self) -> bool:
           return  all(user.task_count>=400 for user in MyUser.all())

        params = MySimulator.get_ParamsFromFile(input_file='Test/file/params.json')

        simulator =  MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        simulator.setUp(input_file='Test/file/test1.json')

        print(f"policy:{simulator.policy}")
        #统计量
        episode_total_delay=[]
        episode_total_E=[]
        episode_success_rate=[]
        for i_episode in range(TEST_EPISODES):
            np.random.seed(i_episode)
            random.seed(i_episode)
            #每次重置环境
            simulator.reset()
            #测试一次迭代
            while simulator.running:
                #由用户生成任务并上传到CPNRouter中
                time_intervals =  0
                for user in MyUser.all():
                    time_intervals = user.step()
                #将任务上传到调度器
                for router in CpnRouter.all():
                    router.step()
                #所有服务器步进，更新到当前时刻最新状态
                for node in CpnNode.all():
                    node.step(time_intervals)
                # 控制器进行决策
                for controller in Controller.all():
                    controller.step()
                #步数+1
                simulator.schedule.steps += 1
                simulator.running = not simulator.stopping_criterion(simulator)
            # print(MyUser.all()[0].task_count)
            # #打印数据
            simulator.monitor()
            episode_total_delay.append(simulator.total_delay)
            episode_total_E.append(simulator.total_E)
            episode_success_rate.append(simulator.success_ratio)
            #打印单次的结果
            print(f'episode:{i_episode+1} | total_delay:{round(simulator.total_delay,2)}s |'
                  f'total_E:{round(simulator.total_E,2)}J | '
                  f'success_ratio:{round(simulator.success_ratio*100,2)}%,')

        #迭代结束后计算平均值
        avg_delay = np.mean(episode_total_delay)
        avg_E = np.mean(episode_total_E)
        avg_success_rate = np.mean(episode_success_rate)
        print("avg_delay(s):",avg_delay)
        print("avg_E(J):",avg_E)
        print("avg_success_rate(%):",round(avg_success_rate*100,2))

    def testPPO(self):
        print("PPO test")
        with open("Test/config.yaml", 'r',encoding='utf-8') as f:
            config = yaml.safe_load(f)



        # 创建仿真器
        def Stop_func() -> bool:
            return all(user.task_count > int(config['ppo']['MAX_STEPS_PER_EPISODE']) for user in MyUser.all())

        params = MySimulator.get_ParamsFromFile(
            input_file='Test/file/params.json')

        simulator = MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        simulator.setUp(input_file='Test/file/test1.json')
        print(f"policy:{simulator.policy}")

        # 构建环境
        device = torch.device("cuda:4" if torch.cuda.is_available() else "cpu")
        Cpn_env = CpnEnvironment(num_task=config['user']['task_num'], num_node=config['server']['nums'],
                                 simulator=simulator, device=device)
        # 状态空间维度
        state_dim = Cpn_env.state_dim
        # 动作空间维度
        action_dim = Cpn_env.action_dim

        agent_params = config['ppo']
        num_episodes = int(agent_params['NUM_EPISODES'])
        # 构建智能体
        agent = PPO(state_dim=state_dim, hidden_dim=int(agent_params['HIDDEN_SIZE']), action_dim=action_dim,
                    actor_lr=float(agent_params['ACTOR_LR']), critic_lr=float(agent_params['CRITIC_LR']),
                    lmbda=float(agent_params['LAMBDA']), epochs=int(agent_params['EPOCHS']),
                    eps=float(agent_params['EPS']),
                    gamma=float(agent_params['GAMMA']), batch_size=int(agent_params['BATCH_SIZE']), device=device)
        #导入模型参数
        agent.load_model(file="Test/result/ppo-single/ppo_params_200.pth")

        #统计量
        episode_total_delay=[]
        episode_total_E=[]
        episode_success_rate=[]
        for i_episode in range(TEST_EPISODES):
                    # 设置随机数种子
                    np.random.seed(i_episode)
                    random.seed(i_episode)
                    torch.random.manual_seed(i_episode)

                    # 重置环境
                    state = Cpn_env.reset()
                    done = False
                    # total_reward = 0
                    while not done:
                        action = agent.take_action(state)
                        next_state, reward, done = Cpn_env.step(action)
                        # total_reward += reward
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
                    # 打印单次的结果
                    print(f'episode:{i_episode + 1} | total_delay:{round(simulator.total_delay, 2)}s |'
                          f'total_E:{round(simulator.total_E, 2)}J | '
                          f'success_ratio:{round(simulator.success_ratio * 100, 2)}%,')

        #迭代结束后计算平均值
        avg_delay = np.mean(episode_total_delay)
        avg_E = np.mean(episode_total_E)
        avg_success_rate = np.mean(episode_success_rate)
        print("avg_delay(s):",avg_delay)
        print("avg_E(J):",avg_E)
        print("avg_success_rate(%):",round(avg_success_rate*100,2))