import os

import pandas as pd
import psutil
import uvicorn
from fastapi import FastAPI, UploadFile, File

from src.api_methods import get_dataset_names, get_dataset_configs, get_predict, run_train
from src.logger import LoggerFactory
from src.config import api_config

app_logger = LoggerFactory.get_logger('APP')
app = FastAPI(openapi_url="/api/v1/openapi.json")


@app.api_route("/health", methods=['GET', 'HEAD'], tags=["health"])
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
    return {
        "status": "OK",
        "info": info
    }


@app.get("/datasets", tags=["datasets"])
def dataset_names_route():
    return get_dataset_names()


@app.get("/datasets/configs", tags=["datasets"])
def dataset_configs_route():
    return get_dataset_configs()


@app.post("/train", tags=["models"])
def train_route(
        dataset_name: str,
        time_limit: float = 5.0
):
    model_info = run_train(
        dataset_name=dataset_name,
        time_limit=time_limit
    )
    print('model_info', model_info)
    return model_info


@app.post("/predict", tags=["models"])
def predict_route(
        dataset_name: str,
        data_file: UploadFile = File(...),
):
    data = pd.read_csv(data_file.file)
    result_array = get_predict(
        data,
        dataset_name=dataset_name
    )
    return result_array.tolist()


if __name__ == '__main__':
    uvicorn.run(
        f"{__name__}:app",
        host=api_config.get("host", "localhost"),
        port=int(api_config.get("port", 8080)),
        log_level="info"
    )
