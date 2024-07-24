from flask import Flask, request, jsonify, redirect, url_for, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SECRET_KEY'] = 'your_secret_key'  # 보안을 위해 실제 키는 복잡하게 설정하세요
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'User already exists', 400
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('todos', username=username))
        return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/<username>/todos')
@login_required
def todos(username):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        all_todos = TodoItem.query.filter_by(user_id=user.id).all()
        result = todos_schema.dump(all_todos)
        return render_template('todos.html', todos=result)
    return 'Unauthorized access', 401

@app.route('/<username>/to', methods=['GET'])
@login_required
def get_todos(username):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        all_todos = TodoItem.query.filter_by(user_id=user.id).all()
        result = todos_schema.dump(all_todos)
        return jsonify(result)
    return jsonify({"message": "Unauthorized access"}), 401

@app.route('/<username>/to', methods=['POST'])
@login_required
def add_todo(username):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        name = request.json['name']
        is_executed = request.json['is_executed']

        new_todo_item = TodoItem(user_id=user.id, name=name, is_executed=is_executed)
        db.session.add(new_todo_item)
        db.session.commit()

        return todo_schema.jsonify(new_todo_item)
    return jsonify({"message": "Unauthorized access"}), 401

@app.route('/<username>/to/<id>', methods=['PUT', 'PATCH'])
@login_required
def execute_todo(username, id):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        todo = TodoItem.query.get(id)
        if todo and todo.user_id == user.id:
            todo.is_executed = not todo.is_executed
            db.session.commit()
            return todo_schema.jsonify(todo)
    return jsonify({"message": "Unauthorized access"}), 401

@app.route('/<username>/to/<id>', methods=['DELETE'])
@login_required
def delete_todo(username, id):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        todo_to_delete = TodoItem.query.get(id)
        if todo_to_delete and todo_to_delete.user_id == user.id:
            db.session.delete(todo_to_delete)
            db.session.commit()
            return todo_schema.jsonify(todo_to_delete)
    return jsonify({"message": "Unauthorized access"}), 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
