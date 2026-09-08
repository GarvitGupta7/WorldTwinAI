from sqlalchemy import select
from app.db.models import SimulationBranch
class BranchRepository:
 def __init__(self,db): self.db=db
 def get(self,i): return self.db.get(SimulationBranch,i)
 def list(self,w): return list(self.db.scalars(select(SimulationBranch).where(SimulationBranch.world_id==w).order_by(SimulationBranch.created_at.desc())))
 def baseline(self,w): return self.db.scalar(select(SimulationBranch).where(SimulationBranch.world_id==w,SimulationBranch.branch_type=="baseline").order_by(SimulationBranch.created_at.asc()))
