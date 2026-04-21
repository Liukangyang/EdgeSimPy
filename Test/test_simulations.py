import unittest
from edge_sim_py.simulator import Simulator
from edge_sim_py.mysimulator import MySimulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
import numpy as np
import random


TEST_EPISODES = 100
class SimulationTestCase(unittest.TestCase):
    def testSimulation(self):
        print("test simulation")
        np.random.seed(1)

        #停止标准：步进次数达到指定步数
        def Stop_func(self) -> bool:
           return (self.schedule.steps >= self.max_steps and all(task.status=='end' or task.being_provisioned==False for task in Task.all()))

        params = MySimulator.get_ParamsFromFile(input_file='Test/params.json')
        simulator =  MySimulator(
            stopping_criterion=Stop_func,
            scheduler=MyScheduler,
            params=params
        )
        simulator.setUp(input_file='Test/test1.json')

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
                for user in MyUser.all():
                    user.step()
                #将任务上传到调度器
                for router in CpnRouter.all():
                    router.step()
                # 控制器进行决策
                for controller in Controller.all():
                    controller.step()
                # 算力节点执行任务
                for node in CpnNode.all():
                    node.step()
                #步数+1
                simulator.schedule.steps += 1
                simulator.running = not simulator.stopping_criterion(simulator)
            # #打印数据
            simulator.monitor()
            episode_total_delay.append(simulator.total_delay)
            episode_total_E.append(simulator.total_E)
            episode_success_rate.append(simulator.success_ratio)
            #打印单次的结果
            print(f'episode:{i_episode+1} | total_delay:{round(simulator.total_delay,2)}s |'
                  f'total_E:{round(simulator.total_E,2)}J | '
                  f'success_ratio:{round(simulator.success_ratio,2)}%,')

        #迭代结束后计算平均值
        avg_delay = np.mean(episode_total_delay)
        avg_E = np.mean(episode_total_E)
        avg_success_rate = np.mean(episode_success_rate)
        print("avg_delay(s):",avg_delay)
        print("avg_E(J):",avg_E)
        print("avg_success_rate(%):",round(avg_success_rate*100,2))
