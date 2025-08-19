from fastapi.routing import APIRouter


from src.config import config_manager
from .health.router import router as health_route
from .datasets.router import router as dataset_router
from .mlmodels.router import router as mlmodel_router
from .predict.router import router as predict_router
from .tasks.router import router as tasks_router

router = APIRouter()

# Добавим основные маршруты
router.include_router(
    health_route, prefix=config_manager.api_config.health, tags=["Health"]
)
router.include_router(
    dataset_router, prefix=config_manager.api_config.datasets, tags=["Datasets"]
)
router.include_router(
    mlmodel_router, prefix=config_manager.api_config.mlmodels, tags=["MLModels"]
)
router.include_router(
    predict_router, prefix=config_manager.api_config.predict, tags=["Predict"]
)
router.include_router(
    tasks_router, prefix=config_manager.api_config.tasks, tags=["Tasks"]
)


# Добавим вложенные маршруты
mlmodel_router.include_router(predict_router, prefix="/{mlmodel_id}")
