# app.py
import os
from flask import Flask
from pymongo.errors import ConnectionFailure
from apps.services.database import init_db

# 1. IMPORTAÇÕES CORRETAS DOS BLUEPRINTS
from apps.routes.main import main_bp
from apps.routes.auth import auth_bp
from apps.routes.salary import salary_bp
from apps.routes.gastos import gastos_bp
from apps.routes.invest import invest_bp

def create_app():
    """ Função para criar e configurar a aplicação Flask. """
    
    # 2. CONFIGURAÇÃO CORRETA DA PASTA DE TEMPLATES
    app = Flask(__name__, template_folder='apps/templates', static_folder='apps/static') 
    app.secret_key = os.urandom(24) 

    # 3. REGISTRO DE TODOS OS BLUEPRINTS
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(salary_bp)
    app.register_blueprint(gastos_bp)
    app.register_blueprint(invest_bp)

    # Inicializa o banco de dados
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