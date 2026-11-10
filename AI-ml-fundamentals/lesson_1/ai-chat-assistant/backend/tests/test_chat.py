import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "conversation_history": []}
    )
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["response"]) > 0

