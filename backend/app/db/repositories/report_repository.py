from sqlalchemy import select
from app.db.models import Report
class ReportRepository:
 def __init__(self,db): self.db=db
 def add(self,x): self.db.add(x); self.db.flush(); return x
 def get(self,i): return self.db.get(Report,i)
 def list(self,w): return list(self.db.scalars(select(Report).where(Report.world_id==w).order_by(Report.created_at.desc())))
