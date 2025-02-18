import json
import pytest
from app import create_app
from app.models.user import User
from flask_jwt_extended import create_access_token

class FakeUser:
    """Clase fake para simular un usuario."""
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        # FOR TESTING, WE ASSUME THAT PASSWORD = "unitpass" IS OK
        return password == "unitpass"

# CREATING FAKE CLASS TO SIMULATE QUERY OBJECT
class FakeQuery:
    def __init__(self, user):
        self.user = user

    def first(self):
        return self.user

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

#ENSURE EACH TEST RUNS WITHIN AN APPLICATION CONTEXT
@pytest.fixture(autouse=True)
def push_app_context(app):
    with app.app_context():
        yield

def test_login_success(client, monkeypatch):
    # CREATING FAKE USER
    fake_user = FakeUser(id=1, username="unit_user", password_hash="irrelevante")

    # Monkeypatch OK query.filter_by() METHOD FOR User MODEL
    def fake_filter_by(**kwargs):
        # Asumimos que si se consulta por username unit_user, devolvemos el fake_user
        if kwargs.get('username') == "unit_user":
            return FakeQuery(fake_user)
        return FakeQuery(None)
    
    monkeypatch.setattr(User, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))

    # MAKING REQUEST TO /login
    payload = {
        "username": "unit_user",
        "password": "unitpass"
    }
    response = client.post('/login', json=payload)
    
    # VERIFY THAT REQUEST IS OK (200) AND RETURNS A TOKEN
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data

def test_login_failure(client, monkeypatch):
    # SIMULATING THAT USER CAN´T BE FOUND
    def fake_filter_by(**kwargs):
        return FakeQuery(None)
    
    monkeypatch.setattr(User, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))

    payload = {
        "username": "nonexistent",
        "password": "whatever"
    }
    response = client.post('/login', json=payload)
    
    # VERIFY THAT ENDPOINT RESPONDS 401 ON INVALID CREDENTIALS
    assert response.status_code == 401
    data = response.get_json()
    assert data["message"] == "Invalid Credentials..."
    
    
    #*******************************************
    #*******************************************

def test_register_success(client, monkeypatch):
    # SIMULATE THAT User.query.filter_by RETURNS None
    def fake_filter_by(**kwargs):
        return FakeQuery(None)
    
    monkeypatch.setattr(User, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    # SIMULATE THAT db.session.add y db.session.commit DO NOTHING
    from app import db
    monkeypatch.setattr(db.session, 'add', lambda x: None)
    monkeypatch.setattr(db.session, 'commit', lambda: None)

    payload = {
        "username": "new_unit_user",
        "password": "newunitpass"
    }
    response = client.post('/register', json=payload)
    
    # WAITING FOR USER CREATION AND RETURNS 201
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully"

def test_register_failure_existing_user(client, monkeypatch):
    # SIMULATE THAT USER ALREADY EXISTS
    fake_user = FakeUser(id=2, username="existing_user", password_hash="irrelevante")
    def fake_filter_by(**kwargs):
        if kwargs.get('username') == "existing_user":
            return FakeQuery(fake_user)
        return FakeQuery(None)
    
    monkeypatch.setattr(User, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))

    payload = {
        "username": "existing_user",
        "password": "any"
    }
    response = client.post('/register', json=payload)
    
    # WAITING FOR 400 RESPONSE FOR USER THAT ALREADY EXISTS
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "User already exists"
