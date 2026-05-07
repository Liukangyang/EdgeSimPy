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

from edge_sim_py import config


#不同SLA等级下的最小带宽，最大时延和资源成本敏感系数
sla_list=config.sla_list

#不同任务类型的资源需求取值范围
task_list=config.task_list

areaID_list=config.areaID_list


class MyUser(User):
    def __init__(self,obj_id: int = None,lambda_rate:float = 2,area_ID:int=None,model:object=None)->object:
        User.__init__(self,obj_id)
        # 任务产生泊松过程的平均到达率
        self.lambda_rate = lambda_rate
        # 产生任务
        self.task = None
        # 任务类型
        # self.task_type = None
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
            "current_service": self.task,
            "task_type":self.task_type,
            "sla_level":self.sla_level
        }
        return metrics


    def step(self):
        #按照泊松过程生成一个任务:
            self.time_intervals = np.random.exponential(scale=1 / self.lambda_rate)
            # self.time_intervals = np.clip(self.time_intervals,0.1,0.5)
            self.task = self.generate_newTask()
            self.task_count += 1
            self.last_task_step += self.time_intervals
            self.task.step()
            return self.time_intervals



    def generate_newTask(self):

        #TODO：随机生成任务类型
        task_type = 3 #固定任务类型为3
        sla_level = 2 #固定SLA等级为2
        #
        demand={
             "cpu_flops":round(np.random.rand()*(task_list["cpu_flops"][task_type-1][1]-task_list["cpu_flops"][task_type-1][0])
                                   +task_list["cpu_flops"][task_type-1][0]),
            "gpu_flops":round(np.random.rand()*(task_list["gpu_flops"][task_type-1][1]-task_list["gpu_flops"][task_type-1][0])
                                   +task_list["gpu_flops"][task_type-1][0]),
             "cpu":np.random.randint(low = task_list["cpu"][task_type-1][0],high = task_list["cpu"][task_type-1][1]+1),
            "gpu":np.random.randint(low = task_list["gpu"][task_type-1][0],high = task_list["gpu"][task_type-1][1]+1),
            "disk":np.random.randint(low=task_list["disk"][task_type-1][0],high=task_list["disk"][task_type-1][1]+1),
        }

        sla ={
            "min_bw":0, #初始带宽固定为0
            # 最大时延按照正态分布生成
            "max_delay":round(np.random.rand()*(sla_list["max_delay"][sla_level-1][1]-sla_list["max_delay"][sla_level-1][0])
                                   +sla_list["max_delay"][sla_level-1][0],1),

            "price_gamma": 1  #价格敏感系数
        }

        area_ID = self.area_ID

        task = Task(area_ID=area_ID,status='init',demand=demand,sla=sla,task_type=task_type,sla_level=sla_level,model=self.model)
        self.sla_level = sla_level

        return task





