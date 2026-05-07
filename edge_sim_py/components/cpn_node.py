""" Contains edge-server-related functionality."""
from edge_sim_py.components import EdgeServer
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py import config
# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx
import typing

import heapq

class CpnNode(EdgeServer):
    """Class that represents an Cpn_node server."""

    # cpn_instances = []
    # cpn_object_count = 0

    def __init__(self,obj_id: int = None,
        label:str=None,
        coordinates: tuple = None,
        model_name: str = "",
        cpu_cores: int = 0,
        gpu_cores: int = 0,
        disk: int = 0,
        bandwidth: int = 0,
        cpu_flops:float = 0,
        gpu_flops:float = 0,
        area_ID : int = None,
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
        EdgeServer.__init__(self,obj_id,coordinates,model_name,cpu_cores,0,disk,power_model)

        #
        self.gpu = gpu_cores
        self.bandwidth = bandwidth

        #cpn-node performance
        self.cpu_flops = cpu_flops
        self.gpu_flops = gpu_flops

        # cpn-node demand
        self.gpu_demand = 0
        self.bw_demand = 0

        # correlation network router
        self.network_gw = None

        # compute queue
        self.compute_queue = []

        #area_ID
        self.area_ID = area_ID

        #各资源利用率
        self.Ucpu = .0
        self.Ugpu = .0
        #带宽利用率
        self.Ubw = .0
        #存储利用率
        self.Udisk = .0

        #累积传输数据量
        self.total_trans_data = .0

        # 执行任务数量
        self.finished_tasks = 0

        self.label = label

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
                "available": self.available,
                "model_name": self.model_name,

                "cpu_flops":self.cpu_flops,
                "gpu_flops":self.gpu_flops,

                "cpu": self.cpu,
                "gpu": self.gpu,
                "disk": self.disk,
                "bandwidth": self.bandwidth,

                "cpu_demand": self.cpu_demand,
                "gpu_demand": self.gpu_demand,
                "disk_demand": self.disk_demand,
                "bandwidth_demand": self.bw_demand,

                "coordinates": self.coordinates,
                "active": self.active,
                "power_model_parameters": self.power_model_parameters,
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

            "CPU": self.cpu,
            "GPU": self.gpu,
            "Disk": self.disk,
            "Bandwidth": self.bandwidth,

            "cpu_flops": self.cpu_flops,
            "gpu_flops": self.gpu_flops,

            "CPU Demand": self.cpu_demand,
            "GPU Demand": self.gpu_demand,
            "Disk Demand": self.disk_demand,
            "Bandwidth Demand": self.bw_demand,

            "resource_ratio":{
                "Ucpu":round(self.Ucpu * 100,2),
                "Ugpu":round(self.Ugpu * 100,2),
                "Udisk":round(self.Udisk * 100,2),
                "Ubw":round(self.Ubw * 100,2)
            },
            #经济影响系数
            "Varea":self.model.params["cost"]["economy_vitality"][self.area_ID-1] / min(self.model.params["cost"]["economy_vitality"]),

            "Services": [service.id for service in self.services],
            "Download Queue": len(self.download_queue),
            "Waiting Queue": len(self.waiting_queue),
            "Computing Queue":len(self.compute_queue),
            "Power Consumption": self.get_power_consumption(),
        }
        return metrics

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
                self.disk_demand += task.remain_disk_demand
                task.remain_disk_demand = 0
                total_delay += task.remain_trans_delay
                task.remain_trans_delay -= T_
                task.remain_total_delay -= T_
                if_comp = True

            else:#同时段内未完成传输
                self.disk_demand += self.bandwidth * T_
                task.remain_disk_demand -= self.bandwidth * T_
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
                    self.disk_demand -= task.disk_demand
                else:  #剩余时间未完成计算
                    trans_delay = T_-total_delay
                    task.cpu_demand -=  self.cpu_flops * T_  #按照浮点量计算
                    task.remain_comp_delay -= T_
                    task.remain_total_delay -=T_

    # 遍历等待队列，超出最大任务数量的剩余任务需要等待，否则直接占用一个核心运行
    def step(self,T):
        """Method that executes the events involving the object at each time step."""

        self.time_intervals = T
        self.total_T += self.time_intervals
        total_delay = 0;self.total_trans_data = 0
        total_trans_delay = 0
        intervals = 0
        #exec按照堆结构排序
        while total_delay < T and len(self.exec_tasks)>0:
                task = heapq.heappop(self.exec_tasks) #剩余计算时间最短的任务
                trans_delay = 0
                if_comp=False
                #先传输，传输完成再进行计算
                if task.remain_trans_delay == 0 :
                    if_comp = True
                elif task.remain_trans_delay <= T-total_delay: # 当前时间间隔内可完成传输任务
                    #完成传输
                    total_delay += task.remain_trans_delay
                    task.remain_total_delay -= task.remain_trans_delay
                    task.remain_trans_delay = 0
                    self.disk_demand += task.remain_disk_demand
                    self.total_trans_data += task.disk_demand
                    task.remain_disk_demand = 0
                    if_comp = True
                else:# 当前时间间隔内未完成传输任务
                    #更新传输数据量
                    self.disk_demand += self.bandwidth * (T-total_delay)
                    task.remain_disk_demand -= self.bandwidth * (T-total_delay)
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
                        task.remain_total_delay = task.remain_comp_delay = 0
                        task.cpu_demand = 0

                    else: #当前时间间隔内无法完成
                        trans_delay = T-total_delay
                        task.cpu_demand -= self.cpu_flops * (T-total_delay)
                        task.remain_total_delay -= (T-total_delay)
                        task.remain_comp_delay -= (T - total_delay)
                        total_delay = T
                #TODO:更新其他任务的剩余时间,包括传输和计算时间
                self.update(T_=total_delay)

                if task.remain_total_delay == 0:
                    self.finished_tasks += 1
                    #释放任务的内存
                    self.disk_demand -= task.disk_demand
                    if len(self.waiting_queue)>0:
                            wait_task = self.waiting_queue[0]
                            if self.has_capacity_to_host(wait_task):
                                heapq.heappush(self.exec_tasks, self.waiting_queue.popleft())
                else:
                    heapq.heappush(self.exec_tasks,task)

        #TODO:时间间隔模拟结束，更新CPU、存储利用率、带宽利用率

        self.Ucpu = len(self.exec_tasks) / self.cpu  # 占用核心比例(每个任务占用一个CPU)
        # self.Ugpu
        self.Udisk= self.disk_demand / self.disk
        self.Ubw = self.total_trans_data / (self.bandwidth * self.total_T)  # total_trans_data和bandwidth均以GB为单位

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
        free_cpu = self.cpu - self.cpu_demand
        free_gpu = self.gpu - self.gpu_demand
        free_disk = self.disk - self.disk_demand
        free_bw = self.bandwidth - self.bw_demand

        # Checking if the host would have resources to host the registry and its (additional) layers
        can_host = free_cpu >= service.cpu_demand and free_gpu >= service.gpu_demand and free_disk >= service.disk_demand \
        and free_bw >= service.min_bw_demand

        return (can_host)


    def _get_task(self):
        return self.services

    #TODO：获取节点状态
    def get_State(self,ori_router=None)->list:
        cpn_state=[]
        metrics = self.collect()
        distance = 0
        if ori_router:
            #计算源节点到目的地的最短路径距离
            path,delay=self.model.topology._shortest_path(origin=ori_router, target=self)
            for i in range(len(path) - 1):
                link = self.model.topology[path[i]][path[i + 1]]
                distance += link["distance"]
        cpn_state = [metrics["GPU"],metrics["Disk"],metrics["Bandwidth"],
                     #资源剩余量
                     metrics["GPU"]-metrics["GPU Demand"], metrics["Disk"]-metrics["Disk Demand"], metrics["Bandwidth"]-metrics["Bandwidth Demand"],
                     metrics["gpu_flops"],
                     metrics["resource_ratio"]["gpu"],metrics["resource_ratio"]["disk"],metrics["resource_ratio"]["bw"],
                     metrics["Varea"],
                     distance
                     ]
        # TODO:考虑归一化
        return cpn_state


    #TODO：CPN节点信息打印
    @classmethod
    def print_Servers_metric(cls,obj_id:int=0):
            lines = []
            lines.append( "| ID | CPU | GPU | Disk | BW |                     ratio(%)                     | d_t | c_t | tasks |")
            lines.append("|----|-----|-----|------|----|--------------------------------------------------|-----|-----|-------|")
            if obj_id == 0:
                for server in cls._instances:
                    metrics = server.collect()
                    data_row = (
                        f"|  {metrics['Instance ID']} | "
                        f"{metrics['CPU']} | "
                        f"{metrics['GPU']} | "
                        f"{metrics['Disk']}  | "
                        f"{metrics['Bandwidth']} | "
                        f"{metrics["resource_ratio"]} | "
                        f"{metrics['Download Queue']} | "
                        f"{metrics['Computing Queue']} | "
                        f"{(metrics['Download Queue']+metrics['Computing Queue'])} |"
                    )
                    lines.append(data_row)
            else:
                server = cls.find_by_id(cls,obj_id)
                metrics = server.collect()
                data_row = (
                    f"| {metrics['Instance ID']} | "
                    f"{metrics['CPU']} | "
                    f"{metrics['GPU']} | "
                    f"{metrics['Disk']} | "
                    f"{metrics['Bandwidth']} | "
                    f"{metrics["resource_ratio"]} | "
                    f"{metrics['Download Queue']} | "
                    f"{metrics['Computing Quque']} |"
                )
                lines.append(data_row)

            for line in lines:
                print(line)





