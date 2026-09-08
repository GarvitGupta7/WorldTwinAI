class Copilot:
 def __init__(self,world,branches,sim):self.world=world;self.branches=branches;self.sim=sim
 def answer(self,message,branch_id=None):
  m=message.lower(); evidence=[]
  if "why" in m or "congestion" in m:
   if branch_id:
    ev=self.sim.get(branch_id,"events"); evidence=[{"type":e.event_type,"timestamp":e.timestamp,"description":e.description} for e in ev[-5:]]
   return {"answer":"The twin attributes disruption to interacting world-state changes. Inspect the causal chain and simulation events for the selected branch.","intent":"explain","evidence":evidence,"actions":[{"type":"open_branch","branch_id":branch_id}] if branch_id else []}
  if "world" in m or "happening" in m:
   w=self.world.get(); return {"answer":f"The campus twin contains {len(self.world.repo.entities(w.id))} modeled entities and {len(self.world.repo.relationships(w.id))} relationships.","intent":"world_status","evidence":[{"world_id":w.id}],"actions":[]}
  return {"answer":"I can inspect the twin, explain branch outcomes, and guide scenario analysis. Try: 'What's happening?', 'Why is congestion high?', or select a simulation branch and ask for an explanation.","intent":"help","evidence":[],"actions":[]}
