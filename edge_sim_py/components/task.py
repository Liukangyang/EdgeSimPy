""" Contains service-related functionality."""


# EdgeSimPy components
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
import heapq
from edge_sim_py.task_schedulers import Waiting_Time
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
        demand:dict = {
            "cpu_demand":.0,
            "memory_demand":.0
        },
        max_delay = .0,
        state: int = 0,
        status:str='init',
        router:object=None,
        model:object=None)->object:

       Service.__init__(self,obj_id=obj_id,label= label,cpu_demand=demand["cpu_demand"],memory_demand=demand["memory_demand"],state=state)

       self.total_cpu_demand = self.cpu_demand
       self.trans_sustain_steps = 0 #传输时延
       self.comp_sustain_steps = 0 #计算时延
       self.waiting_sustain_steps = 0 #等待时延
       self.delay = .0 # 总时延
       self.E = .0 # 任务预估能耗
       self.max_delay = max_delay #最大容忍时延
       self.remain_total_delay = 0 #剩余时长
       self.remain_comp_delay = 0 #剩余计算时间
       self.remain_trans_delay = 0 #剩余传输时间
       self.remain_memory_demand = self.memory_demand
       self.status = status

       self.router = router

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
                "cpu_demand": self.cpu_demand,
                "memory_demand": self.memory_demand,
                "max_delay": self.max_delay,
                "delay": self.trans_sustain_steps + self.comp_sustain_steps,
            },
            "relationships": {
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
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "max_delay": round(self.max_delay,2),
            "delay":round(self.trans_sustain_steps+self.comp_sustain_steps,2),
        }
        return metrics

    #计算任务的资源成本
    def get_delay(self):
        return round(self.trans_sustain_steps+self.comp_sustain_steps,2),

    #状态转移
    def step(self):
        if self.status=='init' and  not self.being_provisioned: # 上传到控制器列表
                self.router.services.append(self)
                self.status = 'scheduled'

        if self.status == 'finished': #运行结束
            self.status = 'end'
            self.cpu_demand = 0
            self.memory_demand = 0


    # 任务部署：更新服务器资源并预估时延
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

        # 计算当前预估时延
        self.path,link_delay = self.model.topology._shortest_path(origin=self.router,target=target_server,
                                                                  weight="delay",method="dijkstra",service=self)

        # 传输时延
        self.trans_sustain_steps = self.memory_demand / target_server.bandwidth + link_delay #以GB为单位
        # 计算时延
        self.comp_sustain_steps = self.cpu_demand / (target_server.mips/target_server.cpu) #以KMI为单位
        self.remain_comp_delay = self.comp_sustain_steps
        self.remain_trans_delay = self.trans_sustain_steps
        self.remain_total_delay = self.remain_trans_delay + self.remain_comp_delay
        # TODO：排队时延需要按照并行处理的思路计算
        self.waiting_sustain_steps = Waiting_Time(self,target_server)
        # 任务总时延
        self.delay = self.trans_sustain_steps + self.waiting_sustain_steps + self.comp_sustain_steps

        # Ucpu =  1 if self.cpu_demand /  (target_server.mips/target_server.cpu) >1 else self.cpu_demand /  (target_server.mips/target_server.cpu)

        #预估能耗
        self.E = self.comp_sustain_steps * (target_server.Pactive / target_server.cpu)
        # TODO:判断是否能直接执行
        if len(target_server.exec_tasks) >= target_server.max_tasks:
            target_server.waiting_queue.append(self)
        else:
            heapq.heappush(target_server.exec_tasks,self)

        self.being_provisioned = True

    #获取任务状态
    def get_State(self)->list:
        task_state = []
        metrics = self.collect()
        task_state=[metrics["cpu_demand"],
                    metrics["memory_demand"],
                    metrics["max_delay"]]
        return task_state

    def __lt__(self,other):
        return   self.remain_total_delay<other.remain_total_delay if self.remain_total_delay != other.remain_total_delay \
                  else self.id<other.id

    #统计打印函数
    @classmethod
    def print_Tasks_metric(cls,obj_id:int=0):
        lines = []
        lines.append(
            "| ID | Server | cpu_demand(MIPS) | memory_demand(MB) |  max_delay(s)  |  delay(s) |  E(J)  |")
        lines.append("|----|------|------|-----------|-----------|--------|------|")
        if obj_id == 0:
            for task in cls._instances:
                metrics = task.collect()
                data_row = (
                    f"|  {metrics['Instance ID']} |  "
                    f"{metrics['Server']}  | "
                    f"{metrics['cpu_demand']*1000}  | "
                    f"{metrics['memory_demand']*1000}  | "
                    f"{metrics["max_delay"]}  | "
                    f"{metrics["delay"]} |  "
                    f"{metrics['E']} |  "
                )
                lines.append(data_row)
        else:
            task = cls.find_by_id(cls, obj_id)
            metrics = task.collect()
            data_row = (
                f"|  {metrics['Instance ID']} |  "
                f"{metrics['Server']}  | "
                f"{metrics['cpu_demand'] * 1000}  | "
                f"{metrics['memory_demand'] * 1000}  | "
                f"{metrics["max_delay"]}  | "
                f"{metrics["delay"]} |  "
                f"{metrics['E']} |  "
            )
            lines.append(data_row)

        for line in lines:
            print(line)


