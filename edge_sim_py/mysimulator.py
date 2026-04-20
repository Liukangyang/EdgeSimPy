# EdgeSimPy components
from edge_sim_py import Simulator
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers import *

# Mesa modules
from mesa import Model, Agent

# Python libraries
import os
import json
import msgpack
from typing import Callable
from datetime import timedelta
from urllib.parse import urlparse
from urllib.request import urlopen

import numpy as np
import json

SUPPORTED_TIME_UNITS = ["seconds", "microseconds", "milliseconds", "minutes"]

def get_Jain(x:list=[]):
    if len(x)==0 or len(x)==1:
        return 1
    else:
        n = len(x)
        sum_x = sum(x)
        sum_x_squared = sum(map(lambda x: x ** 2, x))
        jain_index = (sum_x ** 2) / (n * sum_x_squared)
        return jain_index

def get_Variance(x:list=[]):
    if len(x)==0 or len(x)==1:
        return 0
    else:
        n = len(x)
        avg = np.mean(x)
        V = np.sum([(e-avg)**2 for e in x]) / n
        return np.sqrt(V)

class MySimulator(Simulator):
    def __init__(self,
        stopping_criterion: Callable = None,  # 停止标准
        tick_duration: int = 1,
        tick_unit: str = "seconds",
        obj_id: int = None,
        scheduler: Callable = DefaultScheduler,  #调度器
        dump_interval: int = 100,
        params: dict = None,):
        Simulator.__init__(self,stopping_criterion=stopping_criterion,
                           tick_duration=tick_duration,tick_unit=tick_unit,
                           obj_id=obj_id, scheduler=scheduler,dump_interval=dump_interval)

        #用户列表
        self.users=[]

        # 仿真参数
        if params:
            self.params = params
        else:
            self.params = {
                #资源成本
                "cost":{
                    "Pb": .0,  # 单位带宽增量成本
                    "cpu":{
                        "base_price":.0,
                        "fbase": 0,
                        "C": .0,
                    },
                    "gpu":{
                        "base_price": .0,
                        "fbase": 0,
                        "C": .0,
                    },
                    "economy_vitality": [26751.86,11492.63,7305.89,6878.61],#
                },
                #用户参数
                "user":{
                    "lambda_rate":0.5,
                    "area_nums":1,
                    "user_nums":1,
                },
                "max_tasks":1,
                "policy":'random',
            }
        #预计最大任务数量
        self.max_tasks = self.params["max_tasks"]
        #部署策略
        self.policy = self.params["policy"]
        #仿真停止标准
        if self.stopping_criterion == None:
            self.stopping_criterion = lambda:  ( all( (task.status=='end' or task.status=='scheduled')for task in Task.all())
                                                    and self.schedule.total_count >= self.max_tasks)


    def run_model(self):
        """Executes the simulation."""
        if self.stopping_criterion == None:
            raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

        while self.running:
            # Calls the method that advances the simulation time
            self.step()

            # Calls the method that collects monitoring data about the agents
            # if self.schedule.steps % 5 == 0:
            #     self.monitor()
            # Checks if the simulation should end according to the stop condition
            if self.stopping_criterion():
                self.monitor()
            self.running = False if self.stopping_criterion() else True


    def step(self):
        self.schedule.step()

    def monitor(self):
        lines = []

        # 分隔标识（每步开始前添加，避免首行空分隔）
        if self.schedule.steps > 0:
            lines.append("\n" + "=" * 100)

        # 当前步数
        step_line = f" Step: {self.schedule.steps}"
        lines.append(step_line)
        for line in lines:
            print(line)

        # --- Servers 部分 ---
        print("Cpn-Nodes:")
        CpnNode.print_Servers_metric()

        # --- 累积任务数 ---
        MyScheduler.statistics()

        # --- Task部分 ---
        print("Tasks:")
        Task.print_Tasks_metric()

        # ----指标统计-----
        R_list = self.get_R()
        #min-max归一化
        min_R=min(R_list)
        max_R=max(R_list)
        for task in Task.all():
            task.efficiency = 1-(task.efficiency-min_R)/(max_R-min_R)
        R_list = self.get_R()
        D = self.get_D()

        print("total R:",sum(R_list))
        print("D:",D)

        # 指标结果
        # 所有任务总时延
        total_delay = 0
        # 所有任务总成本
        total_cost = 0
        success_tasks=0
        for task in Task.all():
            metrics = task.collect()
            total_delay += metrics["delay"]
            total_cost += metrics["resource_cost"]
        # 实际任务成功率（即满足时延要求）
            if task.being_provisioned==True and metrics["delay"]<=metrics["max_delay"]:
                success_tasks += 1

        print(f"total_delay:{round(total_delay,2)}, total_cost:{round(total_cost,2)}, success_rate:{round(success_tasks/len(Task.all())*100,2)}%")


    #初始随机生成用户
    def initialize_Users(self):
        for i in range(self.params["user"]["user_nums"]):
            area_ID = np.random.randint(low=1,high=self.params["user"]["area_nums"]+1)
            # area_ID = 3
            user = MyUser(lambda_rate=self.params["user"]["lambda_rate"],area_ID=area_ID,model=self)
            self.users.append(user)


    #重定义初始化
    def setUp(self,input_file: str)->None:
        self.initialize(input_file=input_file) # 初始化拓扑
        self.initialize_Users()  #初始化用户
        #设置控制器策略
        if self.policy:
            for agent in Controller.all():
                agent.policy = self.policy

    #重置环境
    def reset(self):
        for node in CpnNode.all():
            node.waiting_queue = []
            node.download_queue = []
            node.compute_queue = []
            #资源占用量
            node.cpu_demand = 0
            node.gpu_demand = 0
            node.bw_demand = 0
            node.disk_demand = 0

        #清空用户
        MyUser._instances = []
        MyUser._object_count = 0
        self.users = []

        #清空任务
        Task._instances = []
        Task._object_count = 0

        #清空任务列表
        for agent in Controller.all():
            agent.schedule_services = []
            agent.task_count = 0
            agent.unsuccess_count = 0

        for agent in CpnRouter.all():
            agent.services = []

        self.schedule.steps=0
        self.schedule.time=0
        # 每次重新迭代时需要将running重置为True
        self.running = True



    #从json文件中读取仿真参数设置
    @classmethod
    def get_ParamsFromFile(cls,input_file:str)->dict:

        with open(input_file,'r',encoding='utf-8') as file:
            params = json.load(file)
        return params

    def get_R(self):
        R_list = []
        for task in Task.all():
            R_list.append(task.efficiency)
        return R_list

    def get_D(self):
        #cpu负载程度
        cpu_ratio=[]
        gpu_ratio=[]
        bw_ratio=[]
        disk_ratio=[]
        for node in CpnNode.all():
            # cpu_ratio.append(node.cpu_demand / node.cpu)
            gpu_ratio.append(round(node.gpu_demand / node.gpu * 100,2))
            bw_ratio.append(round(node.bw_demand / node.bandwidth * 100,2))
            disk_ratio.append(round(node.disk_demand / node.disk * 100,2))

        # cpu_Jain = get_Jain(cpu_ratio)
        # gpu_V = get_Jain(gpu_ratio)
        # bw_V = get_Jain(bw_ratio)
        # disk_V = get_Jain(disk_ratio)
        #改为方差计算
        gpu_V = get_Variance(gpu_ratio)
        bw_V = get_Variance(bw_ratio)
        disk_V = get_Variance(disk_ratio)
        #归一化
        # max_V = 0.1
        # min_V = 0
        # gpu_V = (gpu_V-min_V) / (max_V-min_V)
        # bw_V = (bw_V-min_V) / (max_V-min_V)
        # disk_V = (disk_V-min_V) / (max_V-min_V)
        D = 0.3333*gpu_V + 0.3333*bw_V + 0.3333*disk_V
        return D


