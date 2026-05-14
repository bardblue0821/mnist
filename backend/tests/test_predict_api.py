"""API エンドポイントのテスト"""

import base64
import io

from PIL import Image


def _create_test_png_b64(width: int = 280, height: int = 280, color: int = 0) -> str:
    """テスト用 Base64 PNG 画像を生成"""
    image = Image.new("RGBA", (width, height), (color, color, color, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


class TestHealthEndpoint:
    """GET /api/health のテスト"""

    def test_health_returns_ok(self, client):
        """ヘルスチェックが {"status": "ok"} を返す"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPredictEndpoint:
    """POST /api/predict のテスト"""

    def test_valid_image_returns_predictions(self, client):
        """正常系: 有効な画像 → 200, 10要素の predictions"""
        b64 = _create_test_png_b64(280, 280)
        response = client.post("/api/predict", json={"image": b64})
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 10

    def test_valid_image_with_data_uri(self, client):
        """正常系: data:image/png;base64, 付きでも正常処理"""
        b64 = _create_test_png_b64(280, 280)
        response = client.post(
            "/api/predict",
            json={"image": f"data:image/png;base64,{b64}"},
        )
        assert response.status_code == 200
        assert len(response.json()["predictions"]) == 10

    def test_predictions_have_correct_structure(self, client):
        """正常系: 各要素に digit と probability がある"""
        b64 = _create_test_png_b64(280, 280)
        response = client.post("/api/predict", json={"image": b64})
        for pred in response.json()["predictions"]:
            assert "digit" in pred
            assert "probability" in pred
            assert 0 <= pred["digit"] <= 9
            assert 0.0 <= pred["probability"] <= 1.0

    def test_invalid_base64_returns_400(self, client):
        """異常系: 不正な Base64 → 400"""
        response = client.post(
            "/api/predict",
            json={"image": "not-valid-base64!!!"},
        )
        assert response.status_code == 400

    def test_empty_image_returns_422(self, client):
        """異常系: 空文字列 → 422 (Pydantic バリデーション)"""
        response = client.post("/api/predict", json={"image": ""})
        # 空文字列は Pydantic の max_length は通るが、Base64 デコードで失敗 → 400
        # もしくは空は有効な Base64 で空バイトになり画像デコードで失敗 → 400
        assert response.status_code == 400

    def test_oversized_image_returns_422(self, client):
        """異常系: サイズ超過 → 422 (max_length)"""
        # 1.5MB の Base64 文字列
        huge = "A" * 1_500_000
        response = client.post("/api/predict", json={"image": huge})
        assert response.status_code == 422

    def test_non_png_data_uri_returns_422(self, client):
        """異常系: PNG 以外の data URI → 422"""
        b64 = _create_test_png_b64(280, 280)
        response = client.post(
            "/api/predict",
            json={"image": f"data:image/jpeg;base64,{b64}"},
        )
        assert response.status_code == 422
