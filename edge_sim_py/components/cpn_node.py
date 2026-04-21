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

        self.cpu_frequency = cpu_frequency
        self.mips = mips

        self.bandwidth = bandwidth

        self.Pidle = Pidle
        self.Pactive = Pactive

        # correlation network router
        self.network_gw = None

        # compute queue
        self.compute_queue = [] #计算队列

        #能耗
        self.total_E = 0
        #CPU利用率
        self.Ucpu = .0
        #带宽利用率
        self.Ubw = .0

        # 执行任务数量
        self.finished_tasks = 0

        self.label = label

        #当前能耗
        self.current_E = 0
        #累积总能耗
        self.total_E = 0


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
            # "cpu_demand": self.cpu_demand,
            # "disk_demand": self.disk_demand,
            "Ucpu": self.Ucpu,
            "Ubw": self.Ubw,
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
    def update(self):
        #1.从download_queue中提取出当前已经传输完成的流量,将对应服务再放入到计算队列中(按照计算时间降序)
        while(len(self.download_queue)>0):
            trans_sustain_steps,flow=heapq.heappop(self.download_queue)
            if trans_sustain_steps<=self.model.schedule.steps:
                if flow.metadata['type'] == 'service':
                    service = flow.metadata['object']
                    service.status = 'computing'
                    heapq.heappush(self.compute_queue,(self.model.schedule.steps+service.comp_sustain_steps,service))
            else:#重新插入下载队列中
                heapq.heappush(self.download_queue,(trans_sustain_steps,flow))
                break

        #2.从compute_queue中提取出已完成计算的任务，并释放相应资源
        while(len(self.compute_queue)>0):
             comp_sustain_steps,service = heapq.heappop(self.compute_queue)
             if comp_sustain_steps <= self.model.schedule.steps:
                 service.status = 'finished'
                # clear resources
                 self.cpu_demand -= service.cpu_demand
                 self.gpu_demand -= service.gpu_demand
                 self.disk_demand -= service.disk_demand
                 self.bw_demand -= service.bw_demand
                #直接执行结束任务的step
                 service.step()
             else:#重新插入计算队列中
                 heapq.heappush(self.compute_queue,(comp_sustain_steps,service))
                 break

    # 遍历等待队列，依次执行任务，可执行总数限制在1s内，每执行完成一个任务将释放相应的ram资源
    def step(self):
        """Method that executes the events involving the object at each time step."""
        # get services and create networkFlow
        total_comp_delay=.0
        total_trans_data=.0
        total_delay = .0

        #依次执行当前步内等待队列内的任务，并计算总时延和总传输数据量
        while len(self.waiting_queue) > 0 and total_delay<1:
            task = self.waiting_queue[0]
            # 执行任务
            if total_delay + task.trans_sustain_steps > 60:  # 单位分钟/60s
                task.trans_sustain_steps -= (60-total_delay) # 更新传输时延
                total_delay = 60
            else: #传输完成
                if task.trans_sustain_steps != 0:
                    self.memory_demand += task.memory_demand *1000/1024
                    total_trans_data += self.memory_demand *1000/1024
                total_delay += task.trans_sustain_steps
                task.trans_sustain_steps = 0
                #执行计算
                if total_delay + task.comp_sustain_steps > 60:
                    task.comp_sustain_steps -= (60-total_delay)
                    total_comp_delay += 60-total_delay
                    total_delay = 60
                else: # 计算完成，执行完任务出队，并释放ram资源
                    total_delay += task.comp_sustain_steps
                    total_comp_delay += task.comp_sustain_steps
                    task.status = 'finished'
                    task.step()
                    self.waiting_queue.popleft()
                    self.memory_demand -= task.memory_demand * 1000 / 1024
                    self.finished_tasks += 1 #完成任务+1

        #计算CPU利用率
        self.Ucpu = total_comp_delay / 60
        #TODO:带宽利用率
        self.Ubw = 1 if total_trans_data >= self.bandwidth else total_trans_data / self.bandwidth
        #单次步进内产生的能耗
        self.current_E = total_comp_delay*(self.Ucpu*self.Pactive+self.Pidle)
        # 累积总能耗
        self.total_E += self.current_E

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
        free_memory = self.memory - self.memory_demand*1000/1024 #以GB为单位

        # Checking if the host would have resources to host the registry and its (additional) layers
        can_host = free_memory >= service.memory_demand

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
            metrics['Ubw'],
            metrics['cpu_frequency'],
            metrics['Pactive'],
            metrics['Pidle'],
        ]
        #预估下一个任务的时延
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





