# EdgeSimPy components
from edge_sim_py import Simulator
from edge_sim_py.activation_schedulers.my_scheduler import MyScheduler
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers import *
# Mesa modules
from mesa import Model,Agent

# Python libraries
from typing import Callable
import numpy as np
import json

from collections import deque

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

        #预计最大任务数量
        self.max_tasks = self.params["max_tasks"]
        #部署策略
        self.policy = self.params["policy"]
        #最大步进次数
        self.max_steps = self.params["max_steps"]

        self.total_delay=0
        self.total_E=0
        self.success_ratio=0
        self.max_delay = 0


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
        # lines = []
        #
        # # 分隔标识（每步开始前添加，避免首行空分隔）
        # if self.schedule.steps > 0:
        #     lines.append("\n" + "=" * 100)
        #
        # # 当前步数
        # step_line = f" Step: {self.schedule.steps}"
        # lines.append(step_line)
        # for line in lines:
        #     print(line)
        #
        # --- Servers 部分 ---
        # print("Cpn-Nodes:")
        # CpnNode.print_Servers_metric()
        #
        # # --- 累积任务数 ---
        # MyScheduler.statistics()

        # --- Task部分 ---
        # print("Tasks:")
        # Task.print_Tasks_metric()

        # ----指标统计-----
        # 计算所有任务累积总时延
        self.total_delay = 0
        self.total_E = 0
        for task in Task.all():
            self.total_delay += task.delay
            self.total_E += task.E
        # # #计算系统累计能耗
        # for node in CpnNode.all():
        #     self.total_E += node.total_E

        # print(f"Total delay(s): {self.total_delay}")
        # print(f"Avg delay(s): {self.total_delay/(MyScheduler.total_count-MyScheduler.unsuccess_count)}")
        # print(f"Total E(J):{self.total_E}")
        # print(f"Avg E(J):{self.total_E/(MyScheduler.total_count-MyScheduler.unsuccess_count)}")

        #计算时延满足比例
        self.success_ratio = 0
        for task in Task.all():
            if task.being_provisioned and task.delay <= task.max_delay:
                self.success_ratio += 1/ len(Task.all())

        #统计所有任务中的最大完成时延
        self.max_delay = np.max([task.delay for task in Task.all()])
        # print(f"Success ratio(%): {self.success_ratio*100}%")

    #初始随机生成用户
    def initialize_Users(self):
        for i in range(self.params["user"]["user_nums"]):
            user = MyUser(lambda_rate=self.params["user"]["lambda_rate"],generate_mode=0,model=self)
            self.users.append(user)


    #初始化
    def setUp(self,input_file: str)->None:
        self.initialize(input_file=input_file) # 初始化拓扑
        # TODO：初始化服务器的参数
        self.initialize_Servers()
        #设置控制器策略
        if self.policy:
            for agent in Controller.all():
                agent.policy = self.policy

    #初始化服务器参数
    def initialize_Servers(self):
        label=["Dell R740", "IBM Dx360 M2", "FUJTU TX1320 M3", "Hewlett DL385 G5", "Hewlett ML110 G4"]
        frequency=[2.7, 2.933, 3.50, 2.3, 1.86]  # 单位Ghz
        Cores=[16, 16, 4, 8, 2]
        MIPS=[604.8, 187.712, 56, 55.2, 14.88]  # 单位KMIPS
        RAM=[64, 48, 8, 16, 16]  # 单位GB
        Bandwidth=[1.5, 1, 1, 1, 0.1]  # 单位GB
        Pactive=[43.2, 47.5, 5.1, 29.9, 11.7]
        Pidle=[50, 116, 9, 178, 86]
        type = [1, 2, 3, 4, 5]
        index=None
        for i in range(1,len(CpnNode.all())+1):
            if i<=16: #边缘服务器
                index = np.random.choice([2,3,4])
            else: # 云服务器
                index = np.random.choice([0,1])

            CpnNode.all()[i-1].label  = label[index]
            CpnNode.all()[i - 1].type = type[index]
            CpnNode.all()[i-1].cpu = Cores[index]
            CpnNode.all()[i-1].max_tasks = Cores[index]
            CpnNode.all()[i-1].cpu_frequency = frequency[index]
            CpnNode.all()[i-1].mips = MIPS[index]
            CpnNode.all()[i-1].memory = RAM[index]
            CpnNode.all()[i-1].bandwidth = Bandwidth[index]
            CpnNode.all()[i - 1].Pactive = Pactive[index]
            CpnNode.all()[i - 1].Pidle = Pidle[index]

    #重置环境
    def reset(self):
        for node in CpnNode.all():
            node.waiting_queue = deque()
            node.exec_tasks = []
            #资源占用量
            node.cpu_demand = 0
            node.memory_demand = 0
            node.total_E = 0
            node.current_E = 0
            node.Ucpu = 0
            node.Ubw = 0
            node.Umemory =0

        #清空用户
        # MyUser._instances = []
        # MyUser._object_count = 0
        # self.users = []
        for user in MyUser.all():
            user.task_count = 0
            user.last_task_step = user.time_intervals = 0

        #清空任务
        Task._instances = []
        Task._object_count = 0

        #清空任务列表
        for agent in Controller.all():
            agent.schedule_services = []
            agent.task_count = 0
            agent.unsuccess_count = 0

        for agent in CpnRouter.all():
            agent.services=[]

        self.schedule.steps=0
        self.schedule.time=0

        self.total_delay=0
        self.total_E=0
        self.success_ratio=0
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


