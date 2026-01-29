"""
自定义带宽分配算法
每个网络流的的带宽值为服务所需带宽与网络链路上可提供最小带宽间的最小值
"""
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers import *
import numpy as np
def flow_share(topology: object, flows: list):
    #遍历每个流量
    for flow in flows:
        left_bw=[]
        # 获取每个链路上的剩余带宽
        for i in range(len(flow.path)-1):
            link = topology[flow.path[i]][flow.path[i+1]]
            left_bw.append(link["bandwidth_left"])
        left_bw.append(flow.bandwidth_demand)
        #取left_bw和bw_demad中的最小值作为该流量的可用带宽
        bw = np.min(left_bw)
        for i in range(len(flow.path)-1):
            link = topology[flow.path[i]][flow.path[i+1]]
            flow.bandwidth[link["id"]] = bw
            
        flow.current_bandwidth = bw
