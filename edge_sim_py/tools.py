""" Contains predefined-related functionality."""

from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.user import User
from edge_sim_py.components.service import Service
from edge_sim_py.components.queue import Queue
from edge_sim_py.components.application import Application
# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx
import numpy as np
import random

import pprint
from datetime import datetime
import json

# 用户步进：实现对访问应用的状态转化，以及访问路径和时延的更新
def User_step(self):
        # Updating user access
        current_step = self.model.schedule.steps
        for app in self.applications:
            last_access = self.access_patterns[str(app.id)].history[-1]
            #将当前需部署应用的服务加入到仿真器服务调度队列当�??############
            if app.status == "init" and current_step >= app.start_time:
                self.communication_paths[str(app.id)] = []
                self._compute_delay(app=app)
                # 将服务加入到调度列表当中
                for service in app.services:
                    self.model.current_services.append(service)
                app.status = "wait"
            # 遍历应用状�?
            elif app.status == "wait":
                    last_access["waiting_time"] += 1
                    #若服务未被调度器处理，则会导致服务丢失
                    for service in app.services:
                       if (service.server == None) and (service not in self.model.current_services): #还未被调度，重新加入到simulator的调度列表中
                           self.model.current_services.append(service)
                                      
            if app.status == "access": #等待计算
                        last_access["access_time"] += 1
            if app.status == "finished":  
                    # 为应用设置访问路径
                    self.set_communication_path(app=app)
                    app.end_time = current_step  #结束时间应当为开始时间加上模拟的完成时延
                    #TODO：释放服务器资源(要避免重复释放资源)
                    for service in app.services:
                        if service.resource_occupy:
                            server = service.server
                            server.cpu_demand -= service.cpu_demand
                            server.gpu_demand -= service.gpu_demand
                            server.disk_demand -= service.disk_demand
                            server.memory_demand -= service.memory_demand
                            server.bw_demand -= service.bw_demand
                            service.resource_occupy = False
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

# 更新用户访问应用的路�?
def User_path(self, app: object, communication_path: list = [])->list:
        """Updates the set of links used during the communication of user and its application.

        Args:
            app (object): User application.
            communication_path (list, optional): User-specified communication path. Defaults to [].

        Returns:
            list: Updated communication path.
        """
        topology = Topology.first()

        # Releasing links used in the past to connect the user with its application
        if app in self.communication_paths:
            path = [[NetworkSwitch.find_by_id(i) for i in p] for p in self.communication_paths[str(app.id)]]
            topology._release_communication_path(communication_path=path, app=app)

        # Defining communication path
        if len(communication_path) > 0:
            self.communication_paths[str(app.id)] = communication_path
        else:
            #没有指定的路�?
            self.communication_paths[str(app.id)] = []

            service_hosts_server = [{"service":service,"server":service.server} for service in app.services if service.server]
            communication_chain = [self.base_station.network_switch] + service_hosts_server

            # Defining a set of links to connect the items in the application's service chain
            for i in range(len(communication_chain) - 1):

                # Defining origin and target nodes
                origin = communication_chain[i]
                target = communication_chain[i + 1]["server"]

                # Finding and storing the best communication path between the origin and target nodes
                if origin == target:
                    path = []
                else:
                    path,delay = self.model.topology._shortest_path(
                        origin = origin,
                        target = target, #target_server
                        weight="delay",
                        method="dijkstra",
                        service = communication_chain[i + 1]["service"]
                        )

                # Adding the best path found to the communication path
                #self.communication_paths[str(app.id)].append([network_switch.id for network_switch in path])
                self.communication_paths[str(app.id)].append([network_switch for network_switch in path])
                # Computing the new demand of chosen links
                path = [p for p in self.communication_paths[str(app.id)]]
                
                # 将应用添加到经过的每跳链路当�?
                topology._allocate_communication_path(communication_path=path, app=app)

        # Computing application's delay
        self._compute_delay(app=app, metric="latency")        
        return self.communication_paths[str(app.id)] 

# 更新用户应用时延
def User_compute_delay(self, app: object, metric: str = "latency")->float:
        """Computes the delay of an application accessed by the user.

        Args:
            metric (str, optional): Delay measure (valid options: 'latency' and 'response time'). Defaults to 'latency'.
            app (object): Application accessed by the user.

        Returns:
            delay (int): User-perceived delay when accessing application "app".
        """
        topology = Topology.first()

        services_available = len([s for s in app.services if s._available])
        if services_available < len(app.services):
            # Defining the delay as infinity if any of the application services is not available
            delay = float("inf")
        else:
            # Initializes the application's delay with the time it takes to communicate its client and his base station
            # first delay
            delay = self.base_station.wireless_delay

            # Adding the communication path delay to the application's delay
            #for path in self.communication_paths[str(app.id)]:
                #delay += topology.calculate_path_delay(path=path)
            # 基于服务累积时延
            for service in [s for s in app.services if s._available]:
                delay += service.delay   #service.delay由服务部署时provision函数计算赋值
            if metric.lower() == "response time":
                # We assume that Response Time = Latency * 2
                delay = delay * 2

        # Updating application delay inside user's 'applications' attribute
        self.delays[str(app.id)] = delay

        return delay

# 应用步进：实现对应用结束状态的判断
def Application_Step(self):
        if any(service._available == True for service in self.services):
            self.status = "finished"

# 服务步进：实现服务部�??/迁移的状态转�??
def Service_Step(self):
    if len(self._Service__migrations) > 0 and self._Service__migrations[-1]["end"] == None:
        migration = self._Service__migrations[-1]
        # 获取目标服务器上有没有对应的下载流量
        service_on_download_queue=[
            flow.metadata["object"]
            for flow in migration["target"].download_queue
            if flow.metadata["type"] == "service" and flow.metadata["object"].id==self.id
        ]
        if migration["status"] == "waiting":
            if len(service_on_download_queue) > 0:
                migration["status"] = "pulling_layers"
        
        #流量下载完成
        if migration["status"] == "pulling_layers" and self.finished_flag:
            #迁移：假设服务只从用户产生，不会占用本地服务器资�??
            """
            if self.server:
                    self.server.cpu_demand -= self.cpu_demand
                    self.server.gpu_demand -= self.cpu_demand
                    self.server.ssd_demand -= self.disk_demand
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
                
        if migration["status"] == "finished" and not migration["updated"]: #服务已完�??
                migration["end"] = self.model.schedule.steps 
                migration["updated"] = True
                
                ##
                #若部署服务时就关联到服务，则此处会发生服务错误地从部署服务器删除
                """
                if self.server:
                    self.server.services.remove(self)
                    self.server.ongoing_migrations -= 1
                """
                ##
                
                # Updating the service's target server metadata
                #self.server = migration["target"]
                #self.server.services.append(self)
                self.server.ongoing_migrations -= 1

                # Tagging the service as available once their migrations finish
                self._available = True  #服务可用 
                self.being_provisioned = False
                
                #更新用户访问的路�??
                # Changing the routes used to communicate the application that owns the service to its users
                """
                app = self.application
                users = app.users
                for user in users:
                    user.set_communication_path(app)
                """

#服务提供provision
def Service_Provision(self,target_server: object):
        # Telling EdgeSimPy that this service is being provisioned
        self.being_provisioned = True
        # Telling EdgeSimPy the service's current server is now performing a migration. This action is only triggered in case
        # this method is called for performing a migration (i.e., the service is already within the infrastructure)
        if self.server:
            self.server.ongoing_migrations += 1
        
        
        # 进行关联
        target_server.services.append(self)
        self.server = target_server
        
        # 计算服务最短路�?
        #源：用户所在出口交换机 目的：目标服务器关联交换�?
        # self.path = self.model.topology._shortest_path(origin=self.src,target=target_server.network_switch, weight="delay",method="dijkstra")
        #源：用户所在出口交换机 目的：目标服务器
        self.path,self.delay = self.model.topology._shortest_path(origin=self.src,target=target_server, weight="delay",method="dijkstra",service=self)
 
        
        # 设定流量可用带宽
        """
        self.path = nx.shortest_path(
            G = self.model.topology,
            source=self.src,
            target = target_server.network_switch,
            weight="delay",
            method="dijkstra",       
        )
        """
        # 将服务加入到目标服务器等待队列中
        target_server.waiting_queue.append(self)

        # Reserving the service demand inside the target server and telling EdgeSimPy that server will receive a service
        target_server.ongoing_migrations += 1
        target_server.cpu_demand += self.cpu_demand
        target_server.gpu_demand += self.gpu_demand
        target_server.disk_demand += self.disk_demand
        target_server.memory_demand += self.memory_demand
        target_server.bw_demand += self.bw_demand   
        self.resource_occupy = True
        
        
        # Updating the service's migration status
        self._Service__migrations.append(
            {
                "status": "waiting",
                "origin": self.src, #服务用户最近的节点
                "target": target_server,
                "start": self.model.schedule.steps,
                "end": None,
                "waiting_time": 0,
                "pulling_layers_time": 0,
                "migrating_service_state_time": 0,
                "updated":False,
            }
        )
             
# 网络流传�??
def NetworkFlow_Step(self):
       if self.status == "active":
            '''
            # Updating the flow progress according to the available bandwidth
            if not any([bw == None for bw in self.bandwidth.values()]):
                # 模拟单步1s的传�? => 后续可将其转化为定时调度事件
                self.data_to_transfer -= min(self.bandwidth.values())
            '''
            if self.sustain_steps > 0:
                 self.sustain_steps -= 1
                 
            if   self.sustain_steps == 0:
                 self.data_to_transfer = 0
                 
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

# 资源池步�??
def EdgeServer_Step(self):
    # 更新资源池带宽统计
    #self.bw_demand = sum([service.bw_demand for service in self.services if not service.finished_flag])
    while len(self.waiting_queue) > 0 and (len(self.download_queue) < self.max_concurrent_layer_downloads):
        unload_service = self.waiting_queue.pop(0)

        # 为该服务创建网络�??
        flow = NetworkFlow(
                topology=self.model.topology,
                source=unload_service.src,  #服务源网关交换机
                target=self, #目标为该服务器
                start=self.model.schedule.steps + 1,
                path=unload_service.path, #传输路径由服务对象提供，由provision在调度时实现路径计�?
                bandwidth_demand=unload_service.bw_demand,
                data_to_transfer=unload_service.disk_demand,
                metadata={"type": "service", "object": unload_service},
                sustain_steps=unload_service.sustain_steps # 模拟持续步长
            )
        # TODO:输出网络流量属性
        log_network_flow(flow = flow)
        
        self.model.initialize_agent(agent=flow)
        #将流量加入到目标服务器的下载队列�??
        self.download_queue.append(flow) 
        #
        unload_service.application.status="access"

# 资源池判断是否有足够的资�??
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

# 交换机步�?
def NetworkSwitch_Step(self):
    pass

# 交换机绑定队列
def addQueue(self,target:object=None,cache_len:int = 0,threshold_len:int=0,
                 qos:int=1,active:bool=True):
        if target==None:
            raise Exception("add queue error:can't add a none object!")

        queue = Queue(model=self.model,cache_len=cache_len,threshold_len=threshold_len,
                      qos = qos,active=active,network_switch=self,target=target)
        if self.model:
            self.model.initialize_agent(agent=queue)

        # 建立关联关系
        self.queue[target] = {}
        self.queue[target][queue.qos]=queue #每个QOS一个队�?

# Simulator步进
def Simulator_Step(self):
    if len(self.current_services)>0:
        self.resource_management_algorithm_parameters["current_services"] = self.current_services
        self.resource_management_algorithm(parameters=self.resource_management_algorithm_parameters)
        self.current_services=[]
    # Activating agents
    self.schedule.step()
    # 迭代步数+1
    self.resource_management_algorithm_parameters["current_step"] = self.schedule.steps

#  Simulator run model
def Simulator_Run_model(self):
    """Executes the simulation."""
    if self.stopping_criterion == None:
        raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

    if self.resource_management_algorithm == None:
        raise Exception("Please assign the 'resource_management_algorithm' attribute before starting the simulation.")

    self.running = True
    while self.running:
        #1.调度器步进
        self.step()
        
        #2. call monitor func
        printResult(Simulator=self,print_to_console=False)
        
        #3. Checks if the simulation should end according to the stop condition
        self.running = False if self.stopping_criterion() else True
        
# 资源匹配度计算#
def __get_match_degree(parameters,service,target_server)->float:
        #TODO：到目标服务器的预估时延计算 
        
        path,delay = Topology.all()[0]._shortest_path(
            origin=service.src,
            target=target_server,
            weight="delay",
            method="dijkstra",
            service = service
        )
        # 时延匹配度
        delay_match_degree = np.exp(-parameters["k1"]*delay)
        # 预估资源负载均衡度（如何获取服务部署资源池的负载均衡度）
        resource_ratio ={
            "cpu": (service.cpu_demand + target_server.cpu_demand) / target_server.cpu,
            "gpu": (service.gpu_demand + target_server.gpu_demand) / target_server.gpu,
            "disk": (service.disk_demand + target_server.disk_demand) / target_server.disk,
            "cpu": (service.memory_demand + target_server.memory_demand) / target_server.memory,
            "cpu": (service.bw_demand + target_server.bw_demand) / target_server.bw, 
        }
        ratio_list = [ratio for key,ratio  in resource_ratio.items()]
        resource_match_degree = np.exp(-parameters["k2"] * np.var(ratio_list))
        # 综合资源匹配度
        match_degree = parameters["alpha"] * delay_match_degree + \
            parameters["beta"] * resource_match_degree
            
        #TODO:待增加路径时延与服务sla时延的比较########
        
        return match_degree

# 自定义调度算法
def My_Schedule(parameters:dict):
    servers = EdgeServer.all()
    # 不同的资源匹配算法
    if parameters["mode"] == 1: #首次适应匹配          
        #1.遍历可部署服务列�??
        for service in parameters["current_services"]:
            #2.寻找适合的服务器
            for server in servers:
                if server.has_capacity_to_host(service):
                    #部署服务
                    service.match_degree = __get_match_degree(parameters,service,server)
                    service.provision(target_server = server)
                    break

    elif parameters["mode"] == 2: #随机匹配
        if len(servers)>0:
            for service in parameters["current_services"]:
                #随机寻找服务器
                select_server = None
                count = 0
                while count<= 10:
                    server = random.choice(servers)
                    if server.has_capacity_to_host(service):
                        select_server = server
                        break
                    count+=1
                if select_server != None:
                    service.match_degree = __get_match_degree(parameters,service,select_server)
                    service.provision(target_server = select_server)

    elif parameters["mode"] == 3: #综合资源匹配度匹配
        #TODO：先按服务顺序遍历，每个服务选取资源匹配度最高的服务器
        for service in parameters["current_services"]:
            select_server = None
            match_degree = .0
            for server in servers:
                if server.has_capacity_to_host(service) :
                    server_degree = __get_match_degree(parameters,service,server)
                    if server_degree > match_degree:
                        select_server = server
                        match_degree = server_degree
            if select_server!=None:
                service.match_degree = match_degree
                service.provision(target_server = select_server)

# 仿真停止函数
def Stop_func()->bool:
    # 所有应用都部署且流转完成
    return all(app.status=="finished" for app in Application.all())


def printResult(
    Simulator: object = None,
    output_file: str = "simulation_log.txt",
    print_to_console: bool = True,
    add_markdown_summary: bool = True
):
    """
    打印并保存模拟结果到文件（格式化+可选Markdown摘要）
    
    Args:
        Simulator: 模拟器对象（含schedule.steps）
        output_file: 输出文件路径（None=仅控制台；默认追加模式）
        print_to_console: 是否同时输出到控制台
        add_markdown_summary: 是否在文件末尾添加Markdown表格摘要（提升可读性）
    """
    # ===== 1. 构建格式化内容 =====
    lines = []
    
    # 分隔标识（每步开始前添加，避免首行空分隔）
    if output_file and Simulator and hasattr(Simulator.schedule, 'steps') and Simulator.schedule.steps > 0:
        lines.append("\n" + "="*50)
    
    # 当前步数
    if Simulator and hasattr(Simulator.schedule, 'steps'):
        step_line = f" Step: {Simulator.schedule.steps} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        lines.append(step_line)
        if print_to_console:
            print(step_line)
    
    # --- Services 部分 ---
    lines.append("\n Services")
    if print_to_console:
        print("\n Services")
    
    service_summaries = []  # 用于Markdown摘要
    for service in Service.all():
        metrics = service.collect()
        # 格式化字典（保持原顺序，缩进清晰）
        formatted = pprint.pformat(metrics, indent=2, width=100, sort_dicts=False)
        lines.append(formatted)
        lines.append("")  # 空行分隔
        
        # 收集摘要数据（用于Markdown表格）
        if add_markdown_summary:
            sid = metrics.get('Instance ID', 'N/A')
            status = " Release" if metrics.get('Available') else " Provisioning"
            server = metrics.get('Server', 'N/A')
            delay = metrics["Last Migration"].get("delay","N/A") if "Last Migration" in metrics else 'N/A'
            match_degree  = metrics["match_degree"]
            service_summaries.append([sid, status, server, f"{delay:.2f}" if isinstance(delay, (int, float)) else delay ,match_degree])
        
        
        if print_to_console:
            print(formatted)
            print()
    
    # --- Servers 部分 ---
    lines.append(" Servers")
    if print_to_console:
        print(" Servers")
    
    
    server_summaries = []
    RESOURCE_KEYS = ['cpu', 'gpu', 'disk', 'memory', 'bw']  # 严格按需顺序
    for server in EdgeServer.all():
        metrics = server.collect()
        formatted = pprint.pformat(metrics, indent=2, width=100, sort_dicts=False)
        lines.append(formatted + "\n")
        
        if add_markdown_summary:
            sid = metrics.get('Instance ID', 'N/A')
            res_ratio = metrics.get('resource_ratio', {})
            # 安全提取并格式化所有资源比例（缺失值显示为0.0%）
            ratios = []
            for key in RESOURCE_KEYS:
                val = res_ratio.get(key)
                try:
                    pct = float(val) if val is not None else 0.0
                    ratios.append(f"{pct:.1f}%")
                except (TypeError, ValueError):
                    ratios.append("ERR")
            services_str = ', '.join(str(s) for s in metrics.get('Services', [])) or "None"
            server_summaries.append([sid] + ratios + [services_str])
        
 
        
        if print_to_console:
            print(formatted)
            print()
    
    # ===== 2. 添加Markdown摘要（显著提升可读性）=====
    if add_markdown_summary and (service_summaries or server_summaries):
        lines.append("\n" + "="*50)
        lines.append(" QUICK SUMMARY (Markdown Table)")
        
        if service_summaries:
            lines.append("\n**Services Status**")
            lines.append("| ID | Status | Server | Delay (s) | Match Degree |")
            lines.append("|----|--------|--------|-----------|--------------|")
            for row in service_summaries:
                lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} ")
            lines.append("")
        
# Servers 资源表（完整五资源）
        if server_summaries:
            lines.append("** Server Resource Utilization**")
            lines.append("| ID | CPU | GPU | Disk | Memory | BW | Hosted Services |")
            lines.append("|:--:|:---:|:---:|:----:|:------:|:--:|:----------------|")
            for row in server_summaries:
                # row: [id, cpu, gpu, disk, memory, bw, services]
                lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |")
    
    lines.append("="*60 + "\n")
    
    # ===== 3. 输出到控制台 & 文件 =====
    full_content = "\n".join(lines)
    
    #if print_to_console:
    print(full_content, end="")
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            if print_to_console:
                print(f" Results appended to: {output_file}")
        except Exception as e:
            if print_to_console:
                print(f" Warning: Failed to write to file: {e}")

    return full_content  # 可选：返回内容供进一步处理   
        
# 记录流量
def log_network_flow(
    flow: object,
    log_file: str = "network_flows.json",
    add_timestamp: bool = True,
    validate: bool = False
) -> bool:
    """
    将 NetworkFlow 对象以 JSON Lines 格式追加到日志文件
    
    Args:
        flow: NetworkFlow 实例（需实现 _to_dict() 方法）
        log_file: 输出文件路径（.jsonl 格式）
        add_timestamp: 是否在每条记录添加写入时间戳（不影响原始数据）
        validate: 是否验证序列化结果（避免损坏日志文件）
    
    Returns:
        bool: 写入成功返回 True，失败返回 False
    """
    try:
        # 1. 获取原始字典（严格调用题目指定方法）
        if not hasattr(flow, '_to_dict') or not callable(getattr(flow, '_to_dict')):
            raise AttributeError("Object missing required '_to_dict()' method")
        data = flow._to_dict()
        data["path"] = [f"{type(p).__name__}_{p.id}" for p in data["path"]]
        # 2. 
        if add_timestamp:
            record = {
                #"_log_timestamp": datetime.now().isoformat(),
                "_log_step": Topology.all()[0].model.schedule.steps,  # 若模拟器提供当前步数
                "flow_data": data
            }
        else:
            record = data
        

        # 4. 原子写入：先写临时行，再追加换行（避免半行损坏）
        # TODO:将record中的path选项改为类名+id
        with open(log_file, 'w', encoding='utf-8') as f:
             json.dump(record, f,ensure_ascii=False, indent=2)
        
        return True
    
    except (TypeError, ValueError) as e:
        print(f"Serialization error for flow ID {getattr(flow, 'id', 'unknown')}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error logging flow: {type(e).__name__}: {e}")
        return False