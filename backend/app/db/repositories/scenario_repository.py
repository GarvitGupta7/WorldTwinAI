from sqlalchemy import select
from app.db.models import Scenario
class ScenarioRepository:
 def __init__(self,db): self.db=db
 def get(self,i): return self.db.get(Scenario,i)
 def list(self,w): return list(self.db.scalars(select(Scenario).where(Scenario.world_id==w).order_by(Scenario.created_at.desc())))
 def add(self,x): self.db.add(x); self.db.flush(); return x
