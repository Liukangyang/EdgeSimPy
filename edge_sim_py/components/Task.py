""" Contains service-related functionality."""
# EdgeSimPy components
from edge_sim_py.components import Service, NetworkSwitch
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.cpn_node import CpnNode
from edge_sim_py.components.cpn_router import CpnRouter
from edge_sim_py.components.network_flow import NetworkFlow

# Mesa modules
from mesa import Agent
import math
# Python libraries
import networkx as nx


class Task( Service):

    Mtu = 1500
    history_instances=[]
    def __init__(self,
        obj_id: int = None,
        label: str = "",
        flops_demand: dict = {"cpu":.0,"gpu":.0},
        cpu_demand: int = 0,
        gpu_demand: int = 0,
        disk_demand: int = 0,
        min_bw_demand: int = 0,
        max_delay: float = 0,
        price_gamma:float = 0,
        state: int = 0,
        area_ID:int = None,cpn_router:object=None)->object:

       Service.__init__(self,obj_id=obj_id,label= label,cpu_demand=cpu_demand,state=state)
       self.gpu_demand = gpu_demand
       self.disk_demand = disk_demand
       self.flops_demand = flops_demand
       self.min_bw_demand = min_bw_demand
       self.bw_demand = 0
       self.max_delay = max_delay
       self.price_gamma = price_gamma
       self.cpn_router = cpn_router

       self.trans_sustain_steps = 0 #传输时延
       self.comp_sustain_steps = 0 #计算时延
       self.resource_cost = .0 #资源花费成本
       self.efficiency = .0 # 任务效用

       self.status = 'init'

    #所属区域
       self.area_ID = area_ID

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "label": self.label,
                "status": self.status,
                "_available": self._available,
                "flops_demand": self.flops_demand,
                "cpu_demand": self.cpu_demand,
                "gpu_demand":self.gpu_demand,
                "disk_demand": self.disk_demand,
                "min_bw_demand": self.min_bw_demand,
                "max_delay": self.max_delay,
                "price_gamma": self.price_gamma,
            },
            "relationships": {
                "cpn_router": {"class":type(self.cpn_router),"id":self.cpn_router.id} if self.cpn_router else None, #src node
                "server": {"class": type(self.server).__name__, "id": self.server.id} if self.server else None, #target service
            },
        }
        return dictionary


    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        last_migration = None

        metrics = {
            "Instance ID": self.id,
            "Available": self._available,
            "Server": self.server.id if self.server else None, #CPN-node
            "Being Provisioned": self.being_provisioned,
            "Last Migration": last_migration,
            "flops_demand": self.flops_demand,
            "cpu_demand": self.cpu_demand,
            "gpu_demand": self.gpu_demand,
            "disk_demand": self.disk_demand,
            "bw_demand": self.bw_demand,
            "max_delay": self.max_delay,
            "price_gamma": self.price_gamma,
        }
        return metrics

    def update(self):
        pass

    def step(self):
        #TODO：将任务与所属区域内的CPN节点相关联:NetworkSwitch修改为新的类
        if self.status=='init' and self.cpn_router is None:
            _cpn_router_instances = CpnRouter.all()
            for router in _cpn_router_instances:
                if router.area_ID == self.area_ID:
                    self.cpn_router = router
                    self.cpn_router.services.append(self)
                    self.status = 'commit'
                    break

        if self.status == 'finished':
            self.status = 'end'
            info = self._to_dict()
            print("task"+info['id'] +"has been finished!")
            print(info)
            self.being_provisioned = False
            self._available = False


    def provision(self, target_server: object):
        """Starts the service's provisioning process. This process comprises both placement and migration. In the former, the
        service is not initially hosted by any server within the infrastructure. In the latter, the service is already being
        hosted by a server and we want to relocate it to another server within the infrastructure.

        Args:
            target_server (object): Target server.
        """
        #1.rectify task's status
        self.status = 'scheduled'
        self.server = target_server
        #2.add task to target server's waiting
        target_server.waiting_queue.append(self)
        #3.occupy target server's resources
        target_server.cpu_demand += self.cpu_demand
        target_server.gpu_demand += self.gpu_demand
        target_server.disk_demand += self.disk_demand
        target_server.bw_demand += self.bw_demand

        #4.compute shortest path
        #TODO：定义_shortest_path函数
        self.path,link_delay = self.model.topology._shortest_path(origin=self.cpn_router,target=target_server,
                                                                  weight="delay",method="dijkstra",service=self)
        #4. compute delay
        pcie_time = self.disk_demand / target_server.pcie_speed
        cpu_time = self.flops_demand['cpu'] / (self.cpu_demand * target_server.cpu_flops)
        gpu_time = self.flops_demand['gpu'] / (self.gpu_demand * target_server.gpu_flops)
        # TODO:self.comp_sustain_steps =  pcie_time + max(cpu_time,gpu_time)-先忽略IO时延
        self.comp_sustain_steps = max(cpu_time, gpu_time)
        #TODO:self.trans_sustain_steps = self.disk_demand / self.bw_demand + (len(self.path)-2) * (self.__class__.Mtu/self.bw_demand + Thop) + \link_delay
        #TODO:先忽略平均每跳处理时延
        self.trans_sustain_steps = self.disk_demand*1e9 / (self.bw_demand*1e9) + (len(self.path)-2) * (self.__class__.Mtu/(self.bw_demand*1e9)) + \
                                   link_delay

        #TODO:资源定价计算和效用计算
        # self.resource_cost =
        total_time = self.trans_sustain_steps + self.comp_sustain_steps
        self.efficiency = math.exp(-( total_time + self.price_gamma * self.resource_cost ))

        self.being_provisioned = True







