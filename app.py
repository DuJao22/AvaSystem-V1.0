# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config.from_object('config.Config')
    
    # Proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize database
    from models.database import init_db
    init_db(app.config['DATABASE_URL'])
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.patients import patients_bp
    from routes.evaluations import evaluations_bp
    from routes.distribution import distribution_bp
    from routes.reports import reports_bp
    from routes.admin import admin_bp
    from routes.profile import profile_bp
    from routes.assistant import assistant_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp, url_prefix='/pacientes')
    app.register_blueprint(evaluations_bp, url_prefix='/avaliacoes')
    app.register_blueprint(distribution_bp, url_prefix='/distribuicao')
    app.register_blueprint(reports_bp, url_prefix='/relatorios')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp, url_prefix='/perfil')
    app.register_blueprint(assistant_bp, url_prefix='/assistente')
    
    # Context processors
    @app.context_processor
    def inject_globals():
        from utils.helpers import format_date, calculate_age, format_datetime
        return {
            'creator_name': 'João Layon',
            'format_date': format_date,
            'calculate_age': calculate_age,
            'format_datetime': format_datetime
        }
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
