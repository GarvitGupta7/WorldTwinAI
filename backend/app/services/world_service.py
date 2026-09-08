import hashlib,json
from app.core.errors import ResourceNotFoundError,StateConsistencyError
from app.models import Entity,EntityType,WorldState
from app.db.models import World,Entity as E,Relationship
from app.world import create_seed_world
class WorldService:
 def __init__(self,repo): self.repo=repo
 def ensure(self,seed=42):
  w=self.repo.get("world-campus")
  if w:return w
  state=create_seed_world(seed); w=World(id="world-campus",name="Campus Living Twin",world_type="campus",description="A simulated university campus world.",current_timestamp=0); self.repo.db.add(w)
  for e in state.entities.values(): self.repo.db.add(E(id=e.id,world_id=w.id,entity_type=e.entity_type.value,name=e.name,x=e.x,y=e.y,state_json=e.state,attributes_json=e.attributes,relationships_json=e.relationships,source="seed",freshness_status="fresh",confidence=1))
  for e in state.entities.values():
   for target in e.relationships:
    if target in state.entities:self.repo.db.add(Relationship(world_id=w.id,source_entity_id=e.id,target_entity_id=target,relationship_type="linked_to",attributes_json={}))
  self.repo.db.commit(); return w
 def get(self,i="world-campus"):
  x=self.repo.get(i)
  if not x:raise ResourceNotFoundError("The requested world was not found.")
  return x
 def state(self,i="world-campus"):
  w=self.get(i); es={}
  for x in self.repo.entities(i):es[x.id]=Entity(x.id,x.name,EntityType(x.entity_type),x.x,x.y,dict(x.state_json),dict(x.attributes_json),list(x.relationships_json))
  return WorldState(w.current_timestamp,es)
 @staticmethod
 def state_hash(s):
  payload={"timestamp":s.timestamp,"entities":{k:{"type":e.entity_type.value,"x":e.x,"y":e.y,"state":e.state,"attributes":e.attributes,"relationships":e.relationships} for k,e in sorted(s.entities.items())}}
  return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
 def validate(self,s):
  if not s.entities:raise StateConsistencyError("World state contains no entities.")
  return True
