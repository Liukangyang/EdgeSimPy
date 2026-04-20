""" Contains user-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.user import User
from edge_sim_py.components import Task
# Mesa modules
from mesa import Agent

# Python libraries
import copy
import networkx as nx

import numpy as np




class MyUser(User):
    def __init__(self,obj_id: int = None,lambda_rate:float = 2,area_ID:int=None,model:object=None)->object:
        User.__init__(self,obj_id)
        # 任务产生泊松过程的平均到达率
        self.lambda_rate = lambda_rate
        # 产生任务
        self.task = None
        # # 任务类型
        # self.task_type = None
        # # 服务SLA等级
        # self.sla_level = None
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
                # "area_ID": self.area_ID
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
            # "area_ID": self.area_ID,
            "task_count" : self.task_count,
            "current_service": self.task,
            # "task_type":self.task_type,
            # "sla_level":self.sla_level
        }
        return metrics


    def step(self):
        #每次生成指定数量的任务
        pass



    def generate_newTask(self):
        #生成并返回任务对象

        pass






