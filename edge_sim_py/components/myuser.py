""" Contains user-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.user import User
from edge_sim_py.components.Task import Task
# Mesa modules
from mesa import Agent

# Python libraries
import copy
import networkx as nx

import numpy as np


#不同SLA等级下的最小带宽，最大时延和资源成本敏感系数
sla_list={
    "min_bw":[[2,4],[4.0,6.0],[6.0,10.0]],
    "max_delay":[[25,40],[12,25],[8,12]],
    "price_gamma":[[0.8,1],[0.4,0.8],[0.2,0.4]]
}

#不同任务类型的资源需求取值范围
task_list={
    "cpu_flops":[[1,5],[5,10],[10,40]],
    "gpu_flops":[[10,50],[50,200],[200,1000]],
    "cpu":[[1,2],[1,4],[4,8]],
    "gpu":[[1000,4000],[4000,10000],[10000,15000]],
    "disk":[[5,10],[10,40],[40,80]]
}

areaID_list=[1,2,3,4]


class MyUser(User):
    def __init__(self,obj_id: int = None,lambda_rate:float = 2,area_ID:int=None,model:object=None)->object:
        User.__init__(self,obj_id)
        # 任务产生泊松过程的平均到达率
        self.lambda_rate = lambda_rate
        # 产生任务
        self.task = None
        # 任务类型
        self.task_type = None
        # 服务SLA等级
        self.sla_level = None
        # 累积生成任务数量
        self.task_count = 0
        # 区域ID -> 作为task ID
        self.area_ID = area_ID

        #上一次生成任务的时间步
        self.last_task_step = 0
        # 预期生成任务的时间间隔
        self.time_intervals = 0

        self.model = model

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """

        dictionary = {
            "attributes": {
                "id": self.id,
                "lambda_rate": self.lambda_rate,
                "area_ID": self.area_ID
            },
            "relationships": {
                "current_service":self.task,
            },
        }
        return dictionary

    def collect(self) -> dict:
        metrics = {
            "id": self.id,
            "lambda_rate": self.lambda_rate,
            "area_ID": self.area_ID,
            "task_count" : self.task_count,
            "current_service": self.task.collect() if self.task else 'None',
            "task_type":self.task_type,
            "sla_level":self.sla_level
        }
        return metrics


    def step(self):
        #TODO:根据间隔时间生成任务
        #1.初始先生成随机时间间隔
        if self.last_task_step == 0 and self.time_intervals <= 0:
            self.time_intervals = np.random.exponential(scale=1/self.lambda_rate)

        #2.判断是否已经到达生成新任务的时间步
        if self.model.schedule.steps - self.last_task_step >= round(self.time_intervals):
            # 生成新任务
            self.task = self.generate_newTask()
            self.task_count += 1
            # 更新last_task_step并生成新的时间间隔
            self.last_task_step = self.model.schedule.steps
            self.time_intervals = np.random.exponential(scale=1/self.lambda_rate)

            # 将任务上传到区域内的CPN路由器缓存队列上
            self.task.step()

            print(self.task.collect())


    def generate_newTask(self):
        #TODO:生成新任务
        #随机生成任务类型
        task_type = np.random.randint(1,4)
        sla_level = np.random.randint(1,4)


        demand={
             "cpu_flops":round(np.random.rand()*(task_list["cpu_flops"][task_type-1][1]-task_list["cpu_flops"][task_type-1][0])
                                   +task_list["cpu_flops"][task_type-1][0]),
            "gpu_flops":round(np.random.rand()*(task_list["gpu_flops"][task_type-1][1]-task_list["gpu_flops"][task_type-1][0])
                                   +task_list["gpu_flops"][task_type-1][0]),
             "cpu":np.random.randint(low = task_list["cpu"][task_type-1][0],high = task_list["cpu"][task_type-1][1]),
            "gpu":np.random.randint(low = task_list["gpu"][task_type-1][0],high = task_list["gpu"][task_type-1][1]),
            "disk":np.random.randint(low=task_list["disk"][task_type-1][0],high=task_list["disk"][task_type-1][1]+1),
        }

        sla ={
            "min_bw": round(np.random.rand()*(sla_list["min_bw"][sla_level-1][1]-sla_list["min_bw"][sla_level-1][0])
                                   +sla_list["min_bw"][sla_level-1][0],1),

            "max_delay": round(np.random.rand()*(sla_list["max_delay"][sla_level-1][1]-sla_list["max_delay"][sla_level-1][0])
                                   +sla_list["max_delay"][sla_level-1][0],1),

            "price_gamma": round(np.random.rand()*(sla_list["price_gamma"][sla_level-1][1]-sla_list["price_gamma"][sla_level-1][0])
                                   +sla_list["price_gamma"][sla_level-1][0],1)
        }


        task = Task(area_ID=self.area_ID,status='init',demand=demand,sla=sla,task_type=task_type,sla_level=sla_level)
        self.task_type = task_type
        self.sla_level = sla_level

        return task





