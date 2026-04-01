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
        coordinates: tuple = None,
        model_name: str = "",
        cpu: int = 0,
        gpu: int = 0,
        disk: int = 0,
        bandwidth: int = 0,
        cpu_flops:float = 0,
        gpu_flops:float = 0,
        pcie_speed:float = 0,
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
        EdgeServer.__init__(self,obj_id,coordinates,model_name,cpu,0,disk,power_model)

        #
        self.gpu = gpu
        self.bandwidth = bandwidth

        #cpn-node performance
        self.cpu_flops = cpu_flops
        self.gpu_flops = gpu_flops
        self.pcie_speed = pcie_speed

        # cpn-node demand
        self.gpu_demand = 0
        self.bw_demand = 0

        #TODO :资源定价

        # correlation network router
        self.network_gw = None

        # compute queue
        self.compute_queue = []

        #area_ID
        self.area_ID = area_ID



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
                "pcie_speed": self.pcie_speed,

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
            "Coordinates": self.coordinates,
            "Available": self.available,

            "cpu_flops": self.cpu_flops,
            "gpu_flops": self.gpu_flops,
            "pcie_speed": self.pcie_speed,

            "CPU": self.cpu,
            "GPU": self.gpu,
            "Disk": self.disk,
            "Bandwidth": self.bandwidth,

            "CPU Demand": self.cpu_demand,
            "GPU Demand": self.gpu_demand,
            "Disk Demand": self.disk_demand,
            "Bandwidth Demand": self.bw_demand,

            "resource_ratio":{
                "cpu":round(self.cpu_demand/self.cpu,2),
                "gpu":round(self.gpu_demand/self.gpu,2),
                "disk":round(self.disk_demand/self.disk,2),
                "bw":round(self.bw_demand/self.bandwidth,2)
            },

            "Services": [service.id for service in self.services],
            "Download Queue": len(self.download_queue),
            "Waiting Queue": len(self.waiting_queue),
            "Computing Queue":len(self.compute_queue),
            "Power Consumption": self.get_power_consumption(),
        }
        return metrics

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


    def step(self):
        """Method that executes the events involving the object at each time step."""
        # get services and create networkFlow
        while len(self.waiting_queue) > 0 and (len(self.download_queue) < self.max_concurrent_layer_downloads):
            unload_service = self.waiting_queue.pop(0)

            # update service's status
            if unload_service.status == 'scheduled':
                unload_service.status = "loading"

            # create network flow for current service
            #TODO：修改NetworkFlow属性
            flow = NetworkFlow(
                topology=self.model.topology,
                source=unload_service.cpn_router,  #service src node
                target=self,  # target node->this cpn node
                start=self.model.schedule.steps + 1,
                path=unload_service.path,  # 传输路径由服务对象提供，由provision在调度时实现路径计算
                bw_demand=unload_service.bw_demand,
                data_to_transfer=unload_service.disk_demand,
                metadata={"type": "service", "object": unload_service},
                sustain_steps=self.model.schedule.steps + unload_service.trans_sustain_steps  # 模拟持续步长
            )

            self.model.initialize_agent(agent=flow)
            # add flow to download_queue
            heapq.heappush(self.download_queue,(flow.sustain_steps,flow))
        self.waiting_queue= []
        #更新算力节点上的任务状态
        self.update()

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
        return can_host


    def _get_task(self):
        return self.services

    #指标打印
    @classmethod
    def print_servers_metric(cls,obj_id:int=0):
            lines = []
            lines.append( "| ID | CPU | GPU | Disk | BW |                     ratio                        | d_t | c_t | tasks |")
            lines.append("|----|-----|-----|------|----|--------------------------------------------------|----|----|----|")
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





