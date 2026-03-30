""" Contains network-switch-related functionality."""
from edge_sim_py import NetworkSwitch
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent

# Python libraries
import copy


class CpnRouter(ComponentManager,Agent,NetworkSwitch):
    def __init__(self,obj_id: int = None,area_ID: int = None,model:object = None):
        NetworkSwitch.__init__(self,obj_id)
        self.area_ID = area_ID
        self.services = []

        self.model = model


    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "coordinates": self.coordinates,
                "active": self.active,
                "area_ID": self.area_ID,
            },
            "relationships": {
                "power_model": self.power_model.__name__ if self.power_model else None,
                "edge_servers": [
                    {"class": type(edge_server).__name__, "id": edge_server.id} for edge_server in self.edge_servers
                ],
                "links": [{"class": type(link).__name__, "id": link.id} for link in self.links],
                "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id}
                if self.base_station
                else None,
                "service": [{"class":type(service).__name__,'id':service.id}for service in self.services]
            },
        }
        return dictionary



    def step(self):
        #TODO：将当前任务列表中的任务放入调度器中
        self.model.cpn_scheduler.schedule_services.append(self.services)
        # 清空任务队列
        self.services = []
