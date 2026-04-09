
sla_list={
    "min_bw":[1,2,5],
    "max_delay":[[40,60],[20,40],[8,20]],
    "price_gamma":[[0.6,1],[0.4,0.6],[0.2,0.4]]
}

#不同任务类型的资源需求取值范围
task_list={
    "cpu_flops":[[5,10],[10,20],[20,40]],
    "gpu_flops":[[10,40],[40,80],[80,100]],
    "cpu":[[1,2],[2,4],[4,8]],
    "gpu":[[2,4],[4,6],[6,8]],
    "disk":[[5,10],[10,20],[20,40]]
}


num_cpn = 3

cpn_state_min = [100,100,500,50,1,1,0,0,0,0]*num_cpn
cpn_state_max = [300,300,1000,200,4,4,1,1,1,1]*num_cpn
task_state_min=[5,10,1,2,5,8,0.2]
task_state_max=[40,100,8,8,40,60,1]

state_min = []
state_min.extend(task_state_min)
state_min.extend(cpn_state_min)

state_max = []
state_max.extend(task_state_max)
state_max.extend(cpn_state_max)


areaID_list=[1,2,3]

params_file= "D:\\学习文档资料\\edgesimpy\\论文仿真\\Test\\params.json"

initialize_file = "D:\\学习文档资料\\edgesimpy\\论文仿真\\Test\\test1.json"

