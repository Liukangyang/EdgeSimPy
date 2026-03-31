import unittest
from edge_sim_py.simulator import Simulator
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers.MyScheduler import MyScheduler


class SimulationTestCase(unittest.TestCase):
    # Dispaly components
    def Collect_Components(self) -> dict:
        datasets = {}

        # Task
        datasets[f"{Task.__name__}"] = []
        for service in Task.all():
            datasets[f"{service.__class__.__name__}"].append((service._to_dict()))

        datasets[f"{CpnNode.__name__}"] = []
        for server in CpnNode.all():
            # print(server.__class__.__name__)
            datasets[f"{server.__class__.__name__}"].append((server._to_dict()))


        datasets[f"{NetworkSwitch.__name__}"] = []
        for switch in NetworkSwitch.all():
            # print(switch.__class__.__name__)
            datasets[f"{switch.__class__.__name__}"].append((switch._to_dict()))

        datasets[f"{CpnRouter.__name__}"] = []
        for router in CpnRouter.all():
            # print(router.__class__.__name__)
            datasets[f"{router.__class__.__name__}"].append((router._to_dict()))

        datasets[f"{Task.__name__}"] = []
        for task in Task.all():
            datasets[f"{task.__class__.__name__}"].append((task._to_dict()))

        datasets[f"{NetworkLink.__name__}"] = []
        for link in NetworkLink.all():
            datasets[f"{link.__class__.__name__}"].append((link._to_dict()))
        return datasets



    def testHello(self):
        print("Hello")

    #仿真模块测试
    #1.场景导入测试
    def testScenarios(self):
        print("testScenarios")

        # 仿真停止函数
        def Stop_func() -> bool:
            return True
        simulator = Simulator(
        stopping_criterion = Stop_func,scheduler=MyScheduler)
        simulator.initialize(input_file="D:\\学习文档资料\\edgesimpy\\论文仿真\\Test\\test1.json")
        datasets = self.Collect_Components()
        #打印信息
        for key,value in datasets.items():
            print(key+":")
            if type(value) is list:
                for e in value:
                    print("[")
                    if type(e) is dict:
                        for subkey,subvalue in e.items():
                            print("{")
                            print(subkey+":")
                            print(subvalue)
                            print("}")
                    print("]")
            elif type(value) is dict:
                for subkey, subvalue in value.items():
                    print("{")
                    print(subkey + ":")
                    print(subvalue)
                    print("}")

    #2.任务上传测试
    def testUptasks(self):
        print("testUptasks")
        # 仿真停止函数
        def Stop_func() -> bool:
            return True
        simulator = Simulator(
        stopping_criterion = Stop_func,scheduler=MyScheduler)
        simulator.initialize(input_file="D:\\学习文档资料\\edgesimpy\\论文仿真\\Test\\test1.json")
        # 上传任务请求
        for agent in Task.all():
            agent.step()
        # CPN路由器上传到控制器队列中
        for agent in CpnRouter.all():
            agent.step()

        #打印控制器任务队列
        for agent in Controller.all():
            data = agent._to_dict()
            for key,value in data.items():
                print(key+":")
                if type(value) is list:
                    for e in value:
                        if type(e) is dict:
                            for subkey,subvalue in e.items():
                                print("{"+subkey+":"+str(subvalue)+"}")
                elif type(value) is dict:
                    for subkey, subvalue in value.items():
                        print("{" + subkey + ":" + str(subvalue) + "}")

            # 控制器决策下发
            agent.step()





        
        


if __name__ == '__main__':
    unittest.main()

