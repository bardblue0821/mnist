"""predictor のテスト"""

import numpy as np
import pytest

from app.services.predictor import Predictor

# Phase 1 で生成したモデルのパス
MODEL_PATH = "app/models/model.tflite"


@pytest.fixture
def predictor():
    """Predictor インスタンスを生成"""
    return Predictor(MODEL_PATH)


class TestPredictor:
    """Predictor のテスト"""

    def test_predict_returns_10_predictions(self, predictor):
        """正常系: 10 要素の Prediction リストが返る"""
        image = np.zeros((1, 28, 28, 1), dtype=np.float32)
        result = predictor.predict(image)
        assert len(result) == 10

    def test_predict_digits_are_0_to_9(self, predictor):
        """正常系: digit が 0〜9"""
        image = np.zeros((1, 28, 28, 1), dtype=np.float32)
        result = predictor.predict(image)
        digits = {p.digit for p in result}
        assert digits == set(range(10))

    def test_probabilities_sum_to_one(self, predictor):
        """正常系: 確率の合計 ≒ 1.0"""
        image = np.random.rand(1, 28, 28, 1).astype(np.float32)
        result = predictor.predict(image)
        total = sum(p.probability for p in result)
        assert abs(total - 1.0) < 0.01

    def test_probabilities_are_non_negative(self, predictor):
        """正常系: 全確率が 0 以上"""
        image = np.random.rand(1, 28, 28, 1).astype(np.float32)
        result = predictor.predict(image)
        for p in result:
            assert p.probability >= 0.0

    def test_probabilities_are_at_most_one(self, predictor):
        """正常系: 全確率が 1 以下"""
        image = np.random.rand(1, 28, 28, 1).astype(np.float32)
        result = predictor.predict(image)
        for p in result:
            assert p.probability <= 1.0
