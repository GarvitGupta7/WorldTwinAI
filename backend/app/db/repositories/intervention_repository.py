from sqlalchemy import select
from app.db.models import Intervention,InterventionRun
class InterventionRepository:
 def __init__(self,db): self.db=db
 def add(self,x): self.db.add(x); self.db.flush(); return x
 def list(self,w): return list(self.db.scalars(select(Intervention).where(Intervention.world_id==w)))
 def add_run(self,x): self.db.add(x); self.db.flush(); return x
