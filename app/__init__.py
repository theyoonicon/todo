from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class='config.default.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from app.views.auth import auth_bp
    from app.views.todos import todos_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(todos_bp)

    return app



    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
    #app.config['SECRET_KEY'] = 'your_secret_key'
    #app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False