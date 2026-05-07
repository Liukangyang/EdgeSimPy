import torch

from edge_sim_py import MyUser, CpnRouter, Controller, CpnNode
from edge_sim_py.drl_model.rl_utils import *
import numpy as np


# CPN网络环境
class CpnEnvironment:
    '''
    初始化
    '''

    def __init__(self, num_task, num_node, simulator, device, state_min=None, state_max=None):
        self.task_state = None  # 任务状态表征

        self.cpn_state = None  # CPN节点状态表征

        self.state = []  # 全局状态=（任务状态，Cpn节点状态）

        self.action = None

        self.device = device

        self.simulator = simulator  # 仿真器

        self.action_dim = num_node
        # 状态空间维度
        self.state_dim = num_task * 3 + num_node * 10

        # 惩罚系数
        # self.p1=-5 #资源约束惩罚
        self.P2 = 100  # 时延奖励系数，看是否满足时延

        # 当前奖励
        self.reward = 0
        # 状态
        self.state = None
        # 动作
        self.action = None

        # 各维度状态最小和最大值
        self.state_min = state_min
        self.state_max = state_max

    """
    重置环境到起始状态。

    返回：
        torch.Tensor：起始状态作为归一化的张量。
    """

    def reset(self):
        # 重置环境
        self.simulator.reset()

        # 初始任务生成，并上传到调度器
        for user in MyUser.all():
            user.step()
        for router in CpnRouter.all():
            router.step()
        # 组装状态向量
        # 任务状态
        state = []
        service = None
        for controller in Controller.all():
            for task in controller.schedule_services:
                task_state = task.get_State()
                state.extend(task_state)
                service = task
        # CPN节点状态
        task = Controller.all()[0].schedule_services[0]
        for node in CpnNode.all():
            cpn_state = node.get_State(task)
            state.extend(cpn_state)

        self.state = state
        self.reward = 0
        return state

    '''
    步进
    '''

    def step(self, action):
        # 1.执行动作
        # selected_node = CpnNode.all()[action]

        #TODO,解析组合动作
        if action[0] == 0: #Cloud
            selected_node = CpnNode.all()[action[1]+16]
        else: #edge_server
            selected_node = CpnNode.all()[action[1]]

        for controller in Controller.all():
            services = controller.step(selected_node)
        # 2.计算奖励值
        R1 = 0
        R2 = 0
        reward = 0
        # 计算任务的能耗
        for service in services:
            R1 += -service.E
            if service.delay <= service.max_delay:
                R2 += self.P2
            else:
                R2 += -self.P2
            # R2 += service.delay
            # if service.delay <= service.max_delay:
            #     R3 += self.P2
        reward = R1 + R2

        # 3.更新状态
        # (1)用户生成任务
        time_intervals = 0
        for user in MyUser.all():
            time_intervals = user.step()
        for agent in CpnRouter.all():
            agent.step()
        # (2)根据时间间隔令服务器步进
        for node in CpnNode.all():
            node.step(time_intervals)

        # 4.获取新的状态向量
        new_state = []
        if len(Controller.all()[0].schedule_services) > 0:
            for task in Controller.all()[0].schedule_services:
                task_state = task.get_State()
                new_state.extend(task_state)
        else:
            new_state.extend([0, 0, 0])  # 空任务

        task = Controller.all()[0].schedule_services[0] if len(Controller.all()[0].schedule_services) > 0 else None
        for node in CpnNode.all():
            new_state.extend(node.get_State(task))

        done = self.simulator.stopping_criterion()

        self.state = new_state
        self.reward = reward
        # 4.返回结果(s',r,done)
        return new_state, reward, done

    def render(self):
        pass

    def get_State(self):
        return self.state

    def get_Reward(self):
        return self.reward
