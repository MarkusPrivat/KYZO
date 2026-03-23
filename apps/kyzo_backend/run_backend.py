import uvicorn
from fastapi import FastAPI

from apps.kyzo_backend.core import create_database
from apps.kyzo_backend.api import user_router, knowledge_router


create_database()
app = FastAPI(title="Kyzo Backend")

app.include_router(user_router)
app.include_router(knowledge_router)



if __name__ == "__main__":
    uvicorn.run("run_backend:app", host="127.0.0.1", port=8000, reload=True)
