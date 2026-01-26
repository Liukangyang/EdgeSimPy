""" Contains predefined-related functionality."""

from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.user import User
from edge_sim_py.components.service import Service
# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx

# 用户步进：实现对访问应用的状态转化，以及访问路径和时延的更新
def User_step(self):
        # Updating user access
        current_step = self.model.schedule.steps
        for app in self.applications:
            last_access = self.access_patterns[str(app.id)].history[-1]
            #将当前需部署应用的服务加入到仿真器服务调度队列当中############
            if app.status == "init" and current_step >= app.start_time:
                for service in app.services:
                    self.model.current_services.append(service)
                app.status = "wait"
            # 遍历应用状态
            elif app.status == "wait":
                    if len([s for s in app.services if s._available]) == len(app.services):
                        #TODO:service的可用性需要在服务传输完成后更新，并计算应用的完整时延
                        app.status = "access"
                        last_access["access_time"] += 1
                        self.set_communication_path(app=app)
                    else:
                        last_access["waiting_time"] += 1
                        self.communication_paths[str(app.id)] = []
                        self._compute_delay(app=app)
            elif app.status == "access": #等待计算
                        last_access["access_time"] += 1
            elif app.status == "finished":
                        app.end_time = current_step  #TODO:结束时间应当为开始时间加上模拟的完成时延

            """
            # Updating user's making requests attribute for the next time step
            if current_step  >= app.start_time and app.status!="over":
                self.making_requests[str(app.id)][str(current_step + 1)] = True
            else:
                self.making_requests[str(app.id)][str(current_step + 1)] = False
            """
     # Re-executing user's mobility model in case no future mobility track is known by the simulator
        if len(self.coordinates_trace) <= self.model.schedule.steps and self.mobility_model!=None:
            self.mobility_model(self)
            
            
#应用步进：实现对应用结束状态的判断
def Application_Step(self):
        if any(service._Service__migrations[-1]["status"]=="finished" for service in self.services):
            self.state = "finished"

#服务步进：实现服务部署/迁移的状态转化
def Service_Step(self):
    if len(self._Service__migrations) > 0 and self._Service__migrations[-1]["end"] == None:
        migration = self._Service__migrations[-1]
        # 获取目标服务器上有没有对应的下载流量
        service_on_download_queue=[
            flow.metadata["service"]
            for flow in migration["target"].download_queue
            if flow.metadata["service"].id==self.id
        ]
        if migration["status"] == "waiting":
            if len(service_on_download_queue) > 0:
                migration["status"] = "pulling_layers"
        
        #流量下载完成
        if migration["status"] == "pulling_layers" and self.finished_flag:
            #迁移：假设服务只从用户产生，不会占用本地服务器资源
            """
            if self.server:
                    self.server.cpu_demand -= self.cpu_demand
                    self.server.gpu_demand -= self.cpu_demand
                    self.server.ssd_demand -= self.ssd_size
                    self.server.memory_demand -= self.memory_demand
                    self.server.bw_demand -= self.bw_demand
            """
            migration["status"] = "finished"
            

        # Incrementing the migration time metadata
        if migration["status"] == "waiting":
                migration["waiting_time"] += 1
        elif migration["status"] == "pulling_layers":
                migration["pulling_layers_time"] += 1
        elif migration["status"] == "migrating_service_state":
                migration["migrating_service_state_time"] += 1
                
        if migration["status"] == "finished" and  not migration["updated"]: #服务已完成
                migration["end"] = self.model.schedule.steps 
                migration["updated"] = True
                
                ##
                if self.server:
                    self.server.services.remove(self)
                    self.server.ongoing_migrations -= 1
                ##
                
                # Updating the service's target server metadata
                self.server = migration["target"]
                self.server.services.append(self)
                self.server.ongoing_migrations -= 1

                # Tagging the service as available once their migrations finish
                self._available = True  #服务可用 
                self.being_provisioned = False
                
                #更新用户访问的路径
                # Changing the routes used to communicate the application that owns the service to its users
                app = self.application
                users = app.users
                for user in users:
                    user.set_communication_path(app)

#服务提供provision
def Service_Provision(self,target_server: object):
        # Telling EdgeSimPy that this service is being provisioned
        self.being_provisioned = True
        # Telling EdgeSimPy the service's current server is now performing a migration. This action is only triggered in case
        # this method is called for performing a migration (i.e., the service is already within the infrastructure)
        if self.server:
            self.server.ongoing_migrations += 1
        
        # 将服务加入到目标服务器等待队列中
        target_server.waiting_queue.append(self)
        
        # Reserving the service demand inside the target server and telling EdgeSimPy that server will receive a service
        target_server.ongoing_migrations += 1
        target_server.cpu_demand += self.cpu_demand
        target_server.gpu_demand += self.gpu_demand
        target_server.disk_demand += self.ssd_size
        target_server.memory_demand += self.memory_demand
        target_server.bw_demand += self.bw_demand   
        # Updating the service's migration status
        self._Service__migrations.append(
            {
                "status": "waiting",
                "origin": self.src, #服务用户最近的节点
                "target": target_server,
                "start": self.model.schedule.steps + 1,
                "end": None,
                "waiting_time": 0,
                "pulling_layers_time": 0,
                "migrating_service_state_time": 0,
                "updated":False,
            }
        )
                    
# 网络流传输
def NetworkFlow_Step(self):
       if self.status == "active":
            # Updating the flow progress according to the available bandwidth
            if not any([bw == None for bw in self.bandwidth.values()]):
                self.data_to_transfer -= min(self.bandwidth.values())

            if self.data_to_transfer <= 0:
                # Updating the completed flow's properties
                self.data_to_transfer = 0

                # Storing the current step as when the flow ended
                self.end = self.model.schedule.steps + 1

                # Updating the flow status to "finished"
                self.status = "finished"

                # Releasing links used by the completed flow
                for i in range(0, len(self.path) - 1):
                    link = self.model.topology[self.path[i]][self.path[i + 1]]
                    link["active_flows"].remove(self)

                # When container layer flows finish: Adds the container layer to its target host
                if self.metadata["type"] == "service":
                    # Removing the flow from its target host's download queue
                    self.target.download_queue.remove(self)

                    # Adding the layer to its target host
                    service = self.metadata["object"]
                    # 
                    #service.server = self.target
                    #self.target.services.append(service)
                    service.finished_flag = True

                # When service state flows finish: change the service migration status
                elif self.metadata["type"] == "service_state":
                    service = self.metadata["object"]
                    service._Service__migrations[-1]["status"] = "finished"   

# 资源池步进
def EdgeServer_Step(self):
    while(self.waiting_queue) > 0 and len(self.download_queue) < self.max_concurrent_layer_downloads:
        unload_service = self.waiting_queue.pop(0)

        #寻找路径
        # 为该服务创建网络流
        flow = NetworkFlow(
                topology=self.model.topology,
                source=unload_service.src,  #服务源节点
                target=self, #目标为该服务器
                start=self.model.schedule.steps + 1,
                path=unload_service.path, #传输路径由服务对象提供，由调度函数在调度时实现路径计算
                data_to_transfer=unload_service.ssd_size,
                metadata={"type": "service", "object": unload_service},
            )
        self.model.initialize_agent(agent=flow)
        #将流量加入到目标服务器的下载队列中
        self.download_queue.append(flow) 

#资源池判断是否有足够的资源
def has_capacity_to_host(self,service:object)-> bool:
        # Calculating the edge server's free resources
        free_cpu = self.cpu - self.cpu_demand
        free_gpu = self.gpu - self.gpu_demand
        free_memory = self.memory - self.memory_demand
        free_disk = self.disk - self.disk_demand
        free_bw = self.bw - self.bw_demand
        free_resources={
            "cpu":free_cpu,
            "gpu":free_gpu,
            "disk":free_disk,
            "memory":free_memory,
            "bw":free_bw,
        }
        
        can_host = all(free_resources[key]>= getattr(service,key+"_demand")for key in self.model.resources_list)
        return can_host


#Simulator步进
def Simulator_Step(self):
    if len(self.current_services)>0:
        self.resource_management_algorithm_parameters["current_services"] = self.current_services
        self.resource_management_algorithm(parameters=self.resource_management_algorithm_parameters)
        self.current_services=[]
    # Activating agents
    self.schedule.step()
    
    self.resource_management_algorithm_parameters["current_step"] = self.schedule.steps + 1


# 自定义调度算法
def My_Schedule(parameters:dict):
    #1.遍历可部署服务列表
    for service in parameters["current_services"]:
        #2.寻找适合的服务器
        for server in EdgeServer.All():
            if server.has_capacity_to_host(service):
                #更新路径
                service.path = nx.shortest_path(
                        G=server.model.topology,
                        source=service.src,
                        target=server.network_switch,
                )
                #部署服务
                service.privsison(target_server = server)
                break




     
        
