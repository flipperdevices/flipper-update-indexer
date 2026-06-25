from fastapi.testclient import TestClient

import main
from src.storage import storage

client = TestClient(main.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready():
    assert client.get("/ready").status_code == 200


def test_serve_local_artifact_wins_over_catch_all_route():
    # also guards route ordering: /builds/<path> must win over /{directory}/{...}
    storage.write(
        b"firmware-bytes", "busybar-firmware", "0.9.2", "busybar-f22-0.9.2.tgz"
    )
    response = client.get("/builds/busybar-firmware/0.9.2/busybar-f22-0.9.2.tgz")
    assert response.status_code == 200
    assert response.content == b"firmware-bytes"


def test_serve_missing_artifact_returns_404():
    response = client.get("/builds/busybar-firmware/0.9.2/missing.tgz")
    assert response.status_code == 404
