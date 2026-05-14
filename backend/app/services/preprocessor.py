"""画像前処理サービス"""

import base64
import io
import re

import numpy as np
from PIL import Image


class PreprocessError(Exception):
    """前処理に関するエラー"""
    pass


def preprocess_image(image_base64: str) -> np.ndarray:
    """
    Base64 PNG 画像を TFLite 入力形式に変換する。

    Parameters:
        image_base64: "data:image/png;base64,..." または 生Base64 文字列

    Returns:
        np.ndarray: shape (1, 28, 28, 1), dtype float32, 値域 [0.0, 1.0]

    Raises:
        PreprocessError: デコードや変換に失敗した場合
    """
    # 1. プレフィクス除去
    raw_b64 = _strip_data_uri_prefix(image_base64)

    # 2. Base64 デコード
    try:
        image_bytes = base64.b64decode(raw_b64)
    except Exception:
        raise PreprocessError("Base64 デコードに失敗しました")

    # 3. PIL で画像を開く
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise PreprocessError("画像の読み込みに失敗しました")

    # 4. グレースケール変換
    image = image.convert("L")

    # 5. 28×28 にリサイズ
    image = image.resize((28, 28), Image.LANCZOS)

    # 6. NumPy 配列に変換 + 正規化
    arr = np.array(image, dtype=np.float32) / 255.0

    # 7. shape を (1, 28, 28, 1) に変換
    arr = arr.reshape(1, 28, 28, 1)

    return arr


def _strip_data_uri_prefix(data: str) -> str:
    """data:image/png;base64, プレフィクスがあれば除去"""
    pattern = r"^data:image/\w+;base64,"
    return re.sub(pattern, "", data)
