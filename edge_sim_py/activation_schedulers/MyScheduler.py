""" Contains the EdgeSimPy's default agent activation scheduler."""
# EdgeSimPy components
from edge_sim_py.components import *

# Mesa modules
from mesa.time import BaseScheduler as MesaBaseScheduler

from edge_sim_py.components.Controller import Controller


class MyScheduler(MesaBaseScheduler):
    """Class responsible for scheduling the events that take place at each step of the simulation model."""

    # TODO:统计数据
    def statistics(self):
        # 统计量
        total_count = 0
        unsuccessful_count = 0
        for agent in Controller.all():
            total_count += agent.task_count
            unsuccessful_count += agent.unsuccess_count

        # 打印总任务统计表格
        print("+********************************+")
        print("| 总任务数量     | 未成功任务数量 |")
        print("+********************************+")
        print(f"| {total_count:<14} | {unsuccessful_count:<14} |")
        print("+********************************+\n")

        # 打印节点队列状态表格
        print("+-------------------------------------+")
        print("| 节点ID | 下载队列 | 计算队列 |")
        print("+-------------------------------------+")
        for node in CpnNode.all():
            download_tasks = len(node.download_queue)
            computing_tasks = len(node.compute_queue)
            print(f"| {node.id:<6} | {download_tasks:<8} | {computing_tasks:<8} |")
        print("+-------------------------------------+")



    # 仿真步进
    def step(self):
        #TODO：产生任务

        # 上传任务请求
        for agent in Task.all():
            agent.step()
        # CPN路由器上传到控制器队列中
        for agent in CpnRouter.all():
            agent.step()
        # 控制器进行决策
        for agent in Controller.all():
            agent.step()

        # 算力节点执行任务
        for agent in CpnNode.all():
            agent.step()

        # Advancing simulation
        self.steps += 1
        self.time += 1

        #每5步打印一次统计
        if(self.steps % 5 == 0):
            self.statistics()

