
import numpy as np
from mesa import Agent

from edge_sim_py import CpnNode
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.task_schedulers import *
import copy

class Controller(ComponentManager,Agent):
    _instances = []
    def __init__(self,id:int=1,policy:str="random",cpn_nodes:list=[],model:object=None):

        self.id = id
        self.model = model
        self.policy = policy
        self.schedule_services = [] #待调度任务
        self.cpn_nodes = cpn_nodes #算力节点集合
        self.task_count = 0 #总计任务数量
        self.unsuccess_count = 0  #未成功调度任务数量

        self.__class__._instances.append(self)

        self.model = None
        self.unique_id = None

    def _to_dict(self):
        dictionary = {
            "attributes": {
                "id": self.id,
                "policy": self.policy,
                "task_count": self.task_count,
                "unsuccess_count": self.unsuccess_count,
            },
            "relationships": {
                "schedule_services":self.schedule_services,
                "cpn_nodes": self.cpn_nodes
            },
        }
        return dictionary


    def step(self,node=None)->list:
        if len(self.schedule_services)>0:
            self.task_count += len(self.schedule_services) # 累积总任务数量
            if self.policy=="dynamic":
                    self.dynamic_policy(node,np.random.choice([1,2,5]))
            elif self.policy=="random":
                    self.random_policy()
                #TODO:其他静态策略
            elif self.policy=="EFT":
                    self.EFT_policy()
            elif self.policy=="EDA":
                    self.ECA_policy()
            elif self.policy=="EES":
                    self.ECS_policy()
            else:
                    print("Unknown policy: " + self.policy)
        services = copy.deepcopy(self.schedule_services)
        self.schedule_services = [] #清空调度列表
        return services


    # 随机策略
    def random_policy(self):
        count = 0
        for  service in self.schedule_services:
             node = np.random.choice(self.cpn_nodes)
             count = 1
             # 随机生成带宽等级
             service.min_bw_demand = np.random.choice([1,2,5])
             while((not node.has_capacity_to_host(service)) and count <= 10):
                 np.random.seed(count)
                 node = np.random.choice(self.cpn_nodes)
                 count+=1

             if count>10:
                 # print("No cpn node can host the task!")
                 self.unsuccess_count += 1
             else:
                 target_server = node
                 # 部署并分配带宽资源
                 service.bw_demand = service.min_bw_demand
                 service.provision(target_server)

    #智能策略
    def dynamic_policy(self,node,bw):
        if type(node)==list and type(bw)==list:
            for i in range(len(self.schedule_services)):
                service = self.schedule_services[i]
                service.min_bw_demand = bw[i]
                if node[i].has_capacity_to_host(service):
                    service.bw_demand = bw[i]
                    service.provision(node[i])
                else:
                    service.status='end'
                    self.unsuccess_count += 1
        else:
            for i in range(len(self.schedule_services)):
                service = self.schedule_services[i]
                service.min_bw_demand = bw
                #当前决策下是否具有足够的资源可供部署
                if node.has_capacity_to_host(service):
                    service.bw_demand = bw
                    service.provision(node)
                else:
                    #没有足够资源则任务部署失败
                    service.status = 'end'
                    self.unsuccess_count += 1

    #EFT时延最小
    def EFT_policy(self):
        for service in self.schedule_services:
            target_server = EFT(service,CpnNode.all())
            if target_server is not None:
                service.provision(target_server)
            else: self.unsuccess_count += 1

    #ECA时延与成本乘积最小
    def ECA_policy(self):
        for service in self.schedule_services:
            target_server = ECA(service,CpnNode.all())
            if target_server is not None:
                service.provision(target_server)
            else: self.unsuccess_count += 1

    #ECS：成本最小
    def ECS_policy(self):
        for service in self.schedule_services:
            target_server = ECS(service,CpnNode.all())
            if target_server is not None:
                service.provision(target_server)
            else: self.unsuccess_count += 1