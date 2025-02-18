from flask import Blueprint, request, jsonify
from app.models.user import User
from app import db
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: The user's username.
              example: "john_doe"
            password:
              type: string
              description: The user's password.
              example: "secret123"
    responses:
      201:
        description: User registered successfully.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User registered successfully"
      400:
        description: Missing data or user already exists.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Missing data..."      
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing data...'}), 400

    # VERIFY IF USER EXISTS
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user and return a JWT token.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful.
        schema:
          type: object
          properties:
            access_token:
              type: string
      401:
        description: Invalid credentials.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid Credentials...'}), 401

    # GENERATE TOKEN
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token}), 200
