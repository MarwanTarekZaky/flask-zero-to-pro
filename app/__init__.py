from flask import Flask
from app.config import DevConfig
from app.extensions import register_extensions 

def create_app(config_class=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    register_extensions(app)
    
    from app.main import main_bp
    app.register_blueprint(main_bp)
    
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500
    
    