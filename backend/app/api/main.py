from fastapi import APIRouter

from app.api.routes import (
    approvals,
    artifacts,
    documents,
    health,
    jobs,
    literature,
    login,
    private,
    projects,
    query_plans,
    research_questions,
    users,
    utils,
)
from app.core.config import settings
from app.research_questions import service as research_question_service

research_question_service.register_approval_handlers()

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(projects.router)
api_router.include_router(research_questions.router)
api_router.include_router(query_plans.router)
api_router.include_router(literature.router)
api_router.include_router(documents.router)
api_router.include_router(artifacts.router)
api_router.include_router(jobs.router)
api_router.include_router(approvals.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
