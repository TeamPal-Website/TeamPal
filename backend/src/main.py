from fastapi import FastAPI
import uvicorn
from src.api.auth import router as router_auth

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


app = FastAPI()

app.include_router(router_auth)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
