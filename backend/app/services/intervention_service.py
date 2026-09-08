import copy,uuid
from app.db.models import Intervention,InterventionRun
from app.analytics.interventions import candidate_interventions
from app.core.errors import ResourceNotFoundError
class InterventionService:
 def __init__(self,db,world,branches,sim_repo): self.db=db;self.world=world;self.branches=branches;self.sim_repo=sim_repo
 def evaluate(self,branch_id):
  source=self.branches.get(branch_id); state=self.world.state(source.world_id); baseline=self.sim_repo.metrics(branch_id); base=baseline[-1].metrics_json if baseline else {}
  results=[]
  for spec in candidate_interventions():
   score=self._score(spec,base)
   row=Intervention(id=f"int-{uuid.uuid4().hex[:8]}",world_id=source.world_id,scenario_id=source.scenario_id,name=spec["name"],description=spec["description"],parameters_json=spec["parameters"],operational_cost=spec["operational_cost"],safety_score=spec["safety_score"],complexity_score=spec["complexity_score"])
   self.db.add(row);self.db.flush();results.append({"intervention_id":row.id,"name":row.name,"score":score,"score_breakdown":{"operational_cost":row.operational_cost,"safety":row.safety_score,"complexity":row.complexity_score},"description":row.description})
  self.db.commit();return sorted(results,key=lambda x:x["score"],reverse=True)
 def _score(self,spec,metrics):
  delay=metrics.get("average_bus_delay",0); congestion=metrics.get("average_road_congestion",0)
  benefit=min(100,(delay*8+congestion*40)); penalty=spec["operational_cost"]*.4+spec["complexity_score"]*10
  return round(max(0,benefit+spec["safety_score"]*20-penalty),2)
