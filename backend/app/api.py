from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.errors import AppError
from app.db.repositories.world_repository import WorldRepository
from app.db.repositories.scenario_repository import ScenarioRepository
from app.db.repositories.branch_repository import BranchRepository
from app.db.repositories.simulation_repository import SimulationRepository
from app.services.world_service import WorldService
from app.services.scenario_service import ScenarioService
from app.services.branch_service import BranchService
from app.services.simulation_service import SimulationService
from app.ai.copilot import Copilot
from app.ai.rag import LocalRAG
from app.services.intervention_service import InterventionService
from app.services.report_service import ReportService
from app.db.repositories.intervention_repository import InterventionRepository
from app.schemas import *
router=APIRouter(prefix="/api")
def svc(db):
 w=WorldService(WorldRepository(db)); w.ensure(); s=ScenarioService(ScenarioRepository(db)); b=BranchService(BranchRepository(db),w,s); sim=SimulationService(SimulationRepository(db),BranchRepository(db),ScenarioRepository(db),w,b); return w,s,b,sim
def br(x):return BranchResponse(id=x.id,world_id=x.world_id,parent_branch_id=x.parent_branch_id,scenario_id=x.scenario_id,branch_type=x.branch_type,name=x.name,seed=x.seed,duration_minutes=x.duration_minutes,status=x.status,initial_state_hash=x.initial_state_hash,created_at=x.created_at.isoformat(),completed_at=x.completed_at.isoformat() if x.completed_at else None)
@router.get('/health')
def health(db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); base=b.ensure_baseline(); return {"status":"ok","database":"ok","world":"ok","baseline_branch":"ok" if base else "degraded","mode":"local-deterministic"}
@router.get('/world',response_model=WorldSummary)
def world(db:Session=Depends(get_db)):
 w,_,_,_=svc(db); x=w.get();return WorldSummary(id=x.id,name=x.name,world_type=x.world_type,description=x.description,current_timestamp=x.current_timestamp,entity_count=len(w.repo.entities(x.id)),relationship_count=len(w.repo.relationships(x.id)))
@router.get('/world/state')
def state(db:Session=Depends(get_db)):
 w,_,_,_=svc(db); s=w.state();return {"timestamp":s.timestamp,"state_hash":w.state_hash(s),"entities":[e.__dict__ for e in s.entities.values()]}
@router.get('/world/entities',response_model=list[EntityResponse])
def entities(db:Session=Depends(get_db)):
 w,_,_,_=svc(db);return [EntityResponse(id=e.id,name=e.name,entity_type=e.entity_type,x=e.x,y=e.y,state=e.state_json,attributes=e.attributes_json,relationships=e.relationships_json,source=e.source,freshness_status=e.freshness_status,confidence=e.confidence) for e in w.repo.entities('world-campus')]
@router.get('/world/entities/{eid}',response_model=EntityResponse)
def entity(eid,db:Session=Depends(get_db)):
 w,_,_,_=svc(db);e=w.repo.entity('world-campus',eid)
 if not e:from app.core.errors import ResourceNotFoundError;raise ResourceNotFoundError('The requested entity was not found.')
 return EntityResponse(id=e.id,name=e.name,entity_type=e.entity_type,x=e.x,y=e.y,state=e.state_json,attributes=e.attributes_json,relationships=e.relationships_json,source=e.source,freshness_status=e.freshness_status,confidence=e.confidence)
@router.get('/world/relationships',response_model=list[RelationshipResponse])
def rels(db:Session=Depends(get_db)):
 w,_,_,_=svc(db);return [RelationshipResponse(id=r.id,world_id=r.world_id,source_entity_id=r.source_entity_id,target_entity_id=r.target_entity_id,relationship_type=r.relationship_type,attributes=r.attributes_json) for r in w.repo.relationships('world-campus')]
@router.post('/scenarios/parse',response_model=ScenarioResponse)
def parse(req:ScenarioRequest,db:Session=Depends(get_db)):
 return svc(db)[1].parse(req)
@router.post('/scenarios',response_model=ScenarioResponse)
def create(req:ScenarioCreateRequest,db:Session=Depends(get_db)):
 r=svc(db)[1].create(req.scenario);return ScenarioResponse(scenario_id=r.id,original_text=r.original_text,action=r.action,parameters=r.parameters_json,assumptions=r.assumptions_json,ambiguities=r.ambiguities_json,valid=r.valid)
@router.get('/scenarios',response_model=list[ScenarioResponse])
def slist(db:Session=Depends(get_db)):
 return [ScenarioResponse(scenario_id=r.id,original_text=r.original_text,action=r.action,parameters=r.parameters_json,assumptions=r.assumptions_json,ambiguities=r.ambiguities_json,valid=r.valid) for r in svc(db)[1].list()]
@router.get('/scenarios/{sid}',response_model=ScenarioResponse)
def sdetail(sid,db:Session=Depends(get_db)):
 r=svc(db)[1].get(sid);return ScenarioResponse(scenario_id=r.id,original_text=r.original_text,action=r.action,parameters=r.parameters_json,assumptions=r.assumptions_json,ambiguities=r.ambiguities_json,valid=r.valid)
@router.post('/branches',response_model=BranchResponse)
def bcreate(req:BranchCreateRequest,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db);s.get(req.scenario_id);return br(b.create(req.scenario_id,req.world_id,req.seed,req.duration_minutes,req.name))
@router.get('/branches',response_model=list[BranchResponse])
def blist(db:Session=Depends(get_db)):return [br(x) for x in svc(db)[2].list()]
@router.get('/branches/{bid}',response_model=BranchResponse)
def bdetail(bid,db:Session=Depends(get_db)):return br(svc(db)[2].get(bid))
@router.post('/simulations/{bid}/run')
def run(bid,db:Session=Depends(get_db)):
 b,met,aa,causal=svc(db)[3].run(bid);return {"branch":br(b),"metrics":met,"anomalies":aa,"causal_chain":causal}
@router.get('/branches/{bid}/timeline',response_model=list[TimelineStateResponse])
def timeline(bid,db:Session=Depends(get_db)):
 return [TimelineStateResponse(timestamp=x.timestamp,state=x.state_json,state_hash=x.state_hash) for x in svc(db)[3].get(bid,'states')]
@router.get('/branches/{bid}/metrics',response_model=list[MetricSnapshotResponse])
def mtr(bid,db:Session=Depends(get_db)):return [MetricSnapshotResponse(timestamp=x.timestamp,metrics=x.metrics_json) for x in svc(db)[3].get(bid,'metrics')]
@router.get('/branches/{bid}/events',response_model=list[SimulationEventResponse])
def ev(bid,db:Session=Depends(get_db)):return [SimulationEventResponse(timestamp=x.timestamp,event_type=x.event_type,entity_ids=x.entity_ids_json,description=x.description,evidence=x.evidence_json) for x in svc(db)[3].get(bid,'events')]
@router.get('/branches/{bid}/anomalies',response_model=list[AnomalyResponse])
def an(bid,db:Session=Depends(get_db)):return [AnomalyResponse(timestamp=x.timestamp,anomaly_type=x.anomaly_type,severity=x.severity,metric=x.metric,observed_value=x.observed_value,expected_value=x.expected_value,deviation=x.deviation,affected_entity_ids=x.affected_entity_ids_json,evidence=x.evidence_json,confidence=x.confidence) for x in svc(db)[3].get(bid,'anomalies')]
@router.get('/branches/{bid}/predictions',response_model=list[PredictionResponse])
def pred(bid,db:Session=Depends(get_db)):return [PredictionResponse(timestamp=x.timestamp,horizon_minutes=x.horizon_minutes,metric=x.metric,predicted_value=x.predicted_value,confidence=x.confidence,model_name=x.model_name,feature_evidence=x.feature_evidence_json,limitations=x.limitations_json) for x in svc(db)[3].get(bid,'predictions')]
@router.post('/copilot',response_model=CopilotResponse)
def cop(req:CopilotRequest,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db);return Copilot(w,b,sim).answer(req.message,req.branch_id)


@router.get('/dashboard')
def dashboard(db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); branches=b.list(); latest=[]
 for row in branches:
  ms=sim.metrics(row.id); aa=sim.anomalies(row.id)
  latest.append({'branch_id':row.id,'name':row.name,'status':row.status,'branch_type':row.branch_type,'latest_metrics':ms[-1].metrics_json if ms else {},'anomaly_count':len(aa),'duration_minutes':row.duration_minutes})
 return {'world':WorldSummary(id=w.get().id,name=w.get().name,world_type=w.get().world_type,description=w.get().description,current_timestamp=w.get().current_timestamp,entity_count=len(w.repo.entities(w.get().id)),relationship_count=len(w.repo.relationships(w.get().id))),'branches':latest,'entity_type_counts':{t:sum(1 for e in w.repo.entities(w.get().id) if e.entity_type==t) for t in sorted(set(e.entity_type for e in w.repo.entities(w.get().id)))}}

@router.get('/branches/{bid}/summary')
def branch_summary(bid,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); row=b.get(bid); ms=sim.metrics(bid); tl=sim.timeline(bid); ev=sim.events(bid); aa=sim.anomalies(bid); pp=sim.predictions(bid)
 return {'branch':br(row),'latest_metrics':ms[-1].metrics_json if ms else {},'previous_metrics':ms[-2].metrics_json if len(ms)>1 else {},'timeline_points':len(tl),'events':len(ev),'anomalies':len(aa),'predictions':len(pp),'state_hash':tl[-1].state_hash if tl else row.initial_state_hash}

@router.post('/branches/compare')
def compare(payload:dict,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); ids=payload.get('branch_ids',[])
 if len(ids)<2: return {"error":{"code":"INVALID_COMPARISON","message":"Provide at least two branch_ids.","details":{}}}
 out=[]
 for bid in ids:
  row=b.get(bid); ms=sim.metrics(bid); out.append({"branch_id":bid,"name":row.name,"metrics":ms[-1].metrics_json if ms else {}})
 return {"branches":out}
@router.post('/branches/{bid}/interventions/evaluate')
def interventions(bid,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); b.get(bid); return {"branch_id":bid,"recommendations":InterventionService(db,w,b,sim.repo).evaluate(bid)}
@router.post('/branches/{bid}/report')
def report(bid,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); r=ReportService(db,b,sim); x=r.create(bid); return {"id":x.id,"title":x.title,"content_markdown":x.content_markdown,"content":x.content_json}
@router.get('/reports')
def reports(db:Session=Depends(get_db)):
 from app.db.models import Report
 from sqlalchemy import select
 rows=list(db.scalars(select(Report).order_by(Report.created_at.desc())))
 return [{'id':x.id,'title':x.title,'branch_id':x.branch_id,'content_markdown':x.content_markdown,'created_at':x.created_at.isoformat()} for x in rows]

@router.get('/reports/{report_id}')
def report_get(report_id,db:Session=Depends(get_db)):
 from app.db.repositories.report_repository import ReportRepository
 x=ReportRepository(db).get(report_id)
 if not x: from app.core.errors import ResourceNotFoundError; raise ResourceNotFoundError('The requested report was not found.')
 return {"id":x.id,"title":x.title,"branch_id":x.branch_id,"content_markdown":x.content_markdown,"content":x.content_json}
@router.post('/knowledge/ingest')
def knowledge_ingest():
 r=LocalRAG(__import__('pathlib').Path(__file__).resolve().parents[3] / 'knowledge'); return {"documents_indexed":r.ingest()}
@router.post('/knowledge/search')
def knowledge_search(payload:dict):
 r=LocalRAG(__import__('pathlib').Path(__file__).resolve().parents[3] / 'knowledge'); return {"results":r.search(payload.get('query',''),payload.get('k',4))}
@router.post('/experiments/run')
def experiment(payload:dict,db:Session=Depends(get_db)):
 w,s,b,sim=svc(db); texts=payload.get('scenarios',[]); results=[]
 for text in texts:
  parsed=s.parse(ScenarioRequest(text=text,seed=payload.get('seed',42),duration_minutes=payload.get('duration_minutes',60)))
  if not parsed.valid: continue
  row=s.create(parsed); branch=b.create(row.id,seed=payload.get('seed',42),duration=payload.get('duration_minutes',60)); _,m,a,c=sim.run(branch.id); results.append({"branch_id":branch.id,"scenario":text,"metrics":m,"anomalies":a,"causal_chain":c})
 return {"experiment_id":"exp-"+__import__('uuid').uuid4().hex[:8],"results":results}
