import sys
from contextlib import asynccontextmanager
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.errors.base import AppError
import uvicorn
from src.api.auth import router as router_auth
from src.api.admins import router as router_admins
from src.api.profiles import router as router_profiles
from src.api.cities import router as router_cities
from src.api.resumes import router as router_resumes
from src.api.resume_experiences import router as router_resume_experiences
from src.api.resume_skills import router as router_skills
from src.api.skills import router as router_catalog_skills
from src.api.projects import router as router_projects
from src.api.project_vacancies import router as router_project_vacancies
from src.api.roles_dictionary import router as router_roles_dictionary
from src.api.applications import router as router_applications
from src.api.vacancies import router as router_vacancies
from src.api.notifications import router as router_notifications
from src.api.recommendations import router as router_recommendations
from src.catalog_cache import close_redis
from src.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()
app = FastAPI(lifespan=lifespan)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})


app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(router_auth)
app.include_router(router_admins)
app.include_router(router_profiles)
app.include_router(router_cities)
app.include_router(router_resumes)
app.include_router(router_resume_experiences)
app.include_router(router_skills)
app.include_router(router_catalog_skills)
app.include_router(router_projects)
app.include_router(router_project_vacancies)
app.include_router(router_roles_dictionary)
app.include_router(router_applications)
app.include_router(router_vacancies)
app.include_router(router_notifications)
app.include_router(router_recommendations)


if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
