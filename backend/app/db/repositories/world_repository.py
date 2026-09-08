from sqlalchemy import select
from app.db.models import World,Entity,Relationship
class WorldRepository:
 def __init__(self,db): self.db=db
 def get(self,i): return self.db.get(World,i)
 def entities(self,w): return list(self.db.scalars(select(Entity).where(Entity.world_id==w)))
 def entity(self,w,i): return self.db.scalar(select(Entity).where(Entity.world_id==w,Entity.id==i))
 def relationships(self,w): return list(self.db.scalars(select(Relationship).where(Relationship.world_id==w)))
