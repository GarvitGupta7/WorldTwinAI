import uuid
from app.db.models import Report
from app.reports.generator import generate
class ReportService:
 def __init__(self,db,branches,sim):self.db=db;self.branches=branches;self.sim=sim
 def create(self,bid):
  b=self.branches.get(bid); metrics=self.sim.metrics(bid); final=metrics[-1].metrics_json if metrics else {}
  anomalies=[{"severity":x.severity,"explanation":x.evidence_json.get("explanation",x.anomaly_type)} for x in self.sim.anomalies(bid)]
  causal=[]
  for e in self.sim.events(bid):
   if e.event_type=="ROAD_CLOSED":causal+=['ROAD_CLOSED','ROUTE_CAPACITY_REDUCED','TRAFFIC_REROUTED']
  content=generate(f"Digital Twin Simulation Report — {b.name}",bid,final,causal,anomalies)
  row=Report(id=f"report-{uuid.uuid4().hex[:8]}",world_id=b.world_id,branch_id=bid,title=f"Simulation Report — {b.name}",content_markdown=content,content_json={"metrics":final,"anomalies":anomalies,"causal_chain":causal})
  self.db.add(row);self.db.commit();return row
