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
    for agent in datasets[category]:
        print(agent)
        print()
        
        
simulate = Simulator()
simulate.initialize(input_file="Test/test1_date.json")
datasets = Collect_Components()
printComponent(datasets,"User")
printComponent(datasets,"Application")
printComponent(datasets,"Service")
printComponent(datasets,"EdgeServer")
printComponent(datasets,"BaseStation")
printComponent(datasets,"NetworkSwitch")








