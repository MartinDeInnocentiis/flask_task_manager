import json
import datetime
import pytest
from flask import jsonify
from app import create_app, db
from app.models.task import Task

# FAKE CLASSES TO SIMULATE OBJECTS

class FakeTask:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 123)
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.status = kwargs.get("status")
        self.user_id = kwargs.get("user_id")
        self.created_at = datetime.datetime.utcnow().isoformat()
        self.updated_at = datetime.datetime.utcnow().isoformat()

class FakePagination:
    def __init__(self, items, total, pages, current_page, per_page):
        self.items = items
        self.total = total
        self.pages = pages
        self.page = current_page
        self.per_page = per_page
        self.has_next = current_page < pages
        self.has_prev = current_page > 1

# FIXTURES FOR THE APP AND TEST CLIENT

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
        
@pytest.fixture(autouse=True)
def bypass_jwt(monkeypatch):
    monkeypatch.setattr(
        "flask_jwt_extended.view_decorators.verify_jwt_in_request",
        lambda *args, **kwargs: None
    )

# UNIT TESTS FOR TASK ENDPOINTS

def fake_get_jwt_identity():
    # FOR UNIT TESTS, SIMULATE THAT AUTHENTICATED USER IS ID=1
    return "1"

# 1. TEST FOR create_task
def test_create_task_success(client, monkeypatch):
    # BYPASSING AUTH
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", lambda: "1")
    
    # REPLACE Task CLASS IN ROUTES FOR FakeTask
    monkeypatch.setattr("app.routes.tasks.Task", FakeTask)
    
    # SIMULATE DB OPERATIONS
    # REPLACE db.session.add y db.session.commit FOR FUNCTIONS THAT DO NOTHING
    monkeypatch.setattr(db.session, 'add', lambda x: None)
    monkeypatch.setattr(db.session, 'commit', lambda: None)
    
    data = {
        'title': 'New Task',
        'description': 'Test Description',
        'status': 'To Do'
    }
    
    response = client.post(
        '/tasks',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    resp_json = response.get_json()
    # SINCE FakeTask USES 123 ID BY DEFAULT, VERIFY THAT THERE IS THAT VALUE
    assert resp_json['id'] == 123
    assert resp_json['title'] == 'New Task'

def test_create_task_missing_title(client, monkeypatch):
    # SIMULATE AUTENTICATION
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    data = {
        # TITLE IS MISSING
        'description': 'Test Description',
        'status': 'To Do'
    }
    
    response = client.post(
        '/tasks',
        data=json.dumps(data),
        content_type='application/json'
    )
    # 400 IS EXPECTED BECAUSE OF MISSING TITLE
    assert response.status_code == 400
    assert response.get_json()['message'] == 'MUST contain TITLE'

def test_create_task_invalid_status(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    data = {
        'title': 'New Task',
        'description': 'Test Description',
        'status': 'Not valid'
    }
    
    response = client.post(
        '/tasks',
        data=json.dumps(data),
        content_type='application/json'
    )
    # 400 IS EXPECTED BECAUSE OF INVALID STATUS
    assert response.status_code == 400
    assert response.get_json()['message'] == 'Invalid STATUS value'

# 2. TEST FOR get_tasks
def test_get_tasks(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    # CREATE FAKE TASK LIST & PAGINATION
    fake_tasks = [
        FakeTask(id=1, title="Task 1", description="Desc 1", status="To Do", user_id="1"),
        FakeTask(id=2, title="Task 2", description="Desc 2", status="Done", user_id="1")
    ]
    fake_pagination = FakePagination(
        items=fake_tasks,
        total=2,
        pages=1,
        current_page=1,
        per_page=3
    )
    
    # Monkeypatch: SIMULATE THAT Task.query.filter_by(...).order_by(...).paginate(...) RETURNS OUR fake_pagination
    class FakeQuery:
        def __init__(self, pagination):
            self.pagination = pagination
        
        def order_by(self, *args, **kwargs):
            return self
        
        def paginate(self, page, per_page):
            return self.pagination
    
    def fake_filter_by(**kwargs):
        return FakeQuery(fake_pagination)
    
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    response = client.get('/tasks?page=1&per_page=3')
    assert response.status_code == 200
    resp_json = response.get_json()
    # VERIFY THAT RESPONSE INCLUDES 'tasks' y 'pagination'
    assert 'tasks' in resp_json
    assert 'pagination' in resp_json
    # THERE MUST BE 2 TASKS
    assert len(resp_json['tasks']) == 2
    assert resp_json['pagination']['total_items'] == 2

# 3. TEST FOR get_task
def test_get_task_success(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    # CREATING FAKE TASK
    fake_task = FakeTask(id=10, title="Task X", description="Desc X", status="In Progress", user_id="1")
    
    # SIMULATE Task.query.filter_by(...).first() TO RETURN la fake_task
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return fake_task
        return FakeQuery()
    
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    response = client.get('/tasks/10')
    assert response.status_code == 200
    resp_json = response.get_json()
    assert resp_json['id'] == 10
    assert resp_json['title'] == "Task X"

def test_get_task_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    # SIMULATE THAT REQUEST RETURNS None (TASK NOT FOUND)
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return None
        return FakeQuery()
    
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    response = client.get('/tasks/999')
    assert response.status_code == 404
    assert response.get_json()['message'] == 'Task not found'

# 4. TEST FOR update_task
def test_update_task_success(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    # CREATE A FAKE TASK
    fake_task = FakeTask(id=20, title="Old Title", description="Old Desc", status="To Do", user_id="1")
    
    # SIMULATE Task.query.filter_by(...).first() TO RETURN fake_task
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return fake_task
        return FakeQuery()
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    # SIMULATE db.session.commit (DOES NOTHING)
    monkeypatch.setattr(db.session, 'commit', lambda: None)
    
    data = {
        'title': 'Updated Title',
        'status': 'Done'
    }
    
    response = client.put('/tasks/20', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Task updated successfully'
    # VERIFYING THAT TASK WAS MODIFIED
    assert fake_task.title == 'Updated Title'
    assert fake_task.status == 'Done'

def test_update_task_invalid_status(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    fake_task = FakeTask(id=30, title="Old Title", description="Old Desc", status="To Do", user_id="1")
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return fake_task
        return FakeQuery()
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    data = {
        'status': 'Not valid'
    }
    response = client.put('/tasks/30', data=json.dumps(data), content_type='application/json')
    # EXPECTING 400 ERROR (INVALID STATUS)
    assert response.status_code == 400
    assert response.get_json()['message'] == 'Invalid STATUS value'

# 5. TEST FOR delete_task
def test_delete_task_success(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    fake_task = FakeTask(id=40, title="Task to delete", description="Desc", status="Done", user_id="1")
    # SIMULATE Task.query.filter_by(...).first() TO RETURN fake_task
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return fake_task
        return FakeQuery()
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    # SIMULATE db.session.delete AND commit
    monkeypatch.setattr(db.session, 'delete', lambda x: None)
    monkeypatch.setattr(db.session, 'commit', lambda: None)
    
    response = client.delete('/tasks/40')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Task deleted successfully'

def test_delete_task_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routes.tasks.get_jwt_identity", fake_get_jwt_identity)
    
    # SIMULATE THAT TASK CAN´T BE FOUND
    def fake_filter_by(**kwargs):
        class FakeQuery:
            def first(self_nonlocal):
                return None
        return FakeQuery()
    monkeypatch.setattr(Task, 'query', type('FakeQueryClass', (), {'filter_by': staticmethod(fake_filter_by)}))
    
    response = client.delete('/tasks/999')
    assert response.status_code == 404
    assert response.get_json()['message'] == 'Task not found'