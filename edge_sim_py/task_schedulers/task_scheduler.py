'''
静态调度策略实现
'''

from copy import deepcopy
import heapq


#计算等待时延
def Waiting_Time(service,node)->float:
    total_wait_time = 0
    if len(node.exec_tasks) < node.max_tasks:
        total_wait_time = 0
    elif len(node.waiting_queue)==0:
        total_wait_time = heapq.nsmallest(1,node.exec_tasks)[0].remain_total_delay #剩余最小计算时间
    else: #递推计算
        exec_tasks = deepcopy(node.exec_tasks)
        waiting_queue = deepcopy(node.waiting_queue)
        waiting_queue.append(service)
        candidate_node = deepcopy(node)

        while len(exec_tasks)>0:
            #从执行队列里获取弹出最小的任务
            smallest_task = heapq.heappop(exec_tasks)
            total_wait_time += smallest_task.remain_total_delay
            candidate_node.memory_demand -= smallest_task.memory_demand
            for task in exec_tasks:
                task.remain_total_delay -= smallest_task.remain_total_delay
            curr_task = waiting_queue[0]
            #判断当前节点是否能够部署该任务
            if candidate_node.has_capacity_to_host(curr_task):
                if curr_task.id == service.id:#等待时间已到
                    break
                else:#假设部署
                    curr_task = waiting_queue.popleft()
                    heapq.heappush(exec_tasks, curr_task)
                    candidate_node.memory_demand += curr_task.memory_demand
            else:#不部署
                pass

    return total_wait_time


#EFT策略-时延最小
def EFT(service,node_list)->object:
    min_delay=99999999
    min_node=None
    for node in node_list:
        #链路时延
        link_delay = 0
        if node.id <=16:
            link_delay = 1
        else:link_delay= 5
        #传输时间
        trans_delay = service.disk_demand / service.bw_demand + \
                                   (len(service.path)-2) * (service.__class__.Mtu/(service.bw_demand*1e9)) + \
                                   link_delay

        #等待时间
        waiting_delay = Waiting_Time(service,node)

        #计算总时间
        comp_delay = service.flops_demand['cpu'] / (service.cpu_demand * node.cpu_flops)

        total_delay = trans_delay + waiting_delay + comp_delay
        if total_delay < min_delay and node.has_capacity_to_host(service):
            min_node = node
            min_delay = total_delay
    return min_node

#TODO:ECA策略-时延-成本乘积最小
def ECA(service,node_list)->object:
    min_product = 99999999
    min_node = None
    for node in node_list:
        #链路时延
        link_delay = 0
        if node.id <=16:
            link_delay = 1
        else:link_delay= 5
        #传输时间
        trans_delay = service.disk_demand / service.bw_demand + \
                                   (len(service.path)-2) * (service.__class__.Mtu/(service.bw_demand*1e9)) + \
                                   link_delay

        #等待时间
        waiting_delay = Waiting_Time(service,node)

        #计算总时间
        comp_delay = service.flops_demand['cpu'] / (service.cpu_demand * node.cpu_flops)
        #总时延
        total_delay = trans_delay + waiting_delay + comp_delay

        #成本计算
        #带宽总成本(1s为单位)
        bw_price = service.model.params["cost"]["Pb"][str(service.bw_demand)] / 3600 * trans_delay
        # 跨域则按照距离增加基础价格
        if service.area_ID!=node.area_ID:
            distance = 0
            #获取传输路径的总距离
            for i in range(len(service.path)-1):
                link = service.model.topology[service.path[i]][service.path[i+1]]
                distance += link["distance"]
            #按照距离计费
            scale = round(distance / 100,1)
            bw_price *= (1+0.1*scale)

        cpu_base = service.model.params["cost"]["cpu"]["base_price"]
        Ccpu = service.model.params["cost"]["cpu"]["C"]
        cpu_fbase = service.model.params["cost"]["cpu"]["fbase"]
        cpu_price = cpu_base + Ccpu*service.cpu_demand*((node.cpu_flops-cpu_fbase)/cpu_fbase)

        Gbase = min(service.model.params["cost"]["economy_vitality"])
        Garea = service.model.params["cost"]["economy_vitality"][node.area_ID-1]
        Vloc = Garea / Gbase
        #计算资源成本 (单位时间计算成本*计算时间)
        compute_price = cpu_price * Vloc * comp_delay

        resource_cost = bw_price + compute_price

        if total_delay * resource_cost < min_product:
            min_node = node
            min_product = total_delay * resource_cost
    return min_node

#TODO:ECS策略-成本最小
def ECS(service,node_list)->object:
    min_cost = 99999999
    min_node = None
    for node in node_list:
        #链路时延
        link_delay = 0
        if node.id <=16:
            link_delay = 1
        else:link_delay= 5
        #传输时间
        trans_delay = service.disk_demand / service.bw_demand + \
                                   (len(service.path)-2) * (service.__class__.Mtu/(service.bw_demand*1e9)) + \
                                   link_delay
        #计算总时间
        comp_delay = service.flops_demand['cpu'] / (service.cpu_demand * node.cpu_flops)

        #成本计算
        #带宽总成本(1s为单位)
        bw_price = service.model.params["cost"]["Pb"][str(service.bw_demand)] / 3600 * trans_delay
        # 跨域则按照距离增加基础价格
        if service.area_ID!=node.area_ID:
            distance = 0
            #获取传输路径的总距离
            for i in range(len(service.path)-1):
                link = service.model.topology[service.path[i]][service.path[i+1]]
                distance += link["distance"]
            #按照距离计费
            scale = round(distance / 100,1)
            bw_price *= (1+0.1*scale)

        cpu_base = service.model.params["cost"]["cpu"]["base_price"]
        Ccpu = service.model.params["cost"]["cpu"]["C"]
        cpu_fbase = service.model.params["cost"]["cpu"]["fbase"]
        cpu_price = cpu_base + Ccpu*service.cpu_demand*((node.cpu_flops-cpu_fbase)/cpu_fbase)

        Gbase = min(service.model.params["cost"]["economy_vitality"])
        Garea = service.model.params["cost"]["economy_vitality"][node.area_ID-1]
        Vloc = Garea / Gbase
        #计算资源成本 (单位时间计算成本*计算时间)
        compute_price = cpu_price * Vloc * comp_delay

        resource_cost = bw_price + compute_price

        if resource_cost < min_cost:
            min_node = node
            min_cost = resource_cost
    return min_node
