import uvicorn

from fastapi import FastAPI
from sqlalchemy import  create_engine

from apps.kyzo_backend.config.config import fastapi_settings



app = FastAPI()
engine = create_engine(fastapi_settings.SQLALCHEMY_DATABASE_URI)

@app.get("/config-check")
def check():
    return {"project_root": str(fastapi_settings.PROJECT_ROOT)}


if __name__ == "__main__":
    uvicorn.run("run_backend:app", host="127.0.0.1", port=8000, reload=True)
