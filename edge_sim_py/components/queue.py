""" Contains network-queue-related functionality."""

# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent


class Queue(ComponentManager,Agent):
    # Class attributes that allow this class to use helper methods from ComponentManager
    # 全局对象
    _instances = []
    _object_count = 0
    def __init__(self, obj_id:int = None, model:object= None,cache_len:int = 1000,threshold_len:int=1000,
                 qos:int=1,active:bool=True,network_switch:object=None,target:object=None)->object:
        """Creates a NetworkQueue object.

        Args:
            obj_id (int, optional): Object identifier.

        Returns:
            object: Created NetworkQueue object.
        """
        self.__class__._instances.append(self)
            # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id
        
        # max length
        self.cache_len = cache_len
        # current length
        self.qlen = 0
        #threshold length
        self.threshold_len = threshold_len
        # drop packet ration
        self.drop_ratio = 0
        # QOS level
        self.qos = qos

    
        #related NetworkSwitch
        self.network_switch = network_switch
        # related target NetworkSwitch or EdgeServer
        self.target = target
               
        # if active 
        self.active = active
        
        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = model
        self.unique_id = None   
        

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "active": self.active,
                "cache_len":self.cache_len,
                "current_len":self.qlen,
                "threshold":self.threshold_len,
                "drop_ratio":self.drop_ratio,
                "qoe":self.qos
            },
            "relationships": {
                "associated switch":self.network_switch,
                "target switch":self.target_switch,
            },
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        metrics = {
            "current_len": self.qlen,
            "drop_ratio": self.drop_ratio
        }
        return metrics
        
    def step(self):
        """Method that executes the events involving the object at each time step."""
        # 每隔一定时间导入队列参数
        
        pass
    
    #提供队列长度
    def get_Qlen(self):
        return self.qlen
    