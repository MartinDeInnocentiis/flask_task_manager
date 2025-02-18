# Task Manager API

A Flask-based API that implements a task management system with JWT authentication. This API allows users to register an account, log in, and perform CRUD operations (Create, Read, Update, and Delete) on their tasks. Interactive documentation is generated using Swagger (Flasgger).

## Setup Instructions

### Requirements

- Python 3.8 or higher
- Virtualenv (optional but recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MartinDeInnocentiis/flask_task_manager
   cd task-manager-api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Unix/MacOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   
   Create a `.env` file in the project root and define the following variables:
   ```dotenv
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///app.db
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

5. **Initialize the database:**
   ```bash
   flask db init          # First time only
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```
   The application will run at http://127.0.0.1:5000

## API Documentation

The API's interactive documentation is generated using Swagger (Flasgger).

Once the application is running, access the documentation at:
```
http://127.0.0.1:5000/apidocs
```

The documentation shows all available endpoints, their parameters, responses, and examples, and allows you to test them interactively.

## Running Tests

Both integration and unit tests have been implemented using pytest.

Run all tests from the project root:
```bash
pytest -v
```

To check code coverage:
```bash
pytest --cov=app
```

## Design Decisions and Assumptions

### Authentication
- JWT (JSON Web Tokens) is used for authentication
- Endpoints are protected with `@jwt_required()` to ensure only authenticated users can access tasks

### Data Model
- Each task is associated with a user through the `user_id` field
- Users can only manage their own tasks

### API Documentation
- Flasgger was chosen for its easy Flask integration and ability to generate interactive documentation from YAML docstrings

### Validations
- Basic endpoint validations are implemented (e.g., ensuring task titles are provided and status values are valid)
- Production environments might benefit from specialized validation libraries like Marshmallow

### Testing
- Integration tests use an in-memory SQLite database
- Unit tests use monkeypatching to isolate endpoint logic
- This approach verifies both complete integration and isolated route behavior

### Configuration and Security
- Environment variables manage sensitive configurations
- Production deployments should use a robust WSGI server and additional security measures

## Project Structure

```
task-manager-api/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── user.py
│   │   └── task.py
│   └── routes/
│       ├── auth.py
│       └── tasks.py
├── migrations/
├── tests/
│   ├── conftest.py
│   ├── test_auth_unit.py
│   └── test_tasks_unit.py
├── config.py
├── .env
├── requirements.txt
└── run.py
```

## Application Entry Point

The `run.py` file serves as the application entry point:

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
```
