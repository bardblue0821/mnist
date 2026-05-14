"""conftest.py — テスト用の共通 fixture"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """テスト用 FastAPI クライアント"""
    app = create_app()
    with TestClient(app) as c:
        yield c
