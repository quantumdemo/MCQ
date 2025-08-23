from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'main.login' # To be created
login_manager.login_message_category = 'info'

import importlib

def create_app(config_name='config.Config'):
    app = Flask(__name__)

    # Dynamically import the config class
    try:
        config_module_name, config_class_name = config_name.rsplit('.', 1)
        config_module = importlib.import_module(config_module_name)
        config_class = getattr(config_module, config_class_name)
    except (ImportError, AttributeError):
        raise ImportError(f"Could not import config class '{config_name}'")

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from app.exam import exam_bp
    app.register_blueprint(exam_bp)

    # Register CLI commands
    from app import commands
    commands.register_commands(app)

    # Make sure models are imported for migrations
    from app import models

    return app
