import uuid

from app.core.celery import celery_app


class CeleryJobDispatcher:
    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        celery_app.send_task(
            "reca.execute_job",
            args=[str(job_id)],
            task_id=task_id,
        )


dispatcher = CeleryJobDispatcher()
