import pytest
from rest_framework.test import APIClient
from django.db import connection


@pytest.mark.django_db
def test_healthz_ok():
    client = APIClient()
    resp = client.get("/healthz/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_readyz_ok_when_db_up():
    client = APIClient()
    resp = client.get("/readyz/")
    assert resp.status_code == 200
    assert resp.json().get("db") == "ok"


@pytest.mark.django_db
def test_readyz_fails_when_db_down(monkeypatch):
    client = APIClient()

    def broken_cursor(*args, **kwargs):
        raise Exception("DB down")

    monkeypatch.setattr(connection, "cursor", broken_cursor)

    resp = client.get("/readyz/")
    assert resp.status_code == 503
