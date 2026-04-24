import torch

from edge_sim_py import MyUser, CpnRouter, Controller, CpnNode
import numpy as np

#CPN网络环境
class CpnEnvironment:
    '''
    初始化
    '''
    def __init__(self,num_task,num_node,state_min,state_max,simulator,device):
        self.task_state = None #任务状态表征

        self.cpn_state = None #CPN节点状态表征

        self.state = []  #全局状态=（任务状态，Cpn节点状态）

        self.action = None

        self.device = device

        self.simulator = simulator #仿真器


        self.action_dim = num_node
        #状态空间维度
        self.state_dim = num_task*3 + num_node*8

        #惩罚系数
        self.p1=-5 #资源约束惩罚
        self.p2=1 # 时延惩罚系数，看是否满足时延

        #当前奖励
        self.reward = 0
        #状态
        self.state = None
        #动作
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
        for controller in Controller.all():
            for task in controller.schedule_services:
                task_state = task.get_State()
                state.extend(task_state)
        #CPN节点状态
        for node in CpnNode.all():
            cpn_state = node.get_State()

        pass
