# app.py
import os
from flask import Flask
from pymongo.errors import ConnectionFailure
from werkzeug.middleware.proxy_fix import ProxyFix
from apps.services.database import init_db

# 1. IMPORTAÇÕES DOS BLUEPRINTS
from apps.routes.main import main_bp
from apps.routes.auth import auth_bp
from apps.routes.salary import salary_bp
from apps.routes.invest import invest_bp
from apps.routes.contas import contas_bp

def create_app():
    """ Função para criar e configurar a aplicação Flask. """
    
    app = Flask(__name__, template_folder='apps/templates', static_folder='apps/static') 
    app.secret_key = os.urandom(24) 
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # 2. REGISTRO DE TODOS OS BLUEPRINTS
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(salary_bp)
    app.register_blueprint(invest_bp)
    app.register_blueprint(contas_bp)

    try:
        with app.app_context():
            init_db()
    except ConnectionFailure as e:
        print(f"FALHA CRÍTICA AO CONECTAR COM O BANCO DE DADOS: {e}")
        raise

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)