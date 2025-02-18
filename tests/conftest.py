import pytest
from app import create_app, db
from app.models.user import User
from app.models.task import Task
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def init_database(app):
    """Initialize test database."""
    with app.app_context():
        db.create_all()
        
        # CREATE TEST USER
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        # CREATE TEST TASKS
        task1 = Task(
            title="Test Task 1",
            description="Description 1",
            status="To Do",
            user_id=user.id
        )
        task2 = Task(
            title="Test Task 2",
            description="Description 2",
            status="In Progress",
            user_id=user.id
        )
        db.session.add(task1)
        db.session.add(task2)
        db.session.commit()
        
        yield db
        
        db.drop_all()

@pytest.fixture
def auth_headers(app, init_database):
    """Generate token and headers for authenticated requests."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        token = create_access_token(identity=str(user.id))
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        return headers