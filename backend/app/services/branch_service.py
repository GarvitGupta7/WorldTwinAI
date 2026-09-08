import uuid
from app.core.errors import ResourceNotFoundError
from app.db.models import SimulationBranch
class BranchService:
 def __init__(self,repo,world,scenario):self.repo=repo;self.world=world;self.scenario=scenario
 def get(self,i):
  x=self.repo.get(i)
  if not x:raise ResourceNotFoundError("The requested branch was not found.")
  return x
 def list(self,w="world-campus"):return self.repo.list(w)
 def ensure_baseline(self,w="world-campus",seed=42,duration=60):
  x=self.repo.baseline(w)
  if x:return x
  s=self.world.state(w); x=SimulationBranch(id="baseline-campus",world_id=w,parent_branch_id=None,scenario_id=None,branch_type="baseline",name="Campus Baseline",seed=seed,duration_minutes=duration,status="ready",initial_state_hash=self.world.state_hash(s));self.repo.db.add(x);self.repo.db.commit();return x
 def create(self,sid,w="world-campus",seed=42,duration=60,name=None):
  b=self.ensure_baseline(w,seed,duration); s=self.world.state(w); x=SimulationBranch(id=f"branch-{uuid.uuid4().hex[:10]}",world_id=w,parent_branch_id=b.id,scenario_id=sid,branch_type="scenario",name=name or f"Scenario {sid}",seed=seed,duration_minutes=duration,status="created",initial_state_hash=self.world.state_hash(s));self.repo.db.add(x);self.repo.db.commit();return x
