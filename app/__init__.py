from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load config
    if config_class is None:
        # Import here to avoid circular imports
        from config import get_config
        app.config.from_object(get_config())
    else:
        app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Setup login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'info'
    
    # Import and register blueprints
    from app.routes.auth import auth_bp
    from app.routes.asset import asset_bp
    from app.routes.request import request_bp
    from app.routes.prediction import prediction_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(prediction_bp)
    
    # Register shell context processor
    @app.shell_context_processor
    def make_shell_context():
        # Import models here to avoid circular imports
        from app.models.user import User
        from app.models.asset import Asset
        from app.models.asset_request import AssetRequest
        from app.models.satker import Satker
        from app.models.prediction import Prediction
        return {
            'db': db, 
            'User': User, 
            'Asset': Asset, 
            'AssetRequest': AssetRequest,
            'Satker': Satker,
            'Prediction': Prediction
        }
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    # Initialize database
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app.models import user, asset, asset_request, satker, prediction, sbsk_validator
        db.create_all()
    
    return app