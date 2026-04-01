""" Contains predefined-related functionality."""

from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.cpn_node import CpnNode
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.cpn_router import CpnRouter
from edge_sim_py.components.service import Service
from edge_sim_py.components.Task import Task
# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx
import numpy as np
import random

import pprint
from datetime import datetime
import json

# 替换Simulation函数

# 仿真步进
def Simulator_Step(self):
    self.schedule.step()

# 结果统计输出
def Simulator_result_monitor(self,
    output_file: str = "simulation_log.txt",
    ):
    # ===== 1. 构建格式化内容 =====
    lines = []

    # 分隔标识（每步开始前添加，避免首行空分隔）
    if output_file  and self.schedule.steps > 0:
        lines.append("\n" + "=" * 100)

    # 当前步数
    step_line = f" Step: {self.schedule.steps}"
    lines.append(step_line)
    for line in lines:
        print(line)

    # --- Servers 部分 ---
    print("Cpn-Nodes:")

    CpnNode.print_servers_metric()


# 运行仿真
def Simulator_Run_model(self):
    """Executes the simulation."""
    if self.stopping_criterion == None:
        raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

    while self.running:
        # Calls the method that advances the simulation time
        self.step()

        # Calls the method that collects monitoring data about the agents
        self.monitor()
        # Checks if the simulation should end according to the stop condition
        self.running = False if self.stopping_criterion(self) else True



