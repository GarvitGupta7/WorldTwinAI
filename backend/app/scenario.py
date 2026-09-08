import re,uuid
from .schemas import ScenarioParameter,ScenarioRequest,ScenarioResponse
def parse_scenario(req):
 t=req.text.lower(); ps=[]; assumptions=[]; ambiguities=[]; action="unknown"
 pct=re.search(r"(\d+)\s*%",t); dur=re.search(r"(\d+)\s*(?:minute|minutes|min)",t)
 if "bus" in t and any(w in t for w in ["reduction","reduced","unavailable","delay"]):
  action="modify_bus_availability"; v=int(pct.group(1)) if pct else 40
  ps.append(ScenarioParameter(name="bus_availability_reduction",value=v,unit="percent",source="deterministic_parser",confidence=.94 if pct else .72))
  if "morning" in t: ps.append(ScenarioParameter(name="time_window",value="morning_peak",source="deterministic_parser",confidence=.9))
  if "event" in t: ps.append(ScenarioParameter(name="major_event_active",value=True,source="deterministic_parser",confidence=.88))
 elif "close" in t or "block" in t:
  action="close_road"; road="road-main"
  for key in ["north","east","west","south"]:
   if key in t: road=f"road-{key}"
  if "main" not in t and road=="road-main": ambiguities.append("Affected road was not explicitly identified.")
  ps += [ScenarioParameter(name="road_id",value=road,source="deterministic_parser",confidence=.86),ScenarioParameter(name="duration_minutes",value=int(dur.group(1)) if dur else 30,unit="minutes",source="deterministic_parser",confidence=.9 if dur else .68)]
 elif "library" in t and "capacity" in t:
  action="reduce_facility_capacity"; v=int(pct.group(1)) if pct else 30
  ps += [ScenarioParameter(name="facility_id",value="building-library",source="deterministic_parser",confidence=.93),ScenarioParameter(name="capacity_reduction",value=v,unit="percent",source="deterministic_parser",confidence=.9 if pct else .7)]
 else: ambiguities.append("Request does not match a supported scenario pattern."); assumptions.append("An external LLM adapter can broaden scenario understanding.")
 return ScenarioResponse(scenario_id=f"scenario-{uuid.uuid4().hex[:10]}",original_text=req.text,action=action,parameters=ps,assumptions=assumptions,ambiguities=ambiguities,valid=action!="unknown" and not ambiguities)
