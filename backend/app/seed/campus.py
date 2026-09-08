from app.core.database import SessionLocal
from app.db.repositories.world_repository import WorldRepository
from app.services.world_service import WorldService
from app.db.repositories.branch_repository import BranchRepository
from app.services.scenario_service import ScenarioService
from app.services.branch_service import BranchService
def main():
 db=SessionLocal()
 try:
  w=WorldService(WorldRepository(db)); world=w.ensure(42); b=BranchService(BranchRepository(db),w,ScenarioService(None)); base=b.ensure_baseline(world.id,42,60); print(f"world id: {world.id}");print(f"entity count: {len(w.repo.entities(world.id))}");print(f"relationship count: {len(w.repo.relationships(world.id))}");print(f"baseline branch: {base.id}")
 finally:db.close()
if __name__=='__main__':main()
