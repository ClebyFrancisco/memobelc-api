import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


import pytest
import json
from flask import Flask
from src.app import create_app, mongo
from src.app.models.user_model import UserModel
from src.app.services.auth_service import AuthService
from src.app.controllers.auth_controller import auth_blueprint

from dotenv import load_dotenv
from os import path, environ

basedir = path.abspath(path.join(path.dirname(__file__), "../../"))
load_dotenv(path.join(basedir, ".env"))

@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["MONGO_URI"] = environ["MONGO_URI_TEST"]
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    
    yield app 
    
    mongo.db.users.drop()

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def new_user():
    return {"name": "Test User", "email": "test@example.com", "password": "password123"}


def test_register_new_user(client, new_user):
    response = client.post("/auth/register", data=json.dumps(new_user), content_type="application/json")
    assert response.status_code == 201
    data = response.get_json()
    assert "token" in data

        
def test_register_user_already_exists(client, new_user):
    response = client.post("/auth/register", data=json.dumps(new_user), content_type="application/json")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
