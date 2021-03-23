import pytest
from app import app as flask_app
from app import parseCSV
import json

import mysql.connector

@pytest.fixture
def app():
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

def test_index(app, client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"Upload CSV file" in res.data
