from flask import Blueprint, request, jsonify, render_template
from ..models import User, TodoItem
from .. import db, ma
from .auth import get_jwt_identity_from_request

todos_bp = Blueprint('todos', __name__)

class TodoSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'is_executed')

todo_schema = TodoSchema()
todos_schema = TodoSchema(many=True)

@todos_bp.route('/<username>/todos', methods=['GET', 'POST'])
def get_or_add_todos(username):
    try:
        user_id = get_jwt_identity_from_request()
        if not user_id:
            return jsonify({"message": "Unauthorized access"}), 401
        user = User.query.filter_by(id=user_id).first()
        if user and user.username == username:
            if request.method == 'POST':
                data = request.get_json(force=True, silent=True)
                if data is None:
                    return jsonify({"message": "Invalid JSON data"}), 400
                name = data.get('name')
                is_executed = data.get('is_executed', False)
                new_todo_item = TodoItem(user_id=user.id, name=name, is_executed=is_executed)
                db.session.add(new_todo_item)
                db.session.commit()
                return todo_schema.jsonify(new_todo_item), 201
            else:
                all_todos = TodoItem.query.filter_by(user_id=user.id).all()
                result = todos_schema.dump(all_todos)
                if request.headers.get('Accept') == 'application/json':
                    return jsonify(result)
                return render_template('todos.html', todos=result)
        return jsonify({"message": "Unauthorized access"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@todos_bp.route('/<username>/todos/<id>', methods=['PUT', 'PATCH'])
def execute_todo(username, id):
    try:
        user_id = get_jwt_identity_from_request()
        if not user_id:
            return jsonify({"message": "Unauthorized access"}), 401
        user = User.query.filter_by(id=user_id).first()
        if user and user.username == username:
            todo = TodoItem.query.get(id)
            if todo and todo.user_id == user.id:
                todo.is_executed = not todo.is_executed
                db.session.commit()
                return todo_schema.jsonify(todo)
        return jsonify({"message": "Unauthorized access"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@todos_bp.route('/<username>/todos/<id>', methods=['DELETE'])
def delete_todo(username, id):
    try:
        user_id = get_jwt_identity_from_request()
        if not user_id:
            return jsonify({"message": "Unauthorized access"}), 401
        user = User.query.filter_by(id=user_id).first()
        if user and user.username == username:
            todo_to_delete = TodoItem.query.get(id)
            if todo_to_delete and todo_to_delete.user_id == user.id:
                db.session.delete(todo_to_delete)
                db.session.commit()
                return todo_schema.jsonify(todo_to_delete)
        return jsonify({"message": "Unauthorized access"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
