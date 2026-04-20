import heapq

import numpy as np
from mesa import Agent

from edge_sim_py import CpnNode
from edge_sim_py.component_manager import ComponentManager
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


    def step(self,node)->list:
        if len(self.schedule_services)>0:
            self.task_count += len(self.schedule_services) # 累积总任务数量
            if len(self.cpn_nodes)>0:
                if self.policy=="random":
                    self.random_policy()
                elif self.policy=="dynamic":
                    self.dynamic_policy(node)
                else: #TODO:实现其他对比策略
                    print("Unknown policy: " + self.policy)
            else: print("No available cpn node available!")
        services = copy.deepcopy(self.schedule_services)
        self.schedule_services = [] #清空调度列表
        return services


    #随机策略
    def random_policy(self):
        count = 0
        for  service in self.schedule_services:
             node = np.random.choice(CpnNode.all())
             count = 1
             while((not node.has_capacity_to_host(service)) and count <= 10):
                 node = np.random.choice(self.cpn_nodes)
                 count+=1

             if count>20:
                 # print("No cpn node can host the task!")
                 self.unsuccess_count += 1
             else:
                 target_server = node
                 service.provision(target_server)

    ####### TODO：智能策略
    def dynamic_policy(self,node):
        if type(node)==list:
            for i in range(len(self.schedule_services)):
                service = self.schedule_services[i]
                if node[i].has_capacity_to_host(service):
                    service.provision(node[i])
                else:
                    service.status='end'
                    self.unsuccess_count += 1
        else:
            for i in range(len(self.schedule_services)):
                service = self.schedule_services[i]
                #当前决策下是否具有足够的资源可供部署
                if node.has_capacity_to_host(service):
                    service.provision(node)
                else:
                    #没有足够资源则任务部署失败
                    service.status = 'end'
                    self.unsuccess_count += 1


