from app.core.errors import ResourceNotFoundError,ScenarioValidationError
from app.db.models import Scenario
from app.scenario import parse_scenario
class ScenarioService:
 def __init__(self,repo):self.repo=repo
 def parse(self,req):return parse_scenario(req)
 def create(self,p,world="world-campus"):
  if not p.valid:raise ScenarioValidationError("Scenario is not valid.",{"ambiguities":p.ambiguities})
  x=Scenario(id=p.scenario_id,world_id=world,original_text=p.original_text,action=p.action,parameters_json=[q.model_dump() for q in p.parameters],assumptions_json=p.assumptions,ambiguities_json=p.ambiguities,valid=p.valid,parser_name="deterministic_parser",parser_version="1.0"); self.repo.add(x);self.repo.db.commit();return x
 def get(self,i):
  x=self.repo.get(i)
  if not x:raise ResourceNotFoundError("The requested scenario was not found.")
  return x
 def list(self,w="world-campus"):return self.repo.list(w)
