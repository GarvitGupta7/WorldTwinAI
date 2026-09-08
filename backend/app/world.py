import random
from .models import Entity,EntityType,WorldState
def create_seed_world(seed=42):
 r=random.Random(seed); es={}
 buildings=[("building-library","Central Library",20,70,600),("building-science","Science Block",70,70,800),("building-academic","Academic Block",50,45,1000),("building-admin","Administration",25,25,400),("building-hostel","Student Residence",75,25,1200),("building-sports","Sports Complex",85,55,900)]
 for i,n,x,y,c in buildings: es[i]=Entity(i,n,EntityType.BUILDING,x,y,{"occupancy":int(c*.35),"operating":True},{"capacity":c},[])
 roads=[("road-main","Main Campus Road",50,50,1),("road-north","North Gate Road",50,72,.8),("road-east","East Connector",72,50,.7),("road-west","West Connector",28,50,.7),("road-south","South Gate Road",50,28,.9)]
 for i,n,x,y,c in roads: es[i]=Entity(i,n,EntityType.ROAD,x,y,{"blocked":False,"congestion":0.0,"capacity":c},{"base_capacity":c},[])
 for k in range(8): es[f"bus-{k+1}"]=Entity(f"bus-{k+1}",f"Campus Shuttle {k+1}",EntityType.BUS,10+k*10,50,{"delay_minutes":0.0,"occupancy":r.randint(15,35),"available":True,"speed":1.0},{"capacity":50,"route":"campus-loop"},[])
 for k in range(60):
  dest=r.choice(["building-library","building-science","building-academic","building-sports"])
  es[f"student-{k+1}"]=Entity(f"student-{k+1}",f"Student {k+1}",EntityType.STUDENT,r.uniform(15,85),r.uniform(15,85),{"destination":dest,"delay_minutes":0.0,"mode":r.choice(["walking","bus"]),"moving":True},{"arrival_wave":r.choice(["morning","midday","afternoon"])},[dest])
 es["event-tech-fair"]=Entity("event-tech-fair","Technology Fair",EntityType.EVENT,85,55,{"active":True,"attendance":450},{"start_minute":0,"end_minute":180},["building-sports"])
 return WorldState(0,es)
