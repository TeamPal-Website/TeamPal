import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
import uvicorn
from src.api.auth import router as router_auth
from src.api.admins import router as router_admins

app = FastAPI()

app.include_router(router_auth)
app.include_router(router_admins)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
