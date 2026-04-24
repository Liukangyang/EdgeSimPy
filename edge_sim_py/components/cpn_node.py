""" Contains edge-server-related functionality."""
from edge_sim_py.components import EdgeServer
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx
import typing
from collections import deque

import heapq

class CpnNode(EdgeServer):
    """Class that represents an Cpn_node server."""

    # cpn_instances = []
    # cpn_object_count = 0

    def __init__(self,obj_id: int = None,
        label:str = None,
        coordinates: tuple = None,
        model_name: str = "",
        cpu_cores: int = 0,
        cpu_frequency:float = 0,
        mips:float = 0,
        memory:int = 0,
        bandwidth: int = 0,
        disk: int = 0,
        Pactive: float = 0,
        Pidle:float = 0,
        type:int=0,
        power_model: typing.Callable = None) -> object:
        """Creates an Cpn node object.

        Args:
            obj_id (int, optional): Object identifier.
            coordinates (tuple, optional): 2-tuple that represents the cpn node coordinates.
            model_name (str, optional): Cpn node model name. Defaults to "".
            cpu (int, optional): Cpn node's CPU capacity. Defaults to 0.
            gpu (int, optional): Cpn node's GPU capacity. Defaults to 0.
            disk (int, optional): Cpn node's disk capacity. Defaults to 0.
            bandwidth (int, optional): Cpn node's bandwidth. Defaults to 0.
            cpu_flops (float, optional): Cpn node's CPU flops per cpu. Defaults to 0.
            gpu_flops (float, optional): Cpn node's GPU flops per gpu. Defaults to 0.
            pcie_flops (float, optional): Cpn node's PCIe IO speed. Defaults to 0.
            power_model (typing.Callable, optional): Cpn node power model. Defaults to None.
        Returns:
            object: Created EdgeServer object.
        """
        #EdgeServer’s constructor
        EdgeServer.__init__(self,obj_id,coordinates,model_name,cpu_cores,memory,disk,power_model)

        #服务器类型
        self.type = type
        #不同的类型不同的核心数量，对应不同的最大任务数量
        self.max_tasks = self.cpu
        self.cpu_frequency = cpu_frequency
        self.mips = mips

        self.bandwidth = bandwidth

        self.Pidle = Pidle
        self.Pactive = Pactive

        # correlation network router
        self.network_gw = None

        # compute queue
        self.compute_queue = [] #计算队列

        #CPU利用率
        self.Ucpu = .0
        #带宽利用率
        self.Ubw = .0
        #存储利用率
        self.Umemory = .0
        #累积传输数据量
        self.total_trans_data = .0

        # 执行任务数量
        self.finished_tasks = 0

        self.label = label

        #当前能耗
        self.current_E = 0
        #累积总能耗
        self.total_E = 0
        #当前运行任务
        self.exec_tasks=[]

        #每次更新的时间间隔
        self.time_intervals = 0
        #总计时间
        self.total_T = 0

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "label":self.label,
                "available": self.available,
                "model_name": self.model_name,

                "cpu":self.cpu,
                "cpu_frequency":self.cpu_frequency,
                "MIPS": self.mips,
                "bandwidth": self.bandwidth,
                "memory":self.memory,
                "memory_demand":self.memory_demand,
                # "cpu_demand": self.cpu_demand,
                # "disk_demand": self.disk_demand,
                "Pactive":self.Pactive,
                "Pidle":self.Pidle,
                "Ucpu":self.Ucpu,
                "Ubw":self.Ubw,
                "coordinates": self.coordinates,
                "active": self.active,
                # "power_model_parameters": self.power_model_parameters,
            },
            "relationships": {
                "power_model": self.power_model.__name__ if self.power_model else None,
                "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id}
                if self.base_station
                else None,
                "network_gw": {"class": type(self.network_gw).__name__, "id": self.network_gw.id}
                if self.network_gw
                else None,
                "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
            },
        }
        return dictionary


    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        metrics = {
            "Instance ID": self.id,
            "label": self.label,
            "Coordinates": self.coordinates,
            "Available": self.available,

            "cpu": self.cpu,
            "cpu_frequency": self.cpu_frequency,
            "MIPS": self.mips,
            "bandwidth": self.bandwidth,
            "memory": self.memory,
            "Pactive": self.Pactive,
            "Pidle": self.Pidle,
            "Ucpu":self.Ucpu,
            "Umemory":self.memory,
            "Ubw":self.Ubw,
            "E":self.total_E,
            "Services": [service.id for service in self.services],
            "finish_tasks": self.finished_tasks,
            # "Download Queue": len(self.download_queue),
            "Waiting Queue": len(self.waiting_queue),
            # "Computing Queue":len(self.compute_queue),
            # "Power Consumption": self.get_power_consumption(),
        }
        return metrics

############################
    def update(self,T_):
        if T_<=0:
            return
        for task in self.exec_tasks:
            #先传输
            if_comp = False
            total_delay = 0
            trans_delay = 0
            if task.remain_trans_delay == 0:
                if_comp = True
            elif task.remain_trans_delay <= T_:#同时段内完成传输
                self.memory_demand += task.remain_memory_demand
                task.remain_memory_demand = 0
                total_delay += task.remain_trans_delay
                task.remain_trans_delay -= T_
                task.remain_total_delay -= T_
                if_comp = True

            else:#同时段内未完成传输
                self.memory_demand += self.bandwidth * T_
                task.remain_memory_demand -= self.bandwidth * T_
                task.remain_trans_delay -= T_
                task.remain_total_delay -= T_
                total_delay = T_
                if_comp = False

            if if_comp:
                if task.remain_comp_delay <= T_-total_delay: #剩余时间完成计算
                    trans_delay = task.remain_comp_delay
                    task.remain_comp_delay = 0
                    task.remain_total_delay = 0
                    task.cpu_demand = 0
                    self.memory_demand -= task.memory_demand
                else:  #剩余时间未完成计算
                    trans_delay = T_-total_delay
                    task.cpu_demand -=  self.mips / self.cpu * T_
                    task.remain_comp_delay -= T_
                    task.remain_total_delay -=T_
            # self.Ucpu += trans_delay / T_

    # 遍历等待队列，超出最大任务数量的剩余任务需要等待，否则直接占用一个核心运行
    def step(self,T):
        """Method that executes the events involving the object at each time step."""

        self.time_intervals = T
        self.total_T += self.time_intervals
        total_delay = 0;incre_E=0;self.total_trans_data = 0
        total_trans_delay = 0
        intervals = 0
        #exec按照堆结构排序
        while total_delay < T and len(self.exec_tasks)>0:
                task = heapq.heappop(self.exec_tasks) #剩余计算时间最短的任务
                trans_delay = 0
                if_comp=False
                #TODO:先传输，传输完成再进行计算
                if task.remain_trans_delay == 0 :
                    if_comp = True
                elif task.remain_trans_delay <= T-total_delay: # 当前时间间隔内可完成传输任务
                    #完成传输
                    total_delay += task.remain_trans_delay
                    task.remain_total_delay -= task.remain_trans_delay
                    task.remain_trans_delay = 0
                    self.memory_demand += task.remain_memory_demand
                    self.total_trans_data += task.memory_demand
                    task.remain_memory_demand = 0
                    if_comp = True
                else:# 当前时间间隔内未完成传输任务
                    #更新传输数据量
                    self.memory_demand += self.bandwidth * (T-total_delay)
                    task.remain_memory_demand -= self.bandwidth * (T-total_delay)
                    #更新剩余时间
                    task.remain_total_delay -= (T-total_delay)
                    task.remain_trans_delay -= (T-total_delay)
                    total_delay = T
                    if_comp = False

                #是否可以继续传输
                if if_comp:
                    if task.remain_comp_delay <= T-total_delay:  #当前时间间隔内可完成计算任务
                        trans_delay = task.remain_comp_delay
                        total_delay += task.remain_comp_delay
                        # #TODO:待修改Ucpu
                        # incre_E += task.remain_comp_delay * (self.Ucpu*self.Pactive+self.Pidle)
                        task.remain_total_delay = task.remain_comp_delay = 0
                        task.cpu_demand = 0
                        total_trans_delay
                    else: #当前时间间隔内无法完成
                        trans_delay = T-total_delay
                        task.cpu_demand -= self.mips/self.cpu * (T-total_delay)
                        # incre_E = (T-total_delay) * (self.Ucpu*self.Pactive+self.Pidle)
                        task.remain_total_delay -= (T-total_delay)
                        task.remain_comp_delay -= (T - total_delay)
                        total_delay = T
                #TODO:更新其他任务的剩余时间,包括传输和计算时间
                self.update(T_=total_delay)
                # self.Ucpu += (trans_delay / total_delay if total_delay > 0 else 0)

                if task.remain_total_delay == 0:
                    self.finished_tasks += 1
                    #释放任务的内存
                    self.memory_demand -= task.memory_demand
                    if len(self.waiting_queue)>0:
                            wait_task = self.waiting_queue[0]
                            if self.has_capacity_to_host(wait_task):
                                heapq.heappush(self.exec_tasks, self.waiting_queue.popleft())
                else:
                    heapq.heappush(self.exec_tasks,task)

                #TODO:增加能耗
               #  intervals = total_delay - intervals
               #  incre_E +=  intervals*(self.Ucpu * self.Pactive+self.Pidle)
               # #TODO:更新Ucpu
               #  #1.按照实际占用核心数计算
               #  num = 0
               #  for task in self.exec_tasks:
               #     if task.remain_total_delay > 0:
               #         num+=1
               #  self.Ucpu = num / self.cpu
        #TODO:时间间隔模拟结束，更新CPU、存储利用率、带宽利用率
        self.Umemory = 0
        # for task in self.exec_tasks:
        #     self.Ucpu += (1 if task.cpu_demand > (self.mips / self.cpu) else task.cpu_demand / (self.mips / self.cpu))
        # # 取平均
        # self.Ucpu /= self.cpu
        self.Umemory = self.memory_demand / self.memory

        self.Ubw = self.total_trans_data / (self.bandwidth * self.total_T) #total_trans_data和bandwidth均以GB为单位
        # #更新总能耗
        # self.total_E += incre_E

    def has_capacity_to_host(self, service: object) -> bool:
        """Checks if the cpn node has enough free resources to host a given service.

        Args:
            service (object): Service object that we are trying to host on the edge server.

        Returns:
            can_host (bool): Information of whether the edge server has capacity to host the service or not.
        """
        # Calculating the additional disk demand that would be incurred to the edge server
        # additional_disk_demand = self._get_disk_demand_delta(service=service)

        # Calculating the edge server's free resources
        free_memory = self.memory - self.memory_demand #以GB为单位

        # Checking if the host would have resources to host the registry and its (additional) layers
        can_host = free_memory >= service.remain_memory_demand

        return can_host


    def _get_task(self):
        return self.services

    #获取节点状态
    def get_State(self,service=None)->list:
        cpn_state=[]
        metrics = self.collect()
        cpn_state=[
            metrics['cpu'],
            metrics['memory'],
            metrics['bandwidth'],
            metrics['Ucpu'],
            metrics['Umemory'],
            metrics['Ubw'],
            metrics['MIPS'],
            metrics['Pactive'],
            metrics['Pidle'],
        ]
        # 预估下一个任务的时延
        trans_delay = service.memory_demand / self.bandwidth #与带宽有关
        compute_delay = service.cpu_demand / self.mips  #与性能有关
        waiting_delay = sum([task.comp_sustain_steps for task in self.waiting_queue])  #与等待队列长度有关
        predict_delay = trans_delay + compute_delay + waiting_delay
        cpn_state.append(predict_delay)

        return cpn_state


    #指标打印
    @classmethod
    def print_Servers_metric(cls,obj_id:int=0):
            lines = []
            lines.append( "| ID | CPU | FRE(GHz) | MIPS | Memory(GB) | BW(GB/s) | Pactive(W) | Pidle(W) | tasks |")
            lines.append("|----|-----|-----|-----|-----|-----|------|----|-------|")
            if obj_id == 0:
                for server in cls._instances:
                    metrics = server.collect()
                    data_row = (
                        f"|  {metrics['Instance ID']} | "
                        f"{metrics['cpu']} | "
                        f"{metrics['cpu_frequency']} | "
                        f"{metrics['MIPS']} | "
                        f"{metrics['memory']}  | "
                        f"{metrics['bandwidth']} | "
                        f"{metrics['Pactive']} | "
                        f"{metrics['Pidle']} | "
                        f"{metrics['finish_tasks']} | "
                    )
                    lines.append(data_row)
            else:
                server = cls.find_by_id(cls,obj_id)
                metrics = server.collect()
                data_row = (
                    f"|  {metrics['Instance ID']} | "
                    f"{metrics['cpu']} | "
                    f"{metrics['cpu_frequency']} | "
                    f"{metrics['MIPS']} | "
                    f"{metrics['memory']}  | "
                    f"{metrics['bandwidth']} | "
                    f"{metrics['Pactive']} | "
                    f"{metrics['Pidle']} | "
                    f"{metrics['finish_tasks']} | "
                )
                lines.append(data_row)

            for line in lines:
                print(line)





