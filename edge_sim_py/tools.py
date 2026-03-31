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
    print_to_console: bool = False):
    # ===== 1. 构建格式化内容 =====
    lines = []

    # 分隔标识（每步开始前添加，避免首行空分隔）
    if output_file  and self.schedule.steps > 0:
        lines.append("\n" + "=" * 50)

    # 当前步数
    step_line = f" Step: {self.schedule.steps}"
    lines.append(step_line)
    if print_to_console:
            print(step_line)


    # --- Servers 部分 ---
    lines.append("Cpn-Nodes")
    if print_to_console:
        print(" Cpn-Nodes")

    server_summaries = []
    RESOURCE_KEYS = ['cpu', 'gpu', 'disk', 'bw']
    for server in CpnNode.all():
        metrics = server.collect()
        formatted = pprint.pformat(metrics, indent=2, width=100, sort_dicts=False)
        lines.append(formatted + "\n")


        sid = metrics.get('Instance ID', 'N/A')
        res_ratio = metrics.get('resource_ratio', {})
            # 安全提取并格式化所有资源比例（缺失值显示为0.0%）
        ratios = []
        for key in RESOURCE_KEYS:
            val = res_ratio.get(key)
            try:
                pct = float(val) if val is not None else 0.0
                ratios.append(f"{pct:.1f}%")
            except (TypeError, ValueError):
                ratios.append("ERR")
        services_str = ', '.join(str(s) for s in metrics.get('Services', [])) or "None"
        server_summaries.append([sid] + ratios + [services_str])

        if print_to_console:
            print(formatted)
            print()

    # ===== 2. 添加Markdown摘要（显著提升可读性）=====
    if server_summaries:
        lines.append("\n" + "=" * 50)

        # Servers 资源表（完整五资源）
        if server_summaries:
            lines.append("** Server Resource Utilization**")
            lines.append("| ID | CPU | GPU | Disk | Memory | BW | Hosted Services |")
            lines.append("|:--:|:---:|:---:|:----:|:------:|:--:|:----------------|")
            for row in server_summaries:
                # row: [id, cpu, gpu, disk, memory, bw, services]
                lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |")

    lines.append("=" * 60 + "\n")

    # ===== 3. 输出到控制台 & 文件 =====
    full_content = "\n".join(lines)

    # if print_to_console:
    print(full_content, end="")

    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            if print_to_console:
                print(f" Results appended to: {output_file}")
        except Exception as e:
            if print_to_console:
                print(f" Warning: Failed to write to file: {e}")

    return full_content  # 可选：返回内容供进一步处理


# 运行仿真
def Simulator_Run_model(self):
    """Executes the simulation."""
    if self.stopping_criterion == None:
        raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

    while self.running:
        # Calls the method that advances the simulation time
        self.step()

        # Calls the method that collects monitoring data about the agents
        #self.monitor()
        self.simulator_monitor()
        # Checks if the simulation should end according to the stop condition
        self.running = False if self.stopping_criterion(self) else True



