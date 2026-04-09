""" Contains the EdgeSimPy's default agent activation scheduler."""
# EdgeSimPy components
from edge_sim_py.components import *

# Mesa modules
from mesa.time import BaseScheduler as MesaBaseScheduler

from edge_sim_py.components.Controller import Controller


class MyScheduler(MesaBaseScheduler):
    """Class responsible for scheduling the events that take place at each step of the simulation model."""

    total_count = 0
    unsuccess_count = 0

    @classmethod
    def statistics(cls):
        # 统计量
        for agent in Controller.all():
            MyScheduler.total_count += agent.task_count
            MyScheduler.unsuccess_count += agent.unsuccess_count

        # 打印总任务统计表格
        print("+********************************+")
        print("| 总任务数  | 未成功任务数 |")
        print("+********************************+")
        print(f"| {MyScheduler.total_count:<10} | {MyScheduler.unsuccess_count:<10} |")
        print("+********************************+\n")


    # 仿真步进
    def step(self):

        #由用户生成任务并上传到CPNRouter中
        for user in MyUser.all():
            user.step()
        # for agent in Task.all():
        #     agent.step()
        # CPN路由器上传到控制器队列中
        for router in CpnRouter.all():
            router.step()
        # 控制器进行决策
        for controller in Controller.all():
            controller.step()

        # 算力节点执行任务
        for node in CpnNode.all():
            node.step()

        # Advancing simulation
        self.steps += 1
        self.time += 1

