"""Pydantic スキーマ定義"""

from pydantic import BaseModel, Field, field_validator

# Base64 PNG の上限: 280x280 RGBA PNG ≈ 300KB → Base64 で約 400KB
# 余裕を持って 1MB
MAX_IMAGE_LENGTH = 1_400_000


class PredictRequest(BaseModel):
    image: str = Field(
        ...,
        description="Base64エンコードされたPNG画像",
        max_length=MAX_IMAGE_LENGTH,
    )

    @field_validator("image")
    @classmethod
    def validate_image_format(cls, v: str) -> str:
        """Base64 PNG のプレフィクスチェック"""
        if v.startswith("data:"):
            if not v.startswith("data:image/png;base64,"):
                raise ValueError("PNG 画像のみ対応しています")
        return v


class Prediction(BaseModel):
    digit: int = Field(..., ge=0, le=9)
    probability: float = Field(..., ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    predictions: list[Prediction] = Field(..., min_length=10, max_length=10)
