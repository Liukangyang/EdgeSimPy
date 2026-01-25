什么是EdgeSimpy：

<font style="color:rgb(31, 35, 40);">EdgeSimPy 是一款基于 Python 的边缘计算模拟器，具备易于理解的边缘服务器、网络设备和应用抽象，内置用户移动性、应用组合和功耗模型。</font>

<font style="color:rgb(31, 35, 40);">EdgeSimPy 的使用场景概述见下图：</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://github.com/EdgeSimPy/EdgeSimPy/raw/master/docs/assets/edgesimpy-features.jpg)

### EdgeSimpy的组成：
<font style="color:rgb(31, 35, 40);">EdgeSimPy 的功能抽象分为四层：</font>

**<font style="color:rgb(31, 35, 40);">➡️</font>****<font style="color:rgb(31, 35, 40);"> 核心层：</font>**<font style="color:rgb(31, 35, 40);">包含数据加载、时间推进和实体监控所需的基本库和函数。</font>

**<font style="color:rgb(31, 35, 40);">➡️</font>****<font style="color:rgb(31, 35, 40);"> 物理层：</font>**<font style="color:rgb(31, 35, 40);">包含具有地理空间信息的实体的功能抽象（例如，用户、服务器和网络设备）。</font>

**<font style="color:rgb(31, 35, 40);">➡️</font>****<font style="color:rgb(31, 35, 40);"> 逻辑层：</font>**<font style="color:rgb(31, 35, 40);">包含运行在边缘基础设施上的应用的功能抽象。值得注意的是，EdgeSimPy 采用容器化作为默认虚拟化模型。</font>

**<font style="color:rgb(31, 35, 40);">➡️</font>****<font style="color:rgb(31, 35, 40);"> 管理层：</font>**<font style="color:rgb(31, 35, 40);">定义主要资源分配决策，包括服务部署与迁移、维护作以及网络流调度。</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://github.com/EdgeSimPy/EdgeSimPy/raw/master/docs/assets/edgesimpy-architecture.jpg)



所需模块：

+ numpy
+ pandas
+ networkx
+ jupyter
+ edgesimpy==1.1.0



### 各组件属性定义
用户属性的定义：

在 EdgeSimPy 中，用户的定义通常分为两部分：

1. `**attributes**`: 存储用户的具体参数（如位置、SLA 等）。
2. `**relationships**`: 定储用户与其他对象的关联（如连接到哪个基站、使用什么应用）。

以下是对你提供的 JSON 片段中各个属性的详细解释：

1. **Attributes (属性)**

这部分定义了用户的静态特征和动态行为参数。

+ `**id**`: 用户的唯一标识符。在模拟中用于区分不同的用户设备。
+ `**coordinates**`: 用户的**初始**二维坐标位置 `[x, y]`。在你的示例中，用户初始位于 `(6, 0)`。
+ `**coordinates_trace**`: **移动轨迹**。这是一个数组的数组，记录了用户在模拟过程中每一秒（或每个时间步）的具体坐标。
    - _源码逻辑_：模拟器会按顺序读取这个列表，更新用户的位置。在你的示例中，用户的位置一直保持在 `(6, 0)`，表示该用户处于静止状态。
+ `**delays**`: **请求延迟**。定义了用户针对特定请求的处理延迟。
    - _格式_：`{"request_id": delay_value}`。
    - _示例_：`"1": 10` 表示 ID 为 1 的请求，其延迟值为 10（单位取决于模拟配置，通常是毫秒）。
+ `**delay_slas**`: **延迟服务等级协议**。定义了用户对特定请求所能容忍的最大延迟。
    - _格式_：`{"request_id": max_delay_sla}`。
    - _示例_：`"1": 45` 表示 ID 为 1 的请求，其最大允许延迟为 45。如果实际延迟超过这个值，请求可能会被视为失败或违反 SLA。
+ `**communication_paths**`: **通信路径**。定义了用户请求在网络中的传输路径。
    - _格式_：`{"request_id": [[node1, node2, ...]]}`。
    - _示例_：`"1": [[4, 8]]` 表示 ID 为 1 的请求，其数据包将从节点 4 传输到节点 8。
+ `**making_requests**`: **请求生成模式**。定义了用户在特定时间是否生成请求。
    - _格式_：`{"time_step": {"request_id": boolean}}`。
    - _示例_：`"1": {"1": true}` 表示在时间步 1，用户生成 ID 为 1 的请求。

**2. Relationships (关系)**

这部分定义了用户与模拟环境中其他组件的连接。

+ `**access_patterns**`: **访问模式**。定义了用户生成请求的规律（例如周期性、随机性）。
    - _结构_：指定了使用的访问模式类（`class`）和该模式的 ID。
    - _示例_：使用了 `CircularDurationAndIntervalAccessPattern` 类，这通常意味着用户会按照固定的周期和间隔来发送请求。
+ `**mobility_model**`: **移动模型**。定义了用户移动的逻辑类型。
    - _示例_：`"pathway"` 表示用户将根据预定义的路径（即上面的 `coordinates_trace`）进行移动。
+ `**applications**`: **关联的应用**。定义了用户正在使用的应用程序。
    - _结构_：数组，包含应用的类名（`Application`）和应用的 ID。
    - _示例_：用户使用了 ID 为 1 的应用程序。
+ `**base_station**`: **连接的基站**。定义了用户当前连接或关联的基站。
    - _结构_：包含基站的类名（`BaseStation`）和基站的 ID。
    - _示例_：用户连接到了 ID 为 4 的基站。



```java
"User": [
        {
            "attributes": {
                "id": 1,
                "coordinates": [
                    6,
                    0
                ],
                "coordinates_trace": [
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ],
                    [
                        6,
                        0
                    ]
                ],
                "delays": {
                    "1": 10
                },
                "delay_slas": {
                    "1": 45
                },
                "communication_paths": {
                    "1": [
                        [
                            4,
                            8
                        ]
                    ]
                },
                "making_requests": {
                    "1": {
                        "1": true
                    }
                }
            },
            "relationships": {
                "access_patterns": {
                    "1": {
                        "class": "CircularDurationAndIntervalAccessPattern",
                        "id": 1
                    }
                },
                "mobility_model": "pathway",
                "applications": [
                    {
                        "class": "Application",
                        "id": 1
                    }
                ],
                "base_station": {
                    "class": "BaseStation",
                    "id": 4
                }
            }
        },
```



基站属性：

```java
    "BaseStation": [
//..//
{
            "attributes": {
                "id": 4,
                "coordinates": [
                    6,
                    0
                ],
                "wireless_delay": 5
            },
            "relationships": {
                "users": [
                    {
                        "class": "User",
                        "id": 1
                    },
                    {
                        "class": "User",
                        "id": 4
                    }
                ],
                "edge_servers": [
                    {
                        "class": "EdgeServer",
                        "id": 3
                    }
                ],
                "network_switch": {
                    "class": "NetworkSwitch",
                    "id": 4
                }
            }
        },
//..//
],
```

其中relationship关联可关联至用户，边缘服务器以及网络交换机



网络链路属性：

```json
 "NetworkLink": [
  {
              "attributes": {
                  "id": 16,
                  "delay": 5,
                  "bandwidth": 12.5,
                  "bandwidth_demand": 0,
                  "active": true
              },
              "relationships": {
                  "topology": {
                      "class": "Topology",
                      "id": 1
                  },
                  "active_flows": [],
                  "applications": [
                      {
                          "class": "Application",
                          "id": 2
                      }
                  ],
                  "nodes": [
                      {
                          "class": "NetworkSwitch",
                          "id": 6
                      },
                      {
                          "class": "NetworkSwitch",
                          "id": 7
                      }
                  ]
              }
          },
 ],
```





网络交换机属性：

```json
 "NetworkSwitch": [
        //..//
    {
                "attributes": {
                    "id": 1,
                    "coordinates": [
                        0,
                        0
                    ],
                    "active": true,
                    "power_model_parameters": {
                        "chassis_power": 60,
                        "ports_power_consumption": {
                            "125": 1,
                            "12.5": 0.3
                        }
                    }
                },
                "relationships": {
                    "power_model": "ConteratoNetworkPowerModel",
                    "edge_servers": [
                        {
                            "class": "EdgeServer",
                            "id": 1
                        }
                    ],
                    "links": [],
                    "base_station": {
                        "class": "BaseStation",
                        "id": 1
                    }
                }
            },
       //..// 
    ],
```

+ `**power_model**`:
    - **含义**：指定用于计算该交换机功耗的**Python 类名**。
    - _示例_：`"ConteratoNetworkPowerModel"`。这告诉模拟器在计算能耗时，应实例化 `ConteratoNetworkPowerModel` 类并调用其方法。这通常是 EdgeSimPy 中实现的一种特定网络功耗算法。
+ `**edge_servers**`:
    - **含义**：与该交换机直接相连的**边缘服务器列表**。
    - _结构_：数组，每个元素包含关联对象的类名（`class`）和唯一 ID（`id`）。
    - _示例_：`{"class": "EdgeServer", "id": 1}` 表示 ID 为 1 的边缘服务器连接到了这个交换机上。
+ `**links**`:
    - **含义**：连接到其他交换机的**链路列表**。
    - _注意_：在你的示例中该列表为空 `[]`。通常这里会填入连接到其他 `NetworkSwitch` 或核心路由器的 ID。如果为空，说明该交换机目前只连接了服务器和基站，没有上联到其他交换机。
+ `**base_station**`:
    - **含义**：与该交换机直接相连的**基站**。
    - _示例_：`{"class": "BaseStation", "id": 1}` 表示 ID 为 1 的基站通过有线网络连接到了这个交换机



边缘服务器属性：

```json
    "EdgeServer": [
        {
            "attributes": {
                "id": 1,
                "available": true,
                "model_name": "E5430",
                "cpu": 8,
                "memory": 16384,
                "disk": 131072,
                "cpu_demand": 0,
                "memory_demand": 0,
                "disk_demand": 0,
                "coordinates": [
                    0,
                    0
                ],
                "max_concurrent_layer_downloads": 3,
                "active": true,
                "power_model_parameters": {
                    "max_power_consumption": 265,
                    "static_power_percentage": 0.6264
                }
            },
            "relationships": {
                "power_model": "LinearServerPowerModel",
                "base_station": {
                    "class": "BaseStation",
                    "id": 1
                },
                "network_switch": {
                    "class": "NetworkSwitch",
                    "id": 1
                },
                "services": [],
                "container_layers": [],
                "container_images": [],
                "container_registries": []
            }
        },
```

```json
"EdgeServer": [
        {
            "attributes": {
                "id": 1,
                "available": true,
                "model_name": "E5430",
                "cpu": 8,
                "memory": 16384,
                "disk": 131072,
                "cpu_demand": 0,
                "memory_demand": 0,
                "disk_demand": 0,
                "coordinates": [
                    0,
                    0
                ],
                "max_concurrent_layer_downloads": 3,
                "active": true,
                "power_model_parameters": {
                    "max_power_consumption": 265,
                    "static_power_percentage": 0.6264
                }
            },
            "relationships": {
                "power_model": "LinearServerPowerModel",
                "base_station": {
                    "class": "BaseStation",
                    "id": 1
                },
                "network_switch": {
                    "class": "NetworkSwitch",
                    "id": 1
                },
                "services": [],
                "container_layers": [],
                "container_images": [],
                "container_registries": []
            }
        },
```

+ `**id**`:
    - **含义**：服务器的唯一标识符。
+ `**available**`:
    - **含义**：布尔值，表示该服务器是否处于“可用”状态。如果设置为 `false`，调度器将不会向其分配新的任务。
+ `**model_name**`:
    - **含义**：服务器的型号名称。示例中的 `"E5430"` 通常指代 Intel Xeon E5430 处理器，用于标识硬件配置。（代表了CPU的主频）
+ `**cpu**`:
    - **含义**：服务器的 **总 CPU 计算能力**。单位通常是 **MIPS** (每秒百万条指令) 或仅仅是 CPU 核心的抽象算力值。示例中为 `8`。
+ `**memory**`:
    - **含义**：服务器的 **内存容量**。单位通常是 **KB** (千字节) 或 MB。示例中为 `16384`。
+ `**disk**`:
    - **含义**：服务器的 **磁盘存储容量**。单位通常也是 KB 或 MB。示例中为 `131072`。
+ `**cpu_demand**`**,**** **`**memory_demand**`**,**** **`**disk_demand**`:
    - **含义**：当前已使用的资源量（或资源需求累积值）。模拟器在运行时会动态更新这些值，以反映服务器的负载情况。初始值通常为 `0`。
+ `**coordinates**`:
    - **含义**：服务器的二维坐标位置 `[x, y]`。用于计算与基站或用户之间的网络距离/延迟。
+ `**max_concurrent_layer_downloads**`:
    - **含义**：拉取容器镜像时，**最大并发下载层数**。容器镜像由多层组成，此参数限制同时下载的层数，影响服务启动时间。
+ `**active**`:
    - **含义**：服务器当前是否处于“活跃”状态（已开机）。与 `available` 不同，`active` 更多指物理电源状态。
+ `**ower_model_parameters**`<font style="color:rgb(6, 10, 38);">:</font>
    - **含义**：功耗模型的具体参数配置。
+ `**max_power_consumption**`: 服务器满载时的最大功耗（瓦特 W）。示例中为 `265`W。
+ `**static_power_percentage**`: 服务器的静态功耗占比（范围 0～1）。根据线性功耗模型，即使 CPU 利用率为 0，服务器也会消耗一部分基础电力。示例中 `0.6264` 表示基础功耗占最大功耗的 62.64%。
+ `**power_model**`:
    - **含义**：指定计算服务器功耗的算法类。
    - _示例_：`"LinearServerPowerModel"`。这是 EdgeSimPy 中常用的一种线性功耗模型，根据 CPU 利用率线性插值计算当前功耗。
+ `**base_station**`:
    - **含义**：与该服务器关联的基站。
    - _注意_：这通常表示该服务器为附近的基站提供边缘计算支持（MEC 架构）。但在实际拓扑中，服务器通常是通过交换机连接到基站的，这里的直接关联可能是为了简化延迟计算或管理归属。
+ `**network_switch**`:
    - **含义**：与该服务器直接连接的**网络交换机**。
    - _示例_：连接到 ID 为 1 的 `NetworkSwitch`。这是数据进出服务器的主要通道。
+ `**services**`:
    - **含义**：当前部署在该服务器上运行的**服务列表**。在 JSON 初始化时通常为空 `[]`，由模拟器的调度器在运行时动态填充。
+ `**container_layers**`, `**container_images**`, `**container_registries**`:
    - **含义**：缓存的容器层、镜像和注册表引用。模拟器利用这些信息来优化容器部署时的镜像拉取时间（如果镜像已缓存，则无需下载）。



服务定义：







应用定义：





### 代码解析


#### 一、从指定json文件中导入数据集，构建各部分组件
```python
from edge_sim_py import *
simulator = Simulator()

# Loading the dataset from the local "dataset.json" file
simulator.initialize(input_file="dataset.json")

# Displaying some of the objects loaded from the dataset
for edge_server in EdgeServer.all():
    print(f"{edge_server}. CPU Capacity: {edge_server.cpu} cores")

```

其中initialize函数中的input_file参数可传入URL地址，本地json文件的路径或者自定义的json字典



#### 二、ComponentManager类的辅助函数
常用函数：

component.all():返回所有对象示例的列表

component.first()/last():返回列表中的第一个和最后一个对象（按照ID排序）

component.count():返回对象集合的计数值

component.find_by_id(int):根据指定ID查找对象

component.find_by(attribute_name: str, attribute_value: object)：根据指定属性值查找对象



自定义辅助函数：

自定义一个辅助函数后，可通过classmethod将其转化为类中的方法，并赋予给componentManager类的相应成员。

示例：

```python
ComponentManager.sorted_by = classmethod(sorted_by)
```

注册到componentManager类后，所有继承的子类组件（如User,EdgeServer等）都可以使用自定义的辅助函数：

```python
edge_servers = EdgeServer.sorted_by(attribute="id", order="descending")
for edge_server in edge_servers:
    print(f"{edge_server}")

```



#### 三、管理仿真数据输出
在EdgesimPy中，使用MessagePack模块记录姐记录结果数据，

若要访问记录的数据， 有以下两种办法：

1.直接访问记录数据的变量

2.仿真运行结束后查看保存在磁盘中的日志文件。

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/45416683/1768890227134-b0940147-ee1e-49ad-b17e-3e7eadd32e3b.png)



1，直接访问变量：

通过Simulator类中的agent_metrics属性可访问各类元素的属性

例如：

```python
simulator.agent_metrics["User"]
```



2.读取日志文件，并转化为pandas数据格式

```python
logs_directory = f"{os.getcwd()}/logs"
dataset_files = [file for file in os.listdir(logs_directory) if ".msgpack" in file]

# Reading msgpack files found
datasets = {}
for file in dataset_files:
    with open(f"logs/{file}", "rb") as data_file:
        datasets[file.replace(".msgpack", "")] = 
             pd.DataFrame(msgpack.unpackb(data_file.read(), strict_map_key=False))
```

转化为DataFrame格式后，进一步可通过Pandas的filter方法过滤出想要的属性列：

```python
properties = ['Coordinates', 'CPU Demand', 'RAM Demand', 'Disk Demand', 'Services']
columns = ['Time Step', 'Instance ID'] + properties

dataframe = datasets["EdgeServer"].filter(items=columns)
```

如何管理各agent元素需要统计的指标？（自定义）

-可自定义指标统计函数，构建指标字典，并将统计函数覆写collect函数，

示例：

```python
def custom_collect_method(self) -> dict:
    temperature = random.randint(10, 50)  # Generating a random integer between 10 and 50 representing the switch's temperature
    metrics = {
        "Instance ID": self.id,
        "Power Consumption": self.get_power_consumption(),
        "Temperature": temperature,
    }
    return metrics

# Overriding the NetworkSwitch's collect() method
NetworkSwitch.collect = custom_collect_method
```



#### 四、Simulator类
属性：

```python
stopping_criterion: Callable = None,
resource_management_algorithm: Callable = None,
resource_management_algorithm_parameters: dict = {},
user_defined_functions: list = [],
network_flow_scheduling_algorithm: Callable = max_min_fairness,
tick_duration: int = 1,
tick_unit: str = "seconds",
obj_id: int = None,
scheduler: Callable = DefaultScheduler,
dump_interval: int = 100,
logs_directory: str = "logs",
```

构造函数init：指定步进周期时间、结果记录周期时间，仿真停止判断函数以及资源管理函数

其中仿真停止判断函数和资源管理函数需要自己指定

```python
simulator = Simulator(
    dump_interval=5,
    tick_duration=1,
    tick_unit="seconds",
    stopping_criterion=stopping_criterion,  #自定义仿真停止函数
    resource_management_algorithm=my_algorithm, #自定义服务部署策略
)
```



`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">dump_data_to_disk</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">(</font><font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">clean_data_in_memory</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">=</font><font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">True</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">)</font>`

实现将仿真运行结果保存到磁盘当中



`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">initialize</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">(</font><font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">input_file</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">)</font>`

根据input_file读取Json格式数据，初始化仿真元素配置

```python
    def initialize(self, input_file: str) -> None:
        """Sets up the initial values for state variables, which includes, e.g., loading components from a dataset file.

        Args:
            input_file (str): Dataset file (URL for external JSON file, path for local JSON file, Python dictionary).
        """
        # Resetting the list of instances of EdgeSimPy's component classes
        for component_class in ComponentManager.__subclasses__():
            if component_class.__name__ != "Simulator":
                component_class._object_count = 0
                component_class._instances = []

        # Declaring an empty variable that will receive the dataset metadata (if user passes valid information)
        data = None

        # If "input_file" is a Python dictionary, no additional parsing is needed before starting loading the dataset
        if type(input_file) is dict:
            data = input_file

        # If "input_file" represents a valid URL, parses its response
        elif all([urlparse(input_file).scheme, urlparse(input_file).netloc]):
            data = json.loads(urlopen(input_file).read())

        # If "input_file" points to the local filesystem, checks if the file exists and parses it
        else:
            if os.path.exists(input_file):
                with open(input_file, "r", encoding="UTF-8") as read_file:
                    data = json.load(read_file)

            elif os.path.exists(f"{os.getcwd()}/{input_file}"):
                with open(f"{os.getcwd()}/{input_file}", "r", encoding="UTF-8") as read_file:
                    data = json.load(read_file)

        # Raising exception if the dataset could not be loaded based on the specified arguments
        if type(data) is not dict:
            raise TypeError("EdgeSimPy could not load the dataset based on the specified arguments.")

        # Creating simulator components based on the specified input data
        missing_keys = [key for key in data.keys() if key not in globals()]
        if len(missing_keys) > 0:
            raise Exception(f"\n\nCould not find component classes named: {missing_keys}. Please check your input file.\n\n")

        # Creating a list that will store all the relationships among components
        components = []

        # Creating the topology object and storing a reference to it as an attribute of the Simulator instance
        topology = self.initialize_agent(agent=Topology())
        self.topology = topology

        # Creating simulator components
        for key in data.keys():
            if key != "Simulator" and key != "Topology":
                for object_metadata in data[key]:
                    new_component = globals()[key]._from_dict(dictionary=object_metadata["attributes"])
                    new_component.relationships = object_metadata["relationships"]

                    if hasattr(new_component, "model") and hasattr(new_component, "unique_id"):
                        self.initialize_agent(agent=new_component)

                    components.append(new_component)

        # Defining relationships between components
        for component in components:
            for key, value in component.relationships.items():
                # Defining attributes referencing callables (i.e., functions and methods)
                if type(value) == str and value in globals():
                    setattr(component, f"{key}", globals()[value])

                # Defining attributes referencing lists of components (e.g., lists of edge servers, users, etc.)
                elif type(value) == list:
                    attribute_values = []
                    for item in value:
                        obj = (
                            globals()[item["class"]].find_by_id(item["id"])
                            if type(item) == dict and "class" in item and item["class"] in globals()
                            else None
                        )

                        if obj == None:
                            raise Exception(f"List relationship '{key}' of component {component} has an invalid item: {item}.")

                        attribute_values.append(obj)

                    setattr(component, f"{key}", attribute_values)

                # Defining attributes that reference a single component (e.g., an edge server, an user, etc.)
                elif type(value) == dict and "class" in value and "id" in value:
                    obj = (
                        globals()[value["class"]].find_by_id(value["id"])
                        if type(value) == dict and "class" in value and value["class"] in globals()
                        else None
                    )

                    if obj == None:
                        raise Exception(f"Relationship '{key}' of component {component} references an invalid object: {value}.")

                    setattr(component, f"{key}", obj)

                # Defining attributes that reference a a dictionary of components (e.g., {"1": {"class": "A", "id": 1}} )
                elif type(value) == dict and all(
                    type(entry) == dict and "class" in entry and "id" in entry for entry in value.values()
                ):
                    attribute = {}
                    for k, v in value.items():
                        obj = globals()[v["class"]].find_by_id(v["id"]) if "class" in v and v["class"] in globals() else None
                        if obj == None:
                            raise Exception(
                                f"Relationship '{key}' of component {component} references an invalid object: {value}."
                            )
                        attribute[k] = obj

                    setattr(component, f"{key}", attribute)

                # Defining "None" attributes
                elif value == None:
                    setattr(component, f"{key}", None)

                else:
                    raise Exception(f"Couldn't add the relationship {key} with value {value}. Please check your dataset.")

        # Filling the network topology
        for link in NetworkLink.all():
            # Adding the nodes connected by the link to the topology
            topology.add_node(link.nodes[0])
            topology.add_node(link.nodes[1])

            # Replacing NetworkX's default link dictionary with the NetworkLink object
            topology.add_edge(link.nodes[0], link.nodes[1])
            topology._adj[link.nodes[0]][link.nodes[1]] = link
            topology._adj[link.nodes[1]][link.nodes[0]] = link
```

<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">其中对于读取json数据的映射关系如下：</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/45416683/1769159097038-bd8ac69e-ff22-4bae-a98c-e596d1ab1622.png)



`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">initialize_agent</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">(</font><font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">agent</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">)</font>`

初始化对象

```python
def initialize_agent(self, agent: object) -> object:
        """Initializes an agent object.

        Args:
            agent (object): Agent object.

        Returns:
            object: Initialized agent.
        """
        # Reference to the Simulator object
        agent.model = ComponentManager._ComponentManager__model

        # Agent unique ID
        agent.unique_id = agent.model.next_id()

        # Agent class constructor
        Agent.__init__(self=agent, unique_id=agent.unique_id, model=agent.model)

        # Adding the object to the list of agents of its model
        agent.model.schedule.add(agent)

        return agent
```

`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">monitor</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">()</font>`

记录仿真运行过程中各agent的指标



`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">run_model</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">()</font>`

运行仿真

```python
def run_model(self):
    """Executes the simulation."""
    if self.stopping_criterion == None:
        raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

    if self.resource_management_algorithm == None:
        raise Exception("Please assign the 'resource_management_algorithm' attribute before starting the simulation.")

    # Calls the method that collects monitoring data about the agents
    self.monitor()

    while self.running:
        # Calls the method that advances the simulation time
        self.step()

        # Calls the method that collects monitoring data about the agents
        self.monitor()

        # Checks if the simulation should end according to the stop condition
        self.running = False if self.stopping_criterion(self) else True

    # Dumps simulation data to the disk to make sure no metrics are discarded
    self.dump_data_to_disk()
```



`<font style="color:rgb(54, 70, 78);background-color:rgb(245, 245, 245);">step</font><font style="color:rgba(0, 0, 0, 0.54);background-color:rgb(245, 245, 245);">()</font>`

执行仿真步进

```python
def step(self):
    """Advances the model's system in one step."""
    # Running resource management algorithm
    self.resource_management_algorithm(parameters=self.resource_management_algorithm_parameters)

    # Activating agents
    self.schedule.step()

    # Updating the "current_step" attribute inside the resource management algorithm's parameters
    self.resource_management_algorithm_parameters["current_step"] = self.schedule.steps + 1

```



五、定义自己的服务部署策略

先定义服务部署策略函数，如：

```python
def my_algorithm(parameters):
    # We can always call the 'all()' method to get a list with all created instances of a given class
    for service in Service.all():
        # We don't want to migrate services are are already being migrated
        if service.server == None and not service.being_provisioned:

            # Let's iterate over the list of edge servers to find a suitable host for our service
            for edge_server in EdgeServer.all():
                
                # We must check if the edge server has enough resources to host the service
                if edge_server.has_capacity_to_host(service=service):
                    
                    # Start provisioning the service in the edge server(将服务部署到服务器上)
                    service.provision(target_server=edge_server)  
                    
                    # After start migrating the service we can move on to the next service
                    break
```

然后在创建Simulaltor实例化对象时，指定resource_management_algorithm成员参数，赋予自定义策略函数：

```python
# Creating a Simulator object
simulator = Simulator(
    tick_duration=1,
    tick_unit="seconds",
    stopping_criterion=stopping_criterion,
    resource_management_algorithm=my_algorithm,
)
```



六、自定义服务迁移函数

与自定义服务部署策略类似的，先定义迁移函数，然后在创建Simulaltor实例化对象时，将迁移策略指定r给resource_management_algorithm成员。

```python
def my_algorithm(parameters):
    # Let's iterate over the list of services using the 'all()' helper method
    print("\n\n")
    print(f"==== TIME STEP {parameters['current_step']} ====")
    print("---- EDGE SERVERS ----")
    for server in EdgeServer.all():
        server_metadata = {
            "server": server,
            "capacity": [server.cpu, server.memory, server.disk], #容量
            "demand": [server.cpu_demand, server.memory_demand, server.disk_demand], #当前的占用
            "container_layers": [layer.id for layer in server.container_layers],
            "services": [service for service in server.services],  #服务
        }
        print(server_metadata)

    print("")
    print("---- SERVICES ----")
    for service in Service.all():
        service_image = ContainerImage.find_by(attribute_name="digest", attribute_value=service.image_digest)
        service_layers = [ContainerLayer.find_by(attribute_name="digest", attribute_value=layer).id for layer in service_image.layers_digests]

        service_metadata = {
            "service": service,
            "requirements": [service.cpu_demand, service.memory_demand],
            "layers": service_layers,
            "server": service.server,
            "available": service._available,
            "being_provisioned": service.being_provisioned,
        }
        print(service_metadata)

    # We don't want to migrate services are are already being migrated. As we want to avoid excessive migrations, we are going to
    # define a cool down period for services that have been migrated. For simplicity, we are going to set the cool down period as
    # 10 time steps. To get such information, we are going to access the service's last migration time step and compare it with
    # the current time step. If the difference between the current time step and the last migration time step is less than 10,
    # we are going to skip the service.
    COOLDOWN_STEPS = 10

    for service in Service.all():
        # Gathering the current time step and the last migration time step of the service
        current_step = parameters["current_step"]
        
        if len(service._Service__migrations) > 0 and service._Service__migrations[-1]["end"] is not None:
            last_migration_ended_at = service._Service__migrations[-1]["end"]
        else:
            last_migration_ended_at = None

        # Checking if the service is not being provisioned and if the cool down period has being reached
        service_has_not_been_migrated_yet = len(service._Service__migrations) == 0
        service_not_being_provisioned = service.being_provisioned is False
        cooldown_has_been_reached = last_migration_ended_at is not None and current_step - last_migration_ended_at >= COOLDOWN_STEPS

        if service_has_not_been_migrated_yet or service_not_being_provisioned and cooldown_has_been_reached:
            # We need to sort edge servers based on amount of free resources they have. To do so, we are going to use Python's
            # "sorted" method (you can learn more about "sorted()" in this link: https://docs.python.org/3/howto/sorting.html).
            # The capacity of edge servers is modeled in three layers (CPU, memory, and disk). For simplicity, we are going to
            # use only the CPU layer to sort edge servers. We calculate the free CPU resources of each edge server by subtracting
            # the CPU demand of the services hosted in the edge server from the total CPU capacity of the edge server. We then
            # sort edge servers based on their free CPU resources. To do so, we use the "sorted" method and set the "key" attribute
            # as a lambda function that calculates the free CPU resources of edge servers. We set the "reverse" attribute as "True"
            # as we want to sort edge servers by their free CPU resources in descending order.
            edge_servers = sorted(
                EdgeServer.all(),
                key=lambda s: s.cpu - s.cpu_demand,
                reverse=True,
            )

            for edge_server in edge_servers:
                # Checking if the edge server has resources to host the service
                if edge_server.has_capacity_to_host(service=service):
                    # We just need to migrate the service if it's not already in the least occupied edge server
                    if service.server != edge_server:
                        print(f"\t\t[STEP {parameters['current_step']}] Migrating {service} From {service.server} to {edge_server}")

                        service.provision(target_server=edge_server)

                        # After start migrating the service we can move on to the next service
                        break
                        
```



```python
simulator = Simulator(
    tick_duration=1,
    tick_unit="seconds",
    stopping_criterion=stopping_criterion,
    resource_management_algorithm=my_algorithm,
)
```



#### 五、ComponentManage
ComponentManage是该平台所有元素对象的父类，其主要提供了一些类方法供仿真时调用，

包括：

_**export_scenario**_ ：以json格式导出仿真场景  ==》后续可修改到处自定义状态信息

_from_dict：根据键值对字典创建对象并设置对象属性

find_by和find_by_id：根据属性值和id值返回查询对象

all：返回子类的所有元素对象列表

first/last：返回子类的元素对象列表中的第一个和最后一个对象

count：统计子类的元素对象列表长度，即对象个数

remove：从子类的元素对象列表中删除指定对象，若不存在则抛出异常



### 基础设施层
#### 一、User模型
User类的对象属性主要包括:

```python
#全局属性
_instances = []  #全局用户列表 
_object_count = 0  #全局用户计数
self.id = obj_id #用户id

# User coordinates（坐标）
self.coordinates_trace = []  #移动坐标轨迹
self.coordinates = None  #当前坐标

# List of applications accessed by the user
self.applications = []  #应用列表

# Reference to the base station the user is connected to
self.base_station = None  #关联基站

# User access metadata
self.making_requests = {}
self.access_patterns = {}

# User mobility model（移动模型）
self.mobility_model = None
self.mobility_model_parameters = {}

# List of metadata from applications accessed by the user
self.communication_paths = {}  #通信路径
self.delays = {}  #通信时延
self.delay_slas = {}  #最大时延

# Model-specific attributes (defined inside the model's "initialize()" method)
self.model = None  #指定模型
self.unique_id = None


```

  

_to_dict函数以字典形式打印用户参数，collect函数以字典形式收集用户对象指标



_compute_delay：服务时延计算

用于计算服务从用户流转到边缘服务器上的总时延，其中调用的关键函数是：

_**topology.calculate_path_delay**_



set_communication_path：更新服务流转路径

计算路径时采用的是最短路径算法：

```python
path = nx.shortest_path(
    G=topology,
    source=origin.network_switch,
    target=target.network_switch,
    weight="delay",  #权重
    method="dijkstra",  #最短路径算法
)
```

其中调用的关键函数为_**topology._allocate_communication_path**_

_****_

_connect_to_application_**：**_将服务与用户相关联

_set_initial_position：设置用户初始位置，并将用户与相邻无线基站相关联



根据上述用户类定义，可自定义服务源节点，其中去除基站关联，而实现接入交换机关联

同时需修改topology中的路径更新函数



步进函数：

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        # Updating user access
        current_step = self.model.schedule.steps + 1
        for app in self.applications:
            last_access = self.access_patterns[str(app.id)].history[-1]

            # Updating user access waiting and access times. Waiting time represents the period in which the user is waiting for
            # his application to be provisioned. Access time represents the period in which the user is successfully accessing
            # his application, meaning his application is available. We assume that an application is only available when all its
            # services are available.
            if self.making_requests[str(app.id)][str(current_step)] == True:
                if len([s for s in app.services if s._available]) == len(app.services):
                    last_access["access_time"] += 1
                else:
                    last_access["waiting_time"] += 1

            # Updating user's making requests attribute for the next time step
            if current_step + 1 >= last_access["start"] and current_step + 1 <= last_access["end"]:
                self.making_requests[str(app.id)][str(current_step + 1)] = True
            else:
                self.making_requests[str(app.id)][str(current_step + 1)] = False

            # Creating new access request if needed
            if current_step + 1 == last_access["next_access"]:
                self.making_requests[str(app.id)][str(current_step + 1)] = True
                self.access_patterns[str(app.id)].get_next_access(start=current_step + 1)

        # Re-executing user's mobility model in case no future mobility track is known by the simulator
        if len(self.coordinates_trace) <= self.model.schedule.steps:
            self.mobility_model(self)  #执行一次移动

        # Updating user's location
        if self.coordinates != self.coordinates_trace[self.model.schedule.steps]:
            self.coordinates = self.coordinates_trace[self.model.schedule.steps]

            # Connecting the user to the closest base station
            self.base_station = BaseStation.find_by(attribute_name="coordinates", attribute_value=self.coordinates)

            for application in self.applications:
                # Only updates the routing path of apps available (i.e., whose services are available)
                services_available = len([s for s in application.services if s._available])
                if services_available == len(application.services): #该应用的所有服务均可用时，该应用才可用
                    # Recomputing user communication paths （更新路径）
                    self.set_communication_path(app=application)  
                else:
                    self.communication_paths[str(application.id)] = [] #不迁移
                    self._compute_delay(app=application)  #更新应用时延
```



#### 二、EdgeServer模型
服务器属性主要包括：

```python
if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Edge server model name
        self.model_name = model_name

        # Edge server base station（关联基站）
        self.base_station = None

        # Edge server network switch（直连交换机）
        self.network_switch = None

        # Edge server coordinates
        self.coordinates = coordinates

        # Edge server capacity（资源）######
        self.cpu = cpu
        self.memory = memory
        self.disk = disk

        # Edge server demand（总资源需求/占用量）####
        self.cpu_demand = 0
        self.memory_demand = 0
        self.disk_demand = 0

        # Edge server's availability status
        self.available = True

        # Number of active migrations involving the edge server
        self.ongoing_migrations = 0

        # Power Features（能耗模型）
        self.active = True
        self.power_model = power_model
        self.power_model_parameters = {}

        # Container registries and services hosted by the edge server
        self.container_registries = []
        self.services = []

        # Container images and container layers hosted by the edge server
        self.container_images = []
        self.container_layers = []

        # Lists that control the layers being pulled to the edge server
        self.waiting_queue = []
        self.download_queue = []

        # Number of container layers the edge server can download simultaneously (default = 3)
        self.max_concurrent_layer_downloads = 3

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None
```

_to_dict/collect：收集对象的属性信息并以json/键值对对象返回

get_power_consumption：利用关联能耗模型计算能耗

**has_capacity_to_host：判断是否能够容纳指定服务：**

```python
def has_capacity_to_host(self, service: object) -> bool:
        """Checks if the edge server has enough free resources to host a given service.

        Args:
            service (object): Service object that we are trying to host on the edge server.

        Returns:
            can_host (bool): Information of whether the edge server has capacity to host the service or not.
        """
        # Calculating the additional disk demand that would be incurred to the edge server
        additional_disk_demand = self._get_disk_demand_delta(service=service)

        # Calculating the edge server's free resources(计算服务器资源剩余量)
        free_cpu = self.cpu - self.cpu_demand
        free_memory = self.memory - self.memory_demand
        free_disk = self.disk - self.disk_demand

        # Checking if the host would have resources to host the registry and its (additional) layers
        can_host = free_cpu >= service.cpu_demand and free_memory >= service.memory_demand and free_disk >= additional_disk_demand
        return can_host
```

=>其中_get_disk_demand_delta根据构成服务service的容器镜像总大小决定服务占用的disk空间大小

```python
def _get_disk_demand_delta(self, service: object) -> float:
        """Calculates the additional disk demand necessary to host a registry inside the edge server considering
        the list of cached layers inside the edge server and the layers that compose the service's image.

        Args:
            service (object): Service whose disk demand delta will be calculated.

        Returns:
            disk_demand_delta (float): Disk demand delta.
        """
        # Gathering the list of layers that compose the service's image that are not present in the edge server
        uncached_layers = self._get_uncached_layers(service=service)

        # Calculating the amount of disk resources required by all service layers not present in the host's disk
        disk_demand_delta = sum([layer.size for layer in uncached_layers])

        return disk_demand_delta
```

进一步的利用_get_uncached_layers函数用于获取在当前服务器上未缓存的服务所需镜像列表



_add_container_image：添加容器镜像



step步进：

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        while len(self.waiting_queue) > 0 and len(self.download_queue) < self.max_concurrent_layer_downloads:
            layer = self.waiting_queue.pop(0)

            # Gathering the list of registries that have the layer
            registries_with_layer = []
            for registry in [reg for reg in ContainerRegistry.all() if reg.available]:
                # Checking if the registry is hosted on a valid host in the infrastructure and if it has the layer we need to pull
                if registry.server and any(layer.digest == l.digest for l in registry.server.container_layers):
                    # Selecting a network path to be used to pull the layer from the registry
                    path = nx.shortest_path(
                        G=self.model.topology,
                        source=registry.server.base_station.network_switch,
                        target=self.base_station.network_switch,
                    )

                    registries_with_layer.append({"object": registry, "path": path})

            # Selecting the registry from which the layer will be pulled to the (target) edge server
            registries_with_layer = sorted(registries_with_layer, key=lambda r: len(r["path"]))
            registry = registries_with_layer[0]["object"]
            path = registries_with_layer[0]["path"]

        flow = NetworkFlow(
            topology=self.model.topology,
            source=registry.server,          # 仓库服务器
            target=self,                     # 当前边缘服务器
            start=self.model.schedule.steps + 1,  # 下载开始时间（当前步+1）
            path=path,
            data_to_transfer=layer.size,     # 需传输的数据量
            metadata={"type": "layer", "object": layer, "container_registry": registry},
        )
        self.model.initialize_agent(agent=flow)  # 将流加入模型调度
        self.download_queue.append(flow)        # 加入当前下载队列
    }
```

流程图：

![画板](https://cdn.nlark.com/yuque/0/2026/jpeg/45416683/1769262202572-7ba38f64-4420-4f1b-9103-6bae5a32102c.jpeg)



##### NetworkFlow
其中关于网络流NetworkFlow的定义如下：

```python
if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Reference to the network topology object
        self.topology = topology

        # Flow status. Valid options: "active" (default) and "finished"
        self.status = status

        # Network nodes and path used by the flow
        self.source = source
        self.target = target
        self.path = path

        # Network capacity available to the flow
        self.bandwidth = {}
        self.last_updated_bandwidth = {}

        # Temporal information about the flow
        self.start = start
        self.end = None

        # Amount of data transferred by the flow
        self.data_to_transfer = data_to_transfer

        # Custom flow metadata
        self.metadata = metadata

        # Adding a reference to the flow inside the network links that comprehend the "path" attribute
        for i in range(0, len(path) - 1):
            link = self.topology[path[i]][path[i + 1]]
            link["active_flows"].append(self)
            self.bandwidth[link["id"]] = None
            self.last_updated_bandwidth[link["id"]] = None

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None
```

其步进函数为：

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        if self.status == "active":
            # Updating the flow progress according to the available bandwidth
            if not any([bw == None for bw in self.bandwidth.values()]):
                self.data_to_transfer -= min(self.bandwidth.values())  #单位时间内传输的数据量

            #传输完成
            if self.data_to_transfer <= 0:
                # Updating the completed flow's properties
                self.data_to_transfer = 0

                # Storing the current step as when the flow ended （记录结束时间）
                self.end = self.model.schedule.steps + 1

                # Updating the flow status to "finished"
                self.status = "finished"

                # Releasing links used by the completed flow （释放该流）
                for i in range(0, len(self.path) - 1):
                    link = self.model.topology[self.path[i]][self.path[i + 1]]
                    link["active_flows"].remove(self)

                # When container layer flows finish: Adds the container layer to its target host
                if self.metadata["type"] == "layer":
                    # Removing the flow from its target host's download queue
                    self.target.download_queue.remove(self)

                    # Adding the layer to its target host
                    layer = self.metadata["object"]
                    layer.server = self.target
                    self.target.container_layers.append(layer)

                # When service state flows finish: change the service migration status（服务迁移）
                elif self.metadata["type"] == "service_state":
                    service = self.metadata["object"]
                    service._Service__migrations[-1]["status"] = "finished"
```

模拟单位时间内传输数据，并判断是否传输完成，若传输完成，则修改对应传输对象和目标服务器的状态。



#### 三、NetworkSwitch模型
属性：

```python

        self.coordinates = None

        # Base station connected to the switch
        self.base_station = None

        # List of edge servers connected to the switch
        self.edge_servers = [] =》EdgeServer

        # List of links connected to the switch ports
        self.links = []  =》NetworkLink

        # Power Features
        self.active = True
        self.power_model = None
        self.power_model_parameters = {}

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None
```



_to_dict/collect：获取属性字段

get_power_consumption：根据能耗模型获取能耗



但是step函数没有实现具体的功能，可扩展

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        ...
```



#### 四、NetworkLink模型
属性：

```python
if obj_id is None:
            obj_id = self.__class__._object_count
        self["id"] = obj_id

        # Reference to the network topology
        self["topology"] = None

        # List of network nodes that are connected by the link
        self["nodes"] = []

        # Link delay
        self["delay"] = 0

        # Link bandwidth capacity and bandwidth demand（带宽）
        self["bandwidth"] = 0
        self["bandwidth_demand"] = 0

        # List of applications using the link for routing data to their users
        self["applications"] = []

        # List of network flows passing through the link（活跃流量）
        self["active_flows"] = []

        # Network link active status
        self["active"] = True

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self["model"] = None
        self["unique_id"] = None
```

step函数：计算总的占用带宽

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        # Updating the link's bandwidth demand based on the slice of bandwidth used by the active flows that cross it in the current step
        self["bandwidth_demand"] = sum(flow.bandwidth[self.id] for flow in self["active_flows"])
```



#### 五、Topology模型
属性：拓扑结构

```python
        if existing_graph is None:
            nx.Graph.__init__(self)
        else:
            nx.Graph.__init__(self, incoming_graph_data=existing_graph)
```



步进step方法：

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        self.model.network_flow_scheduling_algorithm(topology=self, flows=NetworkFlow.all())
```

调用_**network_flow_scheduling_algorithm**_实现流量调度=>来自于Simulator类初始化时指定的流量调度算法



calculate_path_delay：计算路径总时延

```python
def calculate_path_delay(self, path: list) -> int:
        """Calculates the communication delay of a network path.

        Args:
            path (list): Network path whose delay will be calculated.

        Returns:
            path_delay (int): Network path delay.
        """
        path_delay = 0

        # Calculates the communication delay based on the delay property of each network link in the path
        path_delay = nx.classes.function.path_weight(G=self, path=path, weight="delay")

        return path_delay
```



_allocate_communication_path：将应用添加到路径中每条链路的“applications”属性列表当中

```python
def _allocate_communication_path(self, communication_path: list, app: object):
        """Adds the demand of a given application to a set of links that comprehend a communication path.

        Args:
            communication_path (list): Communication path.
            app (object): Application object.
        """
        for path in communication_path:
            if len(path) > 1:
                for i in range(len(path) - 1):
                    node1 = path[i]
                    node2 = path[i + 1]

                    link = self[node1][node2]  #获取中间每一条链路

                    if app not in link["applications"]: #将应用加入到链路当中
                        link["applications"].append(app)
```



_release_communication_path：将应用从对应路径每条链路的“applications”属性列表中删除



### 应用/服务层
#### 一、应用模型
主要属性：

```python
        # Application label
        self.label = label

        # List of services that compose the application
        self.services = []

        # List of users that access the application
        self.users = []

```



connect_to_service：将服务绑定到该应用

step：未实现

#### 二、服务模型
主要属性：

```python
        # Service label
        self.label = label

        # Service image's digest
        self.image_digest = image_digest

        # Service demand（需求）
        self.cpu_demand = cpu_demand
        self.memory_demand = memory_demand

        # Service state
        self.state = state

        # Server that hosts the service（部署服务器）
        self.server = None

        # Application to whom the service belongs （关联应用）
        self.application = None

        # List of users that access the service
        self.users = []

        # Service availability and provisioning status
        self._available = False  # Service is not available, for example, when its state is being transferred
        self.being_provisioned = False

        # List that stores metadata about each migration experienced by the service throughout the simulation
        self.__migrations = []
```



provision函数：实现服务到目标服务器的部署和迁移

其中**一个应用由多个服务组成，每个服务对应一个容器镜像，又由多个容器层组成**

```python
    def provision(self, target_server: object):
        """Starts the service's provisioning process. This process comprises both placement and migration. In the former, the
        service is not initially hosted by any server within the infrastructure. In the latter, the service is already being
        hosted by a server and we want to relocate it to another server within the infrastructure.

        Args:
            target_server (object): Target server.
        """
        # Gathering layers present in the target server (layers, download_queue, waiting_queue)
        layers_downloaded = [layer for layer in target_server.container_layers]
        layers_on_download_queue = [flow.metadata["object"] for flow in target_server.download_queue]
        layers_on_waiting_queue = [layer for layer in target_server.waiting_queue]

        layers_on_target_server = layers_downloaded + layers_on_download_queue + layers_on_waiting_queue

        # Gathering the list of layers that compose the service image that are not present in the target server
        # 服务镜像层缺失检查与下载请求生成
        image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)
        for layer_digest in image.layers_digests:
            if not any(layer.digest == layer_digest for layer in layers_on_target_server):
                # As the image only stores its layers digests, we need to get information about each of its layers
                layer_metadata = ContainerLayer.find_by(attribute_name="digest", attribute_value=layer_digest)

                # Creating a new layer object that will be pulled to the target server
                layer = ContainerLayer(
                    digest=layer_metadata.digest,
                    size=layer_metadata.size,
                    instruction=layer_metadata.instruction,
                )
                self.model.initialize_agent(agent=layer)

                # Reserving the layer disk demand inside the target server
                target_server.disk_demand += layer.size

                # Adding the layer to the target server's waiting queue (layers it must download at some point)
                target_server.waiting_queue.append(layer)

        # Telling EdgeSimPy that this service is being provisioned
        self.being_provisioned = True

        # Telling EdgeSimPy the service's current server is now performing a migration. This action is only triggered in case
        # this method is called for performing a migration (i.e., the service is already within the infrastructure)
        if self.server:
            self.server.ongoing_migrations += 1

        # Reserving the service demand inside the target server and telling EdgeSimPy that server will receive a service
        target_server.ongoing_migrations += 1
        target_server.cpu_demand += self.cpu_demand
        target_server.memory_demand += self.memory_demand

        # Updating the service's migration status
        self._Service__migrations.append(
            {
                "status": "waiting",
                "origin": self.server,
                "target": target_server,
                "start": self.model.schedule.steps + 1,
                "end": None,
                "waiting_time": 0,
                "pulling_layers_time": 0,
                "migrating_service_state_time": 0,
            }
        )
```

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/45416683/1769161887812-304e814f-fcbe-4343-b31e-868cf58cb494.png)

与EdgeServer的交互流程：

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/45416683/1769162025377-d23ceaed-5b9c-4f32-a23d-bc83ab7f3e69.png)



step函数：

<font style="color:rgb(6, 10, 38);">负责处理服务在边缘服务器间的动态迁移（包括服务放置和迁移）。它实现了</font>**迁移状态机**<font style="color:rgb(6, 10, 38);">，监控服务迁移的每个阶段（等待、下载层、迁移状态、完成），并协调与网络流、资源管理、用户通信的交互。</font>

<font style="color:rgb(6, 10, 38);"></font>

```python
def step(self):
        """Method that executes the events involving the object at each time step."""
        ##检查是否有最近的迁移
        if len(self._Service__migrations) > 0 and self._Service__migrations[-1]["end"] == None:
            migration = self._Service__migrations[-1]

            # Gathering information about the service's image
            ##服务镜像层状态检查
            image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)

            # Gathering layers present in the target server (layers, download_queue, waiting_queue)
            layers_downloaded = [l for l in migration["target"].container_layers if l.digest in image.layers_digests]
            layers_on_download_queue = [
                flow.metadata["object"]
                for flow in migration["target"].download_queue
                if flow.metadata["object"].digest in image.layers_digests
            ]

            # Setting the migration status to "pulling_layers" once any of the service layers start being downloaded
            if migration["status"] == "waiting":
                layers_on_target_server = layers_downloaded + layers_on_download_queue

                if len(layers_on_target_server) > 0:
                    migration["status"] = "pulling_layers"

            if migration["status"] == "pulling_layers" and len(image.layers_digests) == len(layers_downloaded):
                # Once all the layers that compose the service's image are pulled, the service container is deprovisioned on its
                # origin host even though it still is in there (that's why it is still on the origin's services list). This action
                # is only taken in case the current provisioning process regards a migration.
                if self.server:
                    self.server.cpu_demand -= self.cpu_demand
                    self.server.memory_demand -= self.memory_demand

                # Once all service layers have been pulled, creates a ContainerImage object representing
                # the service image on the target host if that host didn't already have such image
                if not any([image.digest == self.image_digest for image in migration["target"].container_images]):
                    # Finding similar image provisioned on the infrastructure to get metadata from it when creating the new image
                    template_image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)
                    if template_image is None:
                        raise Exception(f"Could not find any container image with digest: {self.image_digest}")

                    # Creating the new image on the target host
                    image = ContainerImage()
                    image.name = template_image.name
                    image.digest = template_image.digest
                    image.tag = template_image.tag
                    image.architecture = template_image.architecture
                    image.layers_digests = template_image.layers_digests

                    # Connecting the new image to the target host
                    image.server = migration["target"]
                    migration["target"].container_images.append(image)

                if self.state == 0 or self.server == None:
                    # Stateless Services: migration is set to finished immediately after layers are pulled
                    migration["status"] = "finished"
                else:
                    # Stateful Services: state must be migrated to the target host after layers are pulled
                    migration["status"] = "migrating_service_state"

                    # Services are unavailable during the period where their states are being migrated
                    self._available = False

                    # Selecting the path that will be used to transfer the service state
                    path = nx.shortest_path(
                        G=self.model.topology,
                        source=self.server.base_station.network_switch,
                        target=migration["target"].base_station.network_switch,
                    )

                    # Creating network flow representing the service state that will be migrated to its target host
                    flow = NetworkFlow(
                        topology=self.model.topology,
                        source=self.server,
                        target=migration["target"],
                        start=self.model.schedule.steps + 1,
                        path=path,
                        data_to_transfer=self.state,
                        metadata={"type": "service_state", "object": self},
                    )
                    self.model.initialize_agent(agent=flow)

            # Incrementing the migration time metadata
            if migration["status"] == "waiting":
                migration["waiting_time"] += 1
            elif migration["status"] == "pulling_layers":
                migration["pulling_layers_time"] += 1
            elif migration["status"] == "migrating_service_state":
                migration["migrating_service_state_time"] += 1

            if migration["status"] == "finished":
                # Storing when the migration has finished
                migration["end"] = self.model.schedule.steps + 1

                # Updating the service's origin server metadata
                if self.server:
                    self.server.services.remove(self)
                    self.server.ongoing_migrations -= 1

                # Updating the service's target server metadata
                self.server = migration["target"]
                self.server.services.append(self)
                self.server.ongoing_migrations -= 1

                # Tagging the service as available once their migrations finish
                self._available = True
                self.being_provisioned = False

                # Changing the routes used to communicate the application that owns the service to its users
                app = self.application
                users = app.users
                for user in users:
                    user.set_communication_path(app)
```

step流程和状态转移图：

![画板](https://cdn.nlark.com/yuque/0/2026/jpeg/45416683/1769244706016-2964bd23-9a21-430d-aaed-3147411f7f48.jpeg)



### 改进思路
1.对于用户

（1）将用户访问的每个应用只关联到一个服务，既一个应用对应一个服务，当服务传输完成可用时应用即可用

用户对每个服务维护一个应用属性列表，表示在什么时刻产生应用以及应用的状态

（2）同时，去除用户移动性，只要coordinates_trace列表为空即代表用户不移动

（3）仍旧保持用户关联到最近的基站，基站作为其接入网关

属性扩展：





step修改：





2.对于应用和服务

应用与服务一一对应绑定：通过修改connect_to_service函数





3.对于边缘服务器

维持原先的等待队列逻辑，

但是等待队列中维护的不再是服务所需的容器层，而是服务本身。

对于等待队列中的每个服务直接创建相应的网络流，（_**metadata中的"type"属性为"service"**_）

同时，扩充其资源属性，包括：

CPU/GPU算力，SSD，RAM，以及带宽资源的总量

每类计算芯片的计算能力，PCIE总线能力

各类资源的使用量

各类资源当前利用率



属性修改：



step修改：



4.对于网络链路

扩充属性：

链路长度、链路传输速率、

带宽（作为相邻交换机的接口带宽）



修改时延属性的计算：







5.对于交换机

扩充属性：

与链路相关联的队列长度、队列长度阈值、丢包率

（关键在于如何与对应链路关联起来）



step修改：



6.对于网络流

修改step函数，当流的类型为“service"时，标记流量完成并从目标服务器的下载队列中移除，、

然后将对应服务与目标服务器相关联



7.对于拓扑（特别是其中最短路径算法的参数和计算）

最短路径算法





8.资源匹配算法



















