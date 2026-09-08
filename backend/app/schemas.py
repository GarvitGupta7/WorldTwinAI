from typing import Any
from pydantic import BaseModel,Field
class ScenarioRequest(BaseModel): text:str=Field(min_length=5,max_length=1000); seed:int=42; duration_minutes:int=Field(60,ge=1,le=240)
class ScenarioParameter(BaseModel): name:str; value:float|int|str|bool; unit:str|None=None; source:str; confidence:float=Field(ge=0,le=1)
class ScenarioResponse(BaseModel): scenario_id:str; original_text:str; action:str; parameters:list[ScenarioParameter]; assumptions:list[str]; ambiguities:list[str]; valid:bool
class ScenarioCreateRequest(BaseModel): scenario:ScenarioResponse
class BranchCreateRequest(BaseModel): scenario_id:str; world_id:str="world-campus"; seed:int=42; duration_minutes:int=Field(60,ge=1,le=240); name:str|None=None
class SimulationRequest(BaseModel): scenario:ScenarioResponse; seed:int=42; duration_minutes:int=Field(60,ge=1,le=240)
class MetricComparison(BaseModel): metric:str; baseline:float; scenario:float; change:float; change_percent:float
class SimulationResponse(BaseModel): branch_id:str; scenario_id:str; seed:int; duration_minutes:int; baseline_metrics:dict[str,float]; scenario_metrics:dict[str,float]; comparison:list[MetricComparison]; anomalies:list[dict[str,Any]]; causal_chain:list[str]
class WorldSummary(BaseModel): id:str; name:str; world_type:str; description:str; current_timestamp:int; entity_count:int; relationship_count:int
class EntityResponse(BaseModel): id:str; name:str; entity_type:str; x:float; y:float; state:dict[str,Any]; attributes:dict[str,Any]; relationships:list[str]; source:str; freshness_status:str; confidence:float
class RelationshipResponse(BaseModel): id:int; world_id:str; source_entity_id:str; target_entity_id:str; relationship_type:str; attributes:dict[str,Any]
class BranchResponse(BaseModel): id:str; world_id:str; parent_branch_id:str|None; scenario_id:str|None; branch_type:str; name:str; seed:int; duration_minutes:int; status:str; initial_state_hash:str; created_at:str; completed_at:str|None
class TimelineStateResponse(BaseModel): timestamp:int; state:dict[str,Any]; state_hash:str
class MetricSnapshotResponse(BaseModel): timestamp:int; metrics:dict[str,float]
class SimulationEventResponse(BaseModel): timestamp:int; event_type:str; entity_ids:list[str]; description:str; evidence:dict[str,Any]
class AnomalyResponse(BaseModel): timestamp:int; anomaly_type:str; severity:str; metric:str; observed_value:float; expected_value:float; deviation:float; affected_entity_ids:list[str]; evidence:dict[str,Any]; confidence:float
class PredictionResponse(BaseModel): timestamp:int; horizon_minutes:int; metric:str; predicted_value:float; confidence:float; model_name:str; feature_evidence:dict[str,Any]; limitations:list[str]
class BranchComparisonResponse(BaseModel): baseline_branch_id:str; scenario_branch_id:str; metrics:list[MetricComparison]
class CopilotRequest(BaseModel): message:str=Field(min_length=2,max_length=2000); branch_id:str|None=None
class CopilotResponse(BaseModel): answer:str; intent:str; evidence:list[dict[str,Any]]; actions:list[dict[str,Any]]
