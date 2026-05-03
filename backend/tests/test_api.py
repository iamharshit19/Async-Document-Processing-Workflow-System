import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import JobStatus

client = TestClient(app)

def get_auth_headers():
    response = client.post("/api/auth/token", data={"username": "admin", "password": "password"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}

def test_upload_document():
    # Create a dummy file
    files = [
        ("files", ("test1.txt", b"Hello World", "text/plain")),
        ("files", ("test2.txt", b"Hello World 2", "text/plain"))
    ]
    headers = get_auth_headers()
    response = client.post("/api/documents/upload", files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["filename"] == "test1.txt"
    assert data[1]["filename"] == "test2.txt"
    assert data[0]["status"] in ["Queued", "Processing", "Completed"]

def test_list_documents():
    headers = get_auth_headers()
    response = client.get("/api/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 2
