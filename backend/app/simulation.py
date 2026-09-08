import random
from .models import EntityType,SimulationEvent,WorldState
def param(s,n,d=None):
 for p in s.parameters:
  if p.name==n:return p.value
 return d
def metrics(w):
 bs=[e for e in w.entities.values() if e.entity_type==EntityType.BUS]; rs=[e for e in w.entities.values() if e.entity_type==EntityType.ROAD]; ss=[e for e in w.entities.values() if e.entity_type==EntityType.STUDENT]; bl=[e for e in w.entities.values() if e.entity_type==EntityType.BUILDING]
 return {"average_bus_delay":round(sum(e.state["delay_minutes"] for e in bs)/len(bs),3),"bus_utilization":round(sum(e.state["occupancy"]/e.attributes["capacity"] for e in bs)/len(bs),3),"average_road_congestion":round(sum(e.state["congestion"] for e in rs)/len(rs),3),"average_building_occupancy":round(sum(e.state["occupancy"]/max(e.attributes["capacity"],1) for e in bl)/len(bl),3),"delayed_students":float(sum(e.state["delay_minutes"]>5 for e in ss)),"active_entities":float(len(w.entities))}
def apply(w,s):
 chain=[]
 if s.action=="modify_bus_availability":
  buses=[e for e in w.entities.values() if e.entity_type==EntityType.BUS]; n=round(len(buses)*float(param(s,"bus_availability_reduction",40))/100)
  for e in buses[:n]: e.state["available"]=False; e.state["occupancy"]=0
  chain=["BUS_AVAILABILITY_REDUCED","STUDENT_TRANSPORT_CAPACITY_REDUCED","BUS_DEMAND_CONCENTRATED"]
  if param(s,"major_event_active",False): w.entities["event-tech-fair"].state["attendance"]*=1.25; chain.append("MAJOR_EVENT_DEMAND_INCREASED")
 elif s.action=="close_road":
  rid=str(param(s,"road_id","road-main")); e=w.entities.get(rid)
  if e: e.state.update(blocked=True,capacity=0.0); w.events.append(SimulationEvent(0,"ROAD_CLOSED",[rid],f"{e.name} was closed.",{"duration_minutes":param(s,"duration_minutes",30)})); chain=["ROAD_CLOSED","ROUTE_CAPACITY_REDUCED","TRAFFIC_REROUTED"]
 elif s.action=="reduce_facility_capacity":
  e=w.entities.get(str(param(s,"facility_id","building-library"))); red=float(param(s,"capacity_reduction",30))
  if e: e.attributes["capacity"]*=1-red/100; chain=["FACILITY_CAPACITY_REDUCED","FACILITY_UTILIZATION_INCREASED","DESTINATIONS_REDISTRIBUTED"]
 return chain
def advance(w,duration,seed,collect_interval=5):
 rng=random.Random(seed)
 timeline=[]
 for minute in range(duration):
  w.timestamp+=1; buses=[e for e in w.entities.values() if e.entity_type==EntityType.BUS]; roads=[e for e in w.entities.values() if e.entity_type==EntityType.ROAD]; students=[e for e in w.entities.values() if e.entity_type==EntityType.STUDENT]
  available=[e for e in buses if e.state["available"]]
  for road in roads: road.state["congestion"]=1.0 if road.state["blocked"] else min(1,max(0,len(students)/max(len(roads),1)/35+rng.uniform(-.04,.04)))
  pressure=sum(e.state["congestion"] for e in roads)/len(roads)
  for bus in buses:
   if bus.state["available"]: bus.state["occupancy"]=min(bus.attributes["capacity"],max(0,int(bus.state["occupancy"]+rng.randint(-2,4)+pressure*8))); bus.state["delay_minutes"]=max(0,bus.state["delay_minutes"]+pressure*.4+rng.uniform(-.2,.5))
  for s in students: s.state["delay_minutes"]+=1 if s.state["mode"]=="bus" and not available else rng.uniform(-.2,.4); s.state["delay_minutes"]=max(0,s.state["delay_minutes"])
  if minute%10==0:w.events.append(SimulationEvent(w.timestamp,"WORLD_OBSERVATION",[],"Periodic world observation recorded.",{"available_buses":len(available)}))
  if (minute+1)%collect_interval==0 or minute==duration-1:
   w.metrics=metrics(w); timeline.append(w.clone())
 w.metrics=metrics(w); return w,timeline
def anomalies(m):
 a=[]
 if m["average_bus_delay"]>3:a.append({"type":"transport_delay","severity":"high","metric":"average_bus_delay","observed_value":m["average_bus_delay"],"explanation":"Average bus delay exceeded the modeled threshold."})
 if m["average_road_congestion"]>.65:a.append({"type":"road_congestion","severity":"high","metric":"average_road_congestion","observed_value":m["average_road_congestion"],"explanation":"Road congestion exceeded the modeled threshold."})
 if m["delayed_students"]>10:a.append({"type":"student_delay","severity":"medium","metric":"delayed_students","observed_value":m["delayed_students"],"explanation":"A significant number of students experienced delays."})
 return a
