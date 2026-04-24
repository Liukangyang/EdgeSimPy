""" Contains user-related functionality."""
""" Contains user-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.user import User
from edge_sim_py.components.task import Task
# Mesa modules
from mesa import Agent

# Python libraries
import copy
import networkx as nx

import numpy as np

import yaml

with open('D:\学习文档资料\CPN仿真\edgesimpy\RL-PPO\Test\config.yaml', 'r',encoding='utf-8') as ymlfile:
    config=yaml.safe_load(ymlfile)


class MyUser(User):
    def __init__(self,obj_id: int = None,lambda_rate:float = 2,
                 generate_mode=0,area_ID:int=None,router:object=None,
                 model:object=None)->object:
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
        #关联路由
        self.router = router

        #上一次生成任务的时间步
        self.last_task_step = 0
        # 预期生成任务的时间间隔
        self.time_intervals = 0
        # 任务生成模式
        self.generate_mode = generate_mode

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
        #按指定数量任务
        if self.task_count >= 500 :
            return 20 #不生成任务，则每隔20s更新环境
        if self.generate_mode == 0:
            num = 10
            for i in range(num):
                self.task = self.generate_newTask()
                self.task_count += 1 #累积生成任务数量
                # 更新last_task_step并生成新的时间间隔
                self.last_task_step = self.model.schedule.steps
                # 将任务上传到调度器
                self.task.step()
        #按照泊松过程生成一个任务:
        elif self.generate_mode == 1:
            self.time_intervals = np.random.exponential(scale=1 / self.lambda_rate)
            # self.time_intervals = np.clip(self.time_intervals,0.1,0.5)
            self.task = self.generate_newTask()
            self.task_count += 1
            self.last_task_step += self.time_intervals
            self.task.step()
        return self.time_intervals


    def generate_newTask(self)->object:
        #生成并返回任务对象
        length = [50,100]
        memory = [0.1,5]
        avg = 15   #以s为单位
        d = np.sqrt(2) #方差
        scope = [1,30]

        task_length = np.random.uniform(low=length[0],high=length[1])
        task_size = np.random.uniform(low=memory[0],high=memory[1])
        max_delay = np.random.randn()*d + avg
        max_delay = np.clip(max_delay,scope[0],scope[1])

        #生成任务
        task = Task(demand={'cpu_demand':task_length,'memory_demand':task_size},
                    max_delay=max_delay,status='init',router=self.router,model=self.model)
        return task






