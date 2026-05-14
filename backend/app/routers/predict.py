"""API ルーター"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas.predict import PredictRequest, PredictResponse
from app.services.preprocessor import PreprocessError, preprocess_image

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest, request: Request) -> PredictResponse:
    """手書き数字を認識して各数字の確率を返す"""
    logger.info("POST /api/predict を受信")

    try:
        image_array = preprocess_image(body.image)
    except PreprocessError as e:
        logger.warning("前処理エラー: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    predictor = request.app.state.predictor
    predictions = predictor.predict(image_array)

    top = max(predictions, key=lambda p: p.probability)
    logger.info("推論結果: digit=%d (%.1f%%)", top.digit, top.probability * 100)

    return PredictResponse(predictions=predictions)


@router.get("/health")
async def health() -> dict:
    """ヘルスチェック"""
    return {"status": "ok"}
