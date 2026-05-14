"""FastAPI アプリケーション"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.logging_config import setup_logging
from app.routers.predict import router as predict_router
from app.services.predictor import Predictor

setup_logging()
logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "model.tflite"
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    logger.info("モデルをロード中: %s", MODEL_PATH)
    app.state.predictor = Predictor(str(MODEL_PATH))
    logger.info("モデルロード完了")
    yield
    logger.info("アプリケーション終了")


def create_app() -> FastAPI:
    """FastAPI アプリケーションファクトリ"""
    app = FastAPI(
        title="手書き数字認識 API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(predict_router, prefix="/api")

    # 静的ファイル配信（本番用: Next.js ビルド成果物）
    if STATIC_DIR.exists():
        app.mount(
            "/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static"
        )

    return app


app = create_app()
