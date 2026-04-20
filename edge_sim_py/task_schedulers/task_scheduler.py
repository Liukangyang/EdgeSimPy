import numpy as np
from edge_sim_py.components import *

#TODO:EFT策略
def EFT(service)->object:
    min_delay=99999999
    min_node=None
    for node in CpnNode.all():
        #计算完成时延
        #传输时间
        trans_delay = service.memory_demand / node.bandwidth

        #等待时间
        waiting_delay = sum([task.comp_sustain_steps for task in service.waiting_queue])

        #计算时间
        comp_delay = service.cpu_demand / node.mips

        total_delay = trans_delay + waiting_delay + comp_delay
        if total_delay < min_delay:
            min_node = node
            min_delay = total_delay
    return min_node


#TODO:EDA策略
def EDA(service)->object:
    return None


#TODO：EES策略
def EFS(service)->object:
    return None
