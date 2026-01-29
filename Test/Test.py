import networkx as nx
import msgpack

    # Importing Matplotlib, Pandas, and NumPy for logs parsing and visualization
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from edge_sim_py import *

#Dispaly components
def Collect_Components()->dict:
    datasets={}
    #User
    datasets[f"{User.__name__}"]=[]
    for user in User.all():
        datasets[f"{user.__class__.__name__}"].append((user._to_dict()))
        
    datasets[f"{Application.__name__}"]=[]
    for app in Application.all():
        datasets[f"{app.__class__.__name__}"].append((app._to_dict()))
        
    datasets[f"{Service.__name__}"]=[]
    for service in Service.all():
        datasets[f"{service.__class__.__name__}"].append((service._to_dict()))
        
    datasets[f"{EdgeServer.__name__}"]=[]
    for server in EdgeServer.all():
        datasets[f"{server.__class__.__name__}"].append((server._to_dict()))
       
    datasets[f"{BaseStation.__name__}"]=[]    
    for station in BaseStation.all():
        datasets[f"{station.__class__.__name__}"].append((station._to_dict()))  
        
    datasets[f"{NetworkSwitch.__name__}"]=[]         
    for switch in NetworkSwitch.all():
        datasets[f"{switch.__class__.__name__}"].append((switch._to_dict()))
        
    datasets[f"{NetworkLink.__name__}"]=[]           
    for link in NetworkLink.all():
        datasets[f"{link.__class__.__name__}"].append((link._to_dict()))  

    return datasets
#

def printComponent(datasets,category:str):
    print(f"{category}:")
    for agent in datasets[category]:
        print(agent)
        print()
    
def printClass(category):
    print(category.__name__)
    #User
    for agent in category.all():
        print(agent._to_dict())
        print()
        
        
        
#2.步进测试
# 先替换各类的步进函数
#User
User.step = tools.User_step
User.set_communication_path = tools.User_path
User._compute_delay = tools.User_compute_delay
#app and service
Application.step = tools.Application_Step
Service.step = tools.Service_Step
Service.provision = tools.Service_Provision
#networkflow
NetworkFlow.step = tools.NetworkFlow_Step
#server
EdgeServer.step = tools.EdgeServer_Step
EdgeServer.has_capacity_to_host = tools.has_capacity_to_host
#simulator
Simulator.step = tools.Simulator_Step
#networkswitch
NetworkSwitch.addQueue = tools.addQueue


#1.导入测试
#networkflow schedule algorithm
simulate = Simulator(
    resource_management_algorithm = My_Schedule,
    network_flow_scheduling_algorithm = flow_share,
    stopping_criterion = Stop_func,
    resource_management_algorithm_parameters= {"mode":3,"k1":0.2,"k2":0.3,"alpha":0.5,"beta":0.5}
)

simulate.initialize(input_file="D:\\Code\\edgesimpy\\EdgeSimPy\\Test\\test1_data.json")
datasets = Collect_Components()

printComponent(datasets,"User")
printComponent(datasets,"Application")
printComponent(datasets,"Service")
printComponent(datasets,"EdgeServer")
printComponent(datasets,"BaseStation")
printComponent(datasets,"NetworkSwitch")


while not simulate.stopping_criterion():
    simulate.schedule.steps+=1
    #1.调度器步进
    simulate.resource_management_algorithm_parameters["current_services"] = simulate.current_services
    simulate.resource_management_algorithm(parameters=simulate.resource_management_algorithm_parameters)
    #print(simulate.current_services)
    #print(simulate.schedule.steps)
    simulate.current_services = []
    #2.网络流步进
    for agent in NetworkFlow.all():
        agent.step()
    #2.服务器步进
    for agent in EdgeServer.all():
        #print(agent.waiting_queue)
        agent.step()
    #3.服务步进
    for agent in Service.all():
        agent.step()      
    #4.应用步进步进
    for agent in Application.all():
        agent.step()     
    #5.用户步进
    for agent in User.all():
        agent.step()      
    #print(User.all()[0].applications[0].status)
    #6.拓扑步进
    for agent in Topology.all():
        agent.step()    
    # 其他
    for agent in NetworkSwitch.all():
        agent.step()
    for agent in NetworkLink.all():
        agent.step()
    # 更新各服务器的资源利用率
    for server in EdgeServer.all():
        server._get_resource_ratio()
    # 每次迭代打印统计量
    tools.printResult2(Simulator=simulate,print_to_console=False)
#TODO：打印统计变量

