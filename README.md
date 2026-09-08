# WorldTwin — AI Digital Twin of a Small World

A research-oriented Generative AI digital twin platform. Campus is the first world implementation, but the architecture is designed around reusable entities, relationships, scenarios, simulation branches, analytics, knowledge grounding and decision support.

## Current feature set

- Interactive living-world spatial view with clickable entities and an entity inspector
- Functional navigation: Living World, Scenario Studio, Future Branches, Experiment Lab, AI Copilot, Intervention Lab, Knowledge Graph, Research Reports
- Natural-language scenario compiler with structured parameters, confidence, assumptions and ambiguity handling
- Persistent immutable simulation branches
- Branch timeline, events, metrics, anomalies and predictions
- Interactive metric trajectory visualization
- Counterfactual-ready intervention evaluation layer
- AI copilot grounded in world and branch context
- Local TF-IDF knowledge retrieval over `knowledge/`
- Experiment Lab for controlled scenario conditions
- Research report generation
- Twin architecture / research instrumentation views
- SQLite + SQLAlchemy + Alembic persistence
- FastAPI API with Swagger documentation
- React + TypeScript + Vite frontend

## Run in VS Code

### Backend terminal

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m app.seed.campus
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

### Frontend terminal

Open a second VS Code terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Suggested flagship demo

1. Open **Living World**.
2. Open **Scenario Studio**.
3. Run:
   `Simulate a 40% reduction in bus availability during the morning rush, while a major campus event is taking place.`
4. Inspect the parsed action and confidence.
5. Run the branch.
6. Open **Future Branches** and inspect telemetry, trajectory, anomalies and predictions.
7. Open **AI Copilot** and ask why the branch is congested.
8. Open **Intervention Lab** and rank responses.
9. Generate a **Research Report**.

## API areas

- `/api/health`
- `/api/dashboard`
- `/api/world`
- `/api/world/state`
- `/api/world/entities`
- `/api/world/relationships`
- `/api/scenarios/*`
- `/api/branches/*`
- `/api/simulations/*`
- `/api/copilot`
- `/api/knowledge/*`
- `/api/experiments/run`
- `/api/reports/*`

## Research roadmap

The next major engineering layers are real counterfactual intervention execution, calibrated predictive models, an LLM adapter, PDF/document ingestion, multimodal inputs, richer agent routing, animated spatial simulation, uncertainty propagation, branch comparison analytics, experiment evaluation and a research dashboard.
