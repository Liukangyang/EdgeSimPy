import torch

from edge_sim_py import MyUser, CpnRouter, Controller, CpnNode
import numpy as np

class CpnEnvironment:
    '''
    初始化
    '''
    def __init__(self,num_task,num_node,Jain_min,state_min,state_max,simulator,device):
        self.task_state = None #任务状态表征

        self.cpn_state = None #CPN节点状态表征

        self.state = []  #全局状态=（任务状态，Cpn节点状态）

        self.action = None

        self.device = device

        self.simulator = simulator #仿真器

        #动作映射
        self.node_map={
            0:1,
            1:2,
            2:3,
        }
        self.bw_map={
            0:1,
            1:2,
            2:5
        }

        #动作空间维度
        self.bw_action_dim=len(self.bw_map)
        self.action_dim = len(self.node_map) * len(self.bw_map)
        #状态空间维度
        self.state_dim = num_task*7+num_node*10

        #负载均衡程度下限
        self.Jain_min = Jain_min

        #惩罚系数
        self.p1=-10
        self.p2=-10

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
        #重置环境
        self.simulator.reset()
        #重新产生用户
        self.simulator.initialize_Users()
        #任务生成：每一步每个用户生成一个任务
        for user in MyUser.all():
            user.step()
        for router in CpnRouter.all():
            router.step()
        #组装状态向量
        #任务状态
        state=[]
        for controller in Controller.all():
            for task in controller.schedule_services:
                task_state = task.get_State()
                state.extend(task_state)

        #CPN节点状态
        for node in CpnNode.all():
            cpn_state = node.get_State()
            state.extend(cpn_state)

        #转化为tensor量
        # state_tensor = torch.tensor(self.state,dtype=torch.float,device=self.device)
        # state_tensor  = state_tensor.unsqueeze(0)
        state = self.normalized_state(state) #归一化处理
        self.state = state
        return state


    '''
    步进
    '''
    def step(self,action):
        #1.解析动作
        #TODO:转化为选择的CPN节点对象
        selected_node = CpnNode.all()[self.node_map[action // self.bw_action_dim]-1]
        bw = self.bw_map[action % self.bw_action_dim]
        #2.执行动作
        services=[]
        for controller in Controller.all():
             services = controller.step(selected_node,bw)

        #3.计算奖励值
        reward = 0
        for service in services:
            if not service.being_provisioned: #不满足资源约束未成功部署
               reward += self.p1
            else:#计算效用+时延超出惩罚
               delay = service.trans_sustain_steps + service.comp_sustain_steps
               max_delay = service.max_delay
               reward += (max_delay-delay) - service.price_gamma*service.resource_cost
        #惩罚部分：负载均衡判断
        Jain = self.simulator.get_D()
        if Jain<self.Jain_min:
            reward += self.p2

        done = self.simulator.stopping_criterion()

        #4.更新状态
           #更新算力节点
        for node in CpnNode.all():
            node.step()
           #生成新的任务
        for user in MyUser.all():
           user.step()
        for router in CpnRouter.all():
           router.step()

        #获取新的状态
        new_state=[]
        for controller in Controller.all():
            for task in controller.schedule_services:
                task_state = task.get_State()
                new_state.extend(task_state)

        #CPN节点状态
        for node in CpnNode.all():
            cpn_state = node.get_State()
            new_state.extend(cpn_state)

        self.reward = reward
        #归一化处理
        new_state = self.normalized_state(new_state)
        self.state = new_state

        #5.返回(s',r,done)
        return new_state,reward,done

    '''
    状态向量归一化
    '''
    # 状态向量归一化
    def normalized_state(self,state)->list:
        for i in range(len(state)):
            state_range = np.maximum(self.state_max[i] - self.state_min[i], 1e-4)
            state[i] = (state[i]-self.state_min[i])/state_range
            state[i] = np.clip(state[i],0.0,1.0)
        return state
    '''
    结果记录
    '''
    def render(self):
        #打印当前结果记录
        print(f"steps:{self.simulator.scheduler.steps},reward:{self.reward}")

    '''
    获取当前状态、动作或奖励函数
    '''
    def get_State(self):
        return self.state


    def get_Action(self):
        return self.action

    def get_Reward(self):
        return self.reward
