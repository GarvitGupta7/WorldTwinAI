from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.core.errors import AppError
from app.core.logging import configure_logging
configure_logging();app=FastAPI(title="AI Digital Twin of a Small World",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"]);app.include_router(router)
@app.exception_handler(AppError)
async def err(request:Request,exc:AppError):return JSONResponse(status_code=exc.status_code,content={"error":{"code":exc.code,"message":exc.message,"details":exc.details}})
@app.get('/')
def root():return {"name":"AI Digital Twin of a Small World","docs":"/docs","health":"/api/health"}
