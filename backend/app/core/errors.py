class AppError(Exception):
    code="APP_ERROR"
    status_code=400
    def __init__(self,message,details=None): self.message=message; self.details=details or {}
class ResourceNotFoundError(AppError): code="RESOURCE_NOT_FOUND"; status_code=404
class ScenarioValidationError(AppError): code="SCENARIO_VALIDATION_ERROR"; status_code=422
class SimulationExecutionError(AppError): code="SIMULATION_EXECUTION_ERROR"; status_code=500
class DatabaseConfigurationError(AppError): code="DATABASE_CONFIGURATION_ERROR"; status_code=503
class StateConsistencyError(AppError): code="STATE_CONSISTENCY_ERROR"; status_code=422
