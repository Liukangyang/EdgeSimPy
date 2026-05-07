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
from edge_sim_py.task_schedulers import Waiting_Time
import heapq
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
        demand:dict = {
            "cpu_flops": .0, "gpu_flops": .0,
            "cpu":.0,"gpu":.0,"disk":.0,
            "min_bw":.0,"max_delay":.0,
            "price_gamma":.0,
        },
        sla:dict={
            "min_bw":.0,
            "max_delay":.0,
            "price_gamma":.0
        },
        state: int = 0,
        status:str='init',
        task_type:int=None,
        sla_level:int = 1,
        area_ID:int = None,cpn_router:object=None,model:object=None)->object:

       Service.__init__(self,obj_id=obj_id,label= label,cpu_demand=demand["cpu"],state=state)
       self.flops_demand = {
           "cpu":demand["cpu_flops"],
           "gpu":demand["gpu_flops"]
       }
       self.gpu_demand = demand["gpu"]
       self.disk_demand = demand["disk"]
       self.min_bw_demand = sla["min_bw"]
       self.bw_demand = 0
       self.max_delay = sla["max_delay"]
       self.price_gamma = sla["price_gamma"]
       self.cpn_router = cpn_router

       self.trans_sustain_steps = 0 #传输时延
       self.comp_sustain_steps = 0 #计算时延
       self.waiting_sustain_steps = 0 #等待时延
       self.resource_cost = .0 #资源花费成本
       self.delay = .0 # 总时延

       self.remain_total_delay = 0  # 剩余时长
       self.remain_comp_delay = 0  # 剩余计算时间
       self.remain_trans_delay = 0  # 剩余传输时间
       self.remain_memory_demand = self.memory_demand

       self.status = status

       self.task_type = task_type #任务类型
       self.sla_level = sla_level #SLA等级
       self.area_ID = area_ID  #所属区域

       self.model = model


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
                "areaID":self.area_ID,

                "task_type": self.task_type,

                "flops_demand": self.flops_demand,
                "cpu_demand": self.cpu_demand,
                "gpu_demand":self.gpu_demand,
                "disk_demand": self.disk_demand,

                "sla_level": self.sla_level,

                "min_bw_demand": self.min_bw_demand,
                "max_delay": self.max_delay,
                "price_gamma": self.price_gamma,

                "delay": self.trans_sustain_steps + self.comp_sustain_steps,
                "resource_cost": self.resource_cost,
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
            "areaID":self.area_ID,

            "task_type": self.task_type,

            "flops_demand": self.flops_demand,
            "cpu_demand": self.cpu_demand,
            "gpu_demand": self.gpu_demand,
            "disk_demand": self.disk_demand,

            "sla_level": self.sla_level,

            "min_bw_demand": self.min_bw_demand,
            "max_delay": round(self.max_delay,2),
            "price_gamma": self.price_gamma,

            "delay":round(self.trans_sustain_steps+self.comp_sustain_steps,2),
            "resource_cost":round(self.resource_cost,2),
        }
        return metrics

    #计算任务的资源成本
    def get_ResourceCost(self):
        return self.resource_cost

    def step(self):
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
        self.path,link_delay = self.model.topology._shortest_path(origin=self.cpn_router,target=target_server,
                                                                  weight="delay",method="dijkstra",service=self)
        #4. compute delay
        cpu_time = self.flops_demand['cpu'] / (self.cpu_demand * target_server.cpu_flops)
        # gpu_time = self.flops_demand['gpu'] / (self.gpu_demand * target_server.gpu_flops)
        self.comp_sustain_steps = cpu_time
        self.remain_trans_delay = self.comp_sustain_steps
        #link_delay包括了每跳转发排毒时延
        self.trans_sustain_steps = self.disk_demand / self.bw_demand + \
                                   (len(self.path)-2) * (self.__class__.Mtu/(self.bw_demand*1e9)) + \
                                   link_delay
        self.remain_trans_delay = self.trans_sustain_steps
        self.waiting_sustain_steps = Waiting_Time(self,target_server)
        self.delay = self.waiting_sustain_steps + self.trans_sustain_steps +  self.comp_sustain_steps

        #TODO:带宽成本:跨域距离每增加100KM，价格增加10%
        #带宽总成本(1s为单位)
        bw_price = self.model.params["cost"]["Pb"][str(self.bw_demand)] / 3600 * self.trans_sustain_steps
        # 跨域则按照距离增加基础价格
        if self.area_ID!=target_server.area_ID:
            distance = 0
            #获取传输路径的总距离
            for i in range(len(self.path)-1):
                link = self.model.topology[self.path[i]][self.path[i+1]]
                distance += link["distance"]
            #按照距离计费
            scale = round(distance / 100,1)
            bw_price *= (1+0.1*scale)

        #cpu成本
        cpu_base = self.model.params["cost"]["cpu"]["base_price"]
        Ccpu = self.model.params["cost"]["cpu"]["C"]
        cpu_fbase = self.model.params["cost"]["cpu"]["fbase"]
        cpu_price = cpu_base + Ccpu*self.cpu_demand*((target_server.cpu_flops-cpu_fbase)/cpu_fbase)

        #gpu成本
        # gpu_base = self.model.params["cost"]["gpu"]["base_price"]
        # Cgpu = self.model.params["cost"]["gpu"]["C"]
        # gpu_fbase = self.model.params["cost"]["gpu"]["fbase"]
        # gpu_price = gpu_base + Cgpu*self.gpu_demand*((target_server.gpu_flops-gpu_fbase)/gpu_fbase)

        # 服务器电力成本
        Gbase = min(self.model.params["cost"]["economy_vitality"])
        Garea = self.model.params["cost"]["economy_vitality"][target_server.area_ID-1]
        Vloc = Garea / Gbase
        #计算资源成本 (单位时间计算成本*计算时间)
        # compute_price =  ((cpu_price + gpu_price) * Vloc) * self.comp_sustain_steps
        compute_price = cpu_price * Vloc * self.comp_sustain_steps

        #总资源成本
        self.resource_cost = bw_price + compute_price

        # TODO:判断是否能直接执行
        if len(target_server.exec_tasks) >= target_server.max_tasks:
            target_server.waiting_queue.append(self)
        else:
            heapq.heappush(target_server.exec_tasks,self)
        self.being_provisioned = True

    #TODO:获取任务状态
    def get_State(self)->list:
        task_state = []
        metrics = self.collect()
        task_state=[metrics["flops_demand"]["cpu"],\
                    metrics["cpu_demand"],metrics["disk_demand"],\
                    metrics["max_delay"]]
        #TODO:考虑归一化
        return task_state

    def __lt__(self,other):
        return self.id < other.id

    #TODO:统计打印函数
    @classmethod
    def print_Tasks_metric(cls,obj_id:int=0):
        lines = []
        lines.append(
            "| ID | Area | Server | task_type | sla_level |  max_delay  |  delay |  cost  |     efficiency     |")
        lines.append("|----|------|--------|-----------|-----------|-------------|--------|--------|--------------------|")
        if obj_id == 0:
            for task in cls._instances:
                metrics = task.collect()
                data_row = (
                    f"|  {metrics['Instance ID']} |  "
                    f"{metrics['areaID']}   |   "
                     f"{metrics['Server']}    |     "
                    f"{metrics['task_type']}     |     "
                    f"{metrics['sla_level']}     |     "
                    f"{metrics["max_delay"]}    |  "
                    f"{metrics["delay"]} |  "
                    f"{metrics['resource_cost']} |   "
                    f"{metrics['efficiency']} |"
                )
                lines.append(data_row)
        else:
            task = cls.find_by_id(cls, obj_id)
            metrics = task.collect()
            data_row = (
                f"| {metrics['Instance ID']} | "
                f"{metrics['areaID']} | "
                f"{metrics['Server']} | "
                f"{metrics['task_type']}  | "
                f"{metrics['sla_level']} | "
                f"{metrics["delay"]} | "
                f"{metrics['resource_cost']} |"
                f"{metrics['efficiency']} | "
            )
            lines.append(data_row)

        for line in lines:
            print(line)


