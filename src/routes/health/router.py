import os
from fastapi.routing import APIRouter
import psutil

from .schemas import HealthResponse


router = APIRouter()


@router.api_route(
    "/",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
)
def health():
    """
    Проверка доступности сервера.
    """
    process = psutil.Process(os.getpid())
    info = {
        "mem": f"{process.memory_info().rss / (1024 ** 2):.3f} MiB",
        "cpu_usage": process.cpu_percent(),
        "threads": len(process.threads()),
    }
    return {"status": "OK", "info": info}
