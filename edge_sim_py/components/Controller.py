import heapq

import numpy as np
from mesa import Agent

from edge_sim_py.component_manager import ComponentManager


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


    def step(self):
        if len(self.schedule_services)>0:
            self.task_count += len(self.schedule_services) # 累积总任务数量
            if len(self.cpn_nodes)>0:
                if self.policy=="random":
                    self.random_policy()
                elif self.policy=="static":
                    self.static_policy()
                elif self.policy=="dynamic":
                    self.dynamic_policy()
                else:
                    print("Unknown policy: " + self.policy)
            else: print("No available cpn node available!")

        self.schedule_services = [] #清空调度列表


    ####### 随机策略
    def random_policy(self):
        count = 0
        for  service in self.schedule_services:
             n = np.random.randint(len(self.cpn_nodes))
             count = 1
             while(not self.cpn_nodes[int(n)].has_capacity_to_host(service) and count <= len(self.cpn_nodes)+1):
                 n = np.random.randint(0, len(self.cpn_nodes))
                 count+=1

             if count>len(self.cpn_nodes)+1:
                 print("No cpn node can host the task!")
                 self.unsuccess_count += 1
             else:
                 target_server = self.cpn_nodes[n]
                 # 部署并分配带宽资源
                 service.bw_demand = service.min_bw_demand
                 service.provision(target_server)

    ####### 静态策略
    def static_policy(self):
        # 将每个任务分配给位于同一区域内的或距离最近的CPN节点
        for service in self.schedule_services:
            area_ID = service.area_ID

            find = False
            target_server = None
            # 遍历算力节点
            for cpn_node in self.cpn_nodes:
                if cpn_node.area_ID == area_ID:
                    find = True
                    target_server = cpn_node
                    break

            #未找到同一区域内的，找距离最近的
            if find == False:
                _, link_delay = self.model.topology._shortest_path(origin=service.cpn_router, target=self.cpn_nodes[0])
                target_server = self.cpn_nodes[0]
                for i in range(1,len(self.cpn_nodes)):
                    _,delay = self.model.topology._shortest_path(origin=service.cpn_router, target=self.cpn_nodes[i])
                    if delay < link_delay:
                        link_delay = delay
                        target_server = self.cpn_nodes[i]
                find = True

            if find == True:
                if target_server.has_capacity_to_host(service):
                    # 部署并分配带宽资源
                    service.bw_demand = service.min_bw_demand
                    service.provision(target_server)
                else:self.unsuccess_count += 1


    ####### TODO：智能策略
    def dynamic_policy(self):
        pass
    pass


