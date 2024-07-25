from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
from flask_jwt_extended import create_access_token, decode_token
from ..models import User
from .. import db, bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
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
        return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True)
            if data is None:
                data = request.form
            username = data.get('username')
            password = data.get('password')
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                access_token = create_access_token(identity=user.id)
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({"message": "Login successful", "token": access_token}), 200
                else:
                    response = make_response(redirect(url_for('todos.get_or_add_todos', username=username)))
                    response.set_cookie('access_token', access_token, httponly=True)
                    return response
            return jsonify({"message": "Invalid credentials"}), 401
        else:
            return render_template('login.html')
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@auth_bp.route('/logout', methods=['GET'])
def logout():
    response = make_response(jsonify({"message": "Logged out successfully"}), 200)
    response.delete_cookie('access_token')
    return response

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
