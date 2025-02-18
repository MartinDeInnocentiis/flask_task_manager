from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.task import Task
from app import db

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json()

    title = data.get('title')
    description = data.get('description')
    # IF THERE IS NO STATUS, SETS "TO DO" AS DEFAULT
    status = data.get('status', 'To Do')

    if not title:
        return jsonify({'message': 'MUST contain TITLE'}), 400

    if status not in ['To Do', 'In Progress', 'Done']:
        return jsonify({'message': 'Invalid STATUS value'}), 400

    new_task = Task(
        title=title,
        description=description,
        status=status,
        user_id=user_id
    )
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'description': new_task.description,
        'status': new_task.status,
        'created_at': new_task.created_at,
        'updated_at': new_task.updated_at
    }), 201

@tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    
    # GET QUERY PARAMS
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 3, type=int) # YOU CAN ADD QUERY PARAM ?per_page= TO THE ENDPOINT
    
    # LIMIT per_page VALUE TO 100
    per_page = min(per_page, 100) # /tasks?per_page=100
    
    # PAGINATED QUERY
    pagination = Task.query.filter_by(user_id=user_id)\
        .order_by(Task.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    tasks_list = []
    for task in pagination.items:
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        })
    
    return jsonify({
        'tasks': tasks_list,
        'pagination': {
            'total_items': pagination.total,
            'total_pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200

@tasks_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'created_at': task.created_at,
        'updated_at': task.updated_at
    }), 200

@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        if status not in ['To Do', 'In Progress', 'Done']:
            return jsonify({'message': 'Invalid STATUS value'}), 400
        task.status = status

    db.session.commit()
    return jsonify({'message': 'Task updated successfully'}), 200

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'}), 200