import os
from app import create_app, db
from flask_migrate import Migrate

config_name = os.getenv('FLASK_CONFIG') or 'config.development.DevelopmentConfig'
app = create_app(config_class=config_name)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()
