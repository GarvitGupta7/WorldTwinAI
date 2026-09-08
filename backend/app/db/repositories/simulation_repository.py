from sqlalchemy import select
from app.db.models import SimulationState,SimulationEvent,MetricSnapshot,Anomaly,Prediction
class SimulationRepository:
 def __init__(self,db): self.db=db
 def add(self,x): self.db.add(x)
 def states(self,b): return list(self.db.scalars(select(SimulationState).where(SimulationState.branch_id==b).order_by(SimulationState.timestamp)))
 def events(self,b): return list(self.db.scalars(select(SimulationEvent).where(SimulationEvent.branch_id==b).order_by(SimulationEvent.timestamp)))
 def metrics(self,b): return list(self.db.scalars(select(MetricSnapshot).where(MetricSnapshot.branch_id==b).order_by(MetricSnapshot.timestamp)))
 def anomalies(self,b): return list(self.db.scalars(select(Anomaly).where(Anomaly.branch_id==b).order_by(Anomaly.timestamp)))
 def predictions(self,b): return list(self.db.scalars(select(Prediction).where(Prediction.branch_id==b).order_by(Prediction.timestamp)))
