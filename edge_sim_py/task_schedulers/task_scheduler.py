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
        trans_delay = service.memory_demand*1000/1024 / node.bandwidth + link_delay

        #等待时间
        waiting_delay = sum([task.trans_sustain_steps + task.comp_sustain_steps for task in node.waiting_queue])

        #计算总时间
        comp_delay = service.cpu_demand / node.mips

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
        trans_delay = service.memory_demand*1000/1024 / node.bandwidth + link_delay

        # 等待时间
        waiting_delay = sum([task.trans_sustain_steps + task.comp_sustain_steps for task in node.waiting_queue])

        # 计算总时间
        comp_delay = service.cpu_demand / node.mips

        total_delay = trans_delay + waiting_delay + comp_delay
        # 计算能耗
        E = comp_delay * (node.Ucpu * node.Pactive + node.Pidle)
        product = total_delay * E
        if product < min_product:
            min_node = node
            min_product = product
    return min_node


#EES策略-能耗最小
def EES(service,node_list)->object:
    min_E = 99999999
    min_node = None
    for node in node_list:
        #计算时延
        comp_delay = service.cpu_demand / node.mips
        #计算能耗
        E = comp_delay * (node.Ucpu * node.Pactive + node.Pidle)
        if E < min_E:
            min_node = node
            min_E = E
    return min_node
