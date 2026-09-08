from dataclasses import dataclass,field
from enum import StrEnum
from typing import Any
class EntityType(StrEnum): STUDENT="student"; BUS="bus"; BUILDING="building"; ROAD="road"; EVENT="event"; FACILITY="facility"; INCIDENT="incident"
@dataclass
class Entity:
 id:str; name:str; entity_type:EntityType; x:float; y:float; state:dict[str,Any]=field(default_factory=dict); attributes:dict[str,Any]=field(default_factory=dict); relationships:list[str]=field(default_factory=list)
@dataclass
class SimulationEvent:
 timestamp:int; event_type:str; entity_ids:list[str]; description:str; evidence:dict[str,Any]=field(default_factory=dict)
@dataclass
class WorldState:
 timestamp:int; entities:dict[str,Entity]; metrics:dict[str,float]=field(default_factory=dict); events:list[SimulationEvent]=field(default_factory=list)
 def clone(self):
  return WorldState(self.timestamp,{k:Entity(e.id,e.name,e.entity_type,e.x,e.y,dict(e.state),dict(e.attributes),list(e.relationships)) for k,e in self.entities.items()},dict(self.metrics),list(self.events))
