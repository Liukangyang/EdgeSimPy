from copy import deepcopy
import heapq

def Waiting_Time(service,node)->object:
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
        #计算完成时延
        #链路时延
        link_delay = 0
        if node.id <=16:
            link_delay = 1
        else:link_delay= 10
        #传输时间
        trans_delay = service.memory_demand / node.bandwidth + link_delay

        #等待时间
        waiting_delay = Waiting_Time(service,node)

        #计算总时间
        comp_delay = service.cpu_demand / (node.mips/node.cpu)

        total_delay = trans_delay + waiting_delay + comp_delay
        if total_delay < min_delay and node.has_capacity_to_host(service):
            min_node = node
            min_delay = total_delay
    return min_node

#EDA策略-时延-能耗乘积最小
def EDA(service,node_list)->object:
    min_product = 99999999
    min_node = None
    for node in node_list:
        # 计算完成时延
        #链路时延
        link_delay = 0
        if node.id <=16:
            link_delay = 1
        else:link_delay= 10
        # 传输时间
        trans_delay = service.memory_demand / node.bandwidth + link_delay

        # 等待时间
        waiting_delay = Waiting_Time(service,node)

        # 计算总时间
        comp_delay = service.cpu_demand / (node.mips/node.cpu)

        total_delay = trans_delay + waiting_delay + comp_delay
        # 计算能耗
        # Ucpu = comp_delay / (comp_delay + trans_delay)
        # Ucpu = 1 if service.cpu_demand / (node.mips/node.cpu) > 1 else service.cpu_demand / (node.mips/node.cpu)
        # Ucpu = 1 if len(node.exec_tasks)>=node.max_tasks else len(node.exec_tasks)/node.max_tasks
        # E = (comp_delay+waiting_delay) * (Ucpu * node.Pactive + node.Pidle)
        E = (comp_delay) * (node.Pactive / node.cpu)
        product = total_delay * E
        if product < min_product and node.has_capacity_to_host(service):
            min_node = node
            min_product = product
    return min_node

#EES策略-能耗最小
def EES(service,node_list)->object:
    min_E = 99999999
    min_node = None
    for node in node_list:
        #计算时延
        comp_delay = service.cpu_demand / (node.mips/node.cpu)
        # 等待时间
        waiting_delay = Waiting_Time(service,node)
        # waiting_delay = Waiting_Time(service,node)
        #计算能耗
        # Ucpu = node.Ucpu + service.cpu_demand / (node.mips/node.cpu)/node.cpu
        # Ucpu =  1 if service.cpu_demand /  (node.mips/node.cpu) >1 else service.cpu_demand /  (node.mips/node.cpu)
        Ucpu = 1 if len(node.exec_tasks)>=node.max_tasks else len(node.exec_tasks)/node.max_tasks
        # E = (comp_delay+waiting_delay) * (Ucpu * node.Pactive + node.Pidle)
        E = (comp_delay) * (node.Pactive / node.cpu)
        if E < min_E and node.has_capacity_to_host(service):
            min_node = node
            min_E = E
    return min_node
