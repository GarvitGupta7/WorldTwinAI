from datetime import datetime,timezone
from app.core.errors import SimulationExecutionError
from app.db.models import SimulationState,SimulationEvent,MetricSnapshot,Anomaly,Prediction
from app.models import Entity,EntityType,WorldState,SimulationEvent as DomainEvent
from app.simulation import apply,advance,metrics,anomalies
from app.schemas import ScenarioResponse,ScenarioParameter

class SimulationService:
 def __init__(self,repo,branch_repo,scenario_repo,world,branches): self.repo=repo;self.br=branch_repo;self.sr=scenario_repo;self.world=world;self.branches=branches
 def _state_from_branch(self,b):
  snaps=self.repo.states(b.id)
  if not snaps: return self.world.state(b.world_id)
  raw=snaps[-1].state_json; entities={}
  for k,e in raw.get('entities',{}).items():
   entities[k]=Entity(k,e['name'],EntityType(e['entity_type']),float(e['x']),float(e['y']),dict(e.get('state',{})),dict(e.get('attributes',{})),list(e.get('relationships',[])))
  return WorldState(int(raw.get('timestamp',snaps[-1].timestamp)),entities)
 def run(self,bid,scenario_override=None):
  b=self.branches.get(bid)
  s=self._state_from_branch(b)
  scenario=None if scenario_override is None else scenario_override
  if scenario is None and b.scenario_id:
   row=self.sr.get(b.scenario_id); scenario=ScenarioResponse(scenario_id=row.id,original_text=row.original_text,action=row.action,parameters=[ScenarioParameter(**q) for q in row.parameters_json],assumptions=row.assumptions_json,ambiguities=row.ambiguities_json,valid=row.valid)
  causal=[]
  if scenario: causal=apply(s,scenario)
  try: s,timeline=advance(s,b.duration_minutes,b.seed,collect_interval=5)
  except Exception as e: raise SimulationExecutionError('Simulation execution failed.') from e
  for snap in timeline:
   self.repo.add(SimulationState(branch_id=b.id,timestamp=snap.timestamp,state_json=self.serialize(snap),state_hash=self.world.state_hash(snap)))
   self.repo.add(MetricSnapshot(branch_id=b.id,timestamp=snap.timestamp,metrics_json=snap.metrics))
  for e in s.events:self.repo.add(SimulationEvent(branch_id=b.id,timestamp=e.timestamp,event_type=e.event_type,entity_ids_json=e.entity_ids,description=e.description,evidence_json=e.evidence))
  aa=anomalies(s.metrics)
  for a in aa:self.repo.add(Anomaly(branch_id=b.id,timestamp=s.timestamp,anomaly_type=a['type'],severity=a['severity'],metric=a['metric'],observed_value=a['observed_value'],expected_value=0,deviation=a['observed_value'],affected_entity_ids_json=[],evidence_json=a,confidence=.9))
  snaps=self.repo.metrics(b.id); prev=snaps[-2].metrics_json if len(snaps)>1 else s.metrics; last=snaps[-1].metrics_json if snaps else s.metrics
  for metric,val in last.items():
   delta=float(val)-float(prev.get(metric,val)); forecast=max(0.0,float(val)+delta*3)
   self.repo.add(Prediction(branch_id=b.id,timestamp=s.timestamp,horizon_minutes=15,metric=metric,predicted_value=forecast,confidence=.62,model_name='linear_trend_v1',feature_evidence_json={'source':'last_two_metric_snapshots','delta':delta},limitations_json=['Lightweight deterministic trend model; requires real historical data for calibrated forecasting.']))
  b.status='completed';b.completed_at=datetime.now(timezone.utc);self.repo.db.commit();return b,s.metrics,aa,causal
 @staticmethod
 def serialize(s): return {'timestamp':s.timestamp,'entities':{k:{'id':e.id,'name':e.name,'entity_type':e.entity_type.value,'x':e.x,'y':e.y,'state':e.state,'attributes':e.attributes,'relationships':e.relationships} for k,e in sorted(s.entities.items())}}
 def get(self,bid,kind): self.branches.get(bid);return getattr(self.repo,kind)(bid)
 def metrics(self,bid): return self.get(bid,'metrics')
 def events(self,bid): return self.get(bid,'events')
 def anomalies(self,bid): return self.get(bid,'anomalies')
 def predictions(self,bid): return self.get(bid,'predictions')
 def timeline(self,bid): return self.get(bid,'states')
