"""Web 壳 单测（不调 LLM，测路由接线）。"""

from fastapi.testclient import TestClient

from daagent.web.server import app

client = TestClient(app)


def test_tools_endpoint():
    r = client.get("/api/tools")
    assert r.status_code == 200
    assert "execute_query" in r.json()["tools"]


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "数据分析" in r.text
