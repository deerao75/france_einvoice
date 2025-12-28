from flask import Flask, render_template
from .config import DevelopmentConfig
from .extensions import db, migrate, login_manager

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models
    from app import models

    # Register Blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.invoices import bp as invoice_bp
    app.register_blueprint(invoice_bp, url_prefix='/invoices')

    from app.routes.public import bp as public_bp
    app.register_blueprint(public_bp)

    # This is the correct place (inside the function)
    from app.routes.management import bp as mgmt_bp
    app.register_blueprint(mgmt_bp, url_prefix='/manage')

    # User loader
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
