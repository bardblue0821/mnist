"""preprocessor のテスト"""

import base64
import io

import numpy as np
import pytest
from PIL import Image

from app.services.preprocessor import PreprocessError, preprocess_image


def _create_test_png(width: int = 280, height: int = 280, color: int = 0) -> str:
    """テスト用の PNG 画像を Base64 文字列として生成する"""
    image = Image.new("RGBA", (width, height), (color, color, color, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64


def _create_test_png_with_data_uri(width: int = 280, height: int = 280) -> str:
    """data:image/png;base64, プレフィクス付きの PNG を生成"""
    b64 = _create_test_png(width, height)
    return f"data:image/png;base64,{b64}"


class TestPreprocessImage:
    """preprocess_image のテスト"""

    def test_valid_png_returns_correct_shape(self):
        """正常系: 280×280 PNG → shape (1, 28, 28, 1)"""
        b64 = _create_test_png(280, 280)
        result = preprocess_image(b64)
        assert result.shape == (1, 28, 28, 1)

    def test_valid_png_returns_float32(self):
        """正常系: dtype が float32"""
        b64 = _create_test_png(280, 280)
        result = preprocess_image(b64)
        assert result.dtype == np.float32

    def test_data_uri_prefix_is_handled(self):
        """正常系: data:image/png;base64, プレフィクス付きでも正常に処理"""
        b64 = _create_test_png_with_data_uri(280, 280)
        result = preprocess_image(b64)
        assert result.shape == (1, 28, 28, 1)

    def test_values_in_valid_range(self):
        """正常系: 全要素が 0.0〜1.0"""
        b64 = _create_test_png(280, 280, color=128)
        result = preprocess_image(b64)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_black_image_produces_zeros(self):
        """正常系: 黒画像は全て 0.0 に近い"""
        b64 = _create_test_png(280, 280, color=0)
        result = preprocess_image(b64)
        assert np.allclose(result, 0.0, atol=0.01)

    def test_white_image_produces_ones(self):
        """正常系: 白画像は全て 1.0 に近い"""
        b64 = _create_test_png(280, 280, color=255)
        result = preprocess_image(b64)
        assert np.allclose(result, 1.0, atol=0.01)

    def test_invalid_base64_raises_error(self):
        """異常系: 不正な Base64 → PreprocessError"""
        with pytest.raises(PreprocessError, match="Base64"):
            preprocess_image("not-valid-base64!!!")

    def test_non_image_binary_raises_error(self):
        """異常系: 画像でないバイナリ → PreprocessError"""
        b64 = base64.b64encode(b"this is not an image").decode("utf-8")
        with pytest.raises(PreprocessError, match="画像"):
            preprocess_image(b64)

    def test_different_sizes_are_resized(self):
        """正常系: 異なるサイズでも 28×28 にリサイズ"""
        b64 = _create_test_png(100, 100)
        result = preprocess_image(b64)
        assert result.shape == (1, 28, 28, 1)
