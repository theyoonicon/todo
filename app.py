from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, decode_token
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SECRET_KEY'] = 'your_secret_key'  # 보안을 위해 실제 키는 복잡하게 설정하세요
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT 비밀 키
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_id'), nullable=False)
    name = db.Column(db.String(100))
    is_executed = db.Column(db.Boolean)

    def __init__(self, user_id, name, is_executed):
        self.user_id = user_id
        self.name = name
        self.is_executed = is_executed

class TodoSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'is_executed')

todo_schema = TodoSchema()
todos_schema = TodoSchema(many=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data is None:
            data = request.form
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 400
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return render_template('register.html')  # HTML 템플릿을 사용하여 등록 폼을 반환

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"message": "Invalid JSON data"}), 400
            username = data.get('username')
            password = data.get('password')
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                access_token = create_access_token(identity=user.id)
                return jsonify({"message": "Login successful", "token": access_token}), 200
            return jsonify({"message": "Invalid credentials"}), 401
        else:
            return render_template('login.html')
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

def get_jwt_identity_from_request():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.cookies.get('access_token')
    if not token:
        return None
    try:
        decoded_token = decode_token(token)
        return decoded_token['sub']
    except:
        return None

@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('access_token')
    return response

@app.route('/<username>/todos', methods=['GET', 'POST'])
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
                return jsonify(result)  # HTML 대신 JSON 반환
        return jsonify({"message": "Unauthorized access"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@app.route('/<username>/todos/<id>', methods=['PUT', 'PATCH'])
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

@app.route('/<username>/todos/<id>', methods=['DELETE'])
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
