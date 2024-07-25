from app import create_app
import os

config_name = os.getenv('FLASK_CONFIG') or 'config.development.DevelopmentConfig'
app = create_app(config_class=config_name)

if __name__ == "__main__":
    app.run()
