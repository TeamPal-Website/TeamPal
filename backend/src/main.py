import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from src.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

app.mount("/", StaticFiles(
    directory=str(Path(__file__)
    .resolve().parent.parent.parent / "frontend"), html=True), name="frontend"
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
