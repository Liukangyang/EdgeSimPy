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

SUPPORTED_TIME_UNITS = ["seconds", "microseconds", "milliseconds", "minutes"]

class MySimulator(Simulator):
    def __init__(self,
        stopping_criterion: Callable = None,  # 停止标准
        tick_duration: int = 1,
        tick_unit: str = "seconds",
        obj_id: int = None,
        scheduler: Callable = DefaultScheduler,  #调度器
        dump_interval: int = 100,
        max_tasks:int=0):
        Simulator.__init__(self,stopping_criterion=stopping_criterion,
                           tick_duration=tick_duration,tick_unit=tick_unit,
                           obj_id=obj_id, scheduler=scheduler,dump_interval=dump_interval)

        #预计最大任务数量
        self.max_tasks = max_tasks
        if self.stopping_criterion == None:
            self.stopping_criterion = lambda:  ( all(task.status=='end' for task in Task.all())
                                                    and self.schedule.total_count >= self.max_tasks)




    def run_model(self):
        """Executes the simulation."""
        if self.stopping_criterion == None:
            raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

        while self.running:
            # Calls the method that advances the simulation time
            self.step()

            # Calls the method that collects monitoring data about the agents
            if self.schedule.steps % 5 == 0:
                self.monitor()
            # Checks if the simulation should end according to the stop condition
            self.running = False if self.stopping_criterion(self) else True


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
        CpnNode.print_servers_metric()

        # --- 累积任务数 ---
        MyScheduler.statistics()
