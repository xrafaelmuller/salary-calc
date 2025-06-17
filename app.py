from flask import Flask, render_template_string, request, redirect, url_for, session, flash, get_flashed_messages
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- Importações para PostgreSQL com SQLAlchemy ---
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, OperationalError

app = Flask(__name__)
app.secret_key = os.urandom(24) # Chave secreta para sessões, essencial!

# --- Configuração do Banco de Dados PostgreSQL ---
# O Render fornece a DATABASE_URL automaticamente.
# Em desenvolvimento local, você pode definir uma URL padrão para PostgreSQL local,
# ou continuar usando SQLite temporariamente para testes locais se preferir,
# mas para deploy no Render, a DATABASE_URL é crucial.
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/my_local_db')
# IMPORTANTE: A string de conexão precisa ser ajustada para o driver psycopg2
# e incluir 'sslmode=require' para o Render em produção.
# O dj_database_url (usado em Django) faz isso automaticamente, mas aqui vamos explicitar.
# Exemplo de DATABASE_URL do Render: postgresql://user:password@host:port/database_name
# Para sqlalchemy, podemos precisar de: postgresql+psycopg2://user:password@host:port/database_name
# E para SSL: postgresql+psycopg2://user:password@host:port/database_name?sslmode=require

# Para garantir que o SSL seja usado em produção no Render
if "RENDER" in os.environ: # Verifica se está no ambiente Render
    DATABASE_URL = DATABASE_URL + "?sslmode=require" # Adiciona sslmode=require

# Cria o engine do SQLAlchemy
# Usamos psycopg2 como driver.
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))

def get_db_connection():
    """Função auxiliar para obter uma conexão com o banco de dados."""
    try:
        return engine.connect()
    except OperationalError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        # Em um ambiente real, você pode querer logar o erro ou lançar uma exceção mais específica
        raise ConnectionError("Não foi possível conectar ao banco de dados.") from e


def init_db():
    """Inicializa o banco de dados, criando tabelas de usuários e perfis."""
    with get_db_connection() as conn:
        # Tabela de Usuários
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        '''))
        # Tabela de Perfis, agora com user_id
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                salario REAL,
                quinquenio REAL,
                vale_alimentacao REAL,
                plano_saude REAL,
                previdencia_privada REAL,
                odontologico REAL,
                premiacao REAL,
                UNIQUE(user_id, name), -- Garante que um usuário não tenha dois perfis com o mesmo nome
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        '''))
        conn.commit() # Commit é necessário ao usar conn.execute direto

# --- Funções de Banco de Dados para Usuários ---
def add_user(username, password):
    """Adiciona um novo usuário ao banco de dados."""
    hashed_password = generate_password_hash(password)
    with get_db_connection() as conn:
        try:
            conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"),
                         {"username": username, "password_hash": hashed_password})
            conn.commit()
            return True
        except IntegrityError: # Captura erro de chave única (usuário já existe)
            conn.rollback() # Garante que a transação seja revertida em caso de erro
            return False

def get_user_by_username(username):
    """Obtém um usuário pelo nome de usuário."""
    with get_db_connection() as conn:
        result = conn.execute(text("SELECT id, username, password_hash FROM users WHERE username = :username"),
                              {"username": username})
        row = result.fetchone()
        if row:
            return dict(row._mapping) # Converte o RowProxy para dicionário
        return None

# --- Funções de Banco de Dados para Perfis (Atualizadas com user_id) ---
def save_profile_to_db(user_id, profile_name, data):
    """Salva ou atualiza um perfil para um usuário específico."""
    with get_db_connection() as conn:
        result = conn.execute(text('SELECT id FROM profiles WHERE user_id = :user_id AND name = :name'),
                             {"user_id": user_id, "name": profile_name})
        existing_profile = result.fetchone()

        if existing_profile:
            conn.execute(text('''
                UPDATE profiles SET
                    salario=:salario, quinquenio=:quinquenio, vale_alimentacao=:vale_alimentacao, plano_saude=:plano_saude,
                    previdencia_privada=:previdencia_privada, odontologico=:odontologico, premiacao=:premiacao
                WHERE id=:id
            '''), {
                "salario": data['salario'], "quinquenio": data['quinquenio'], "vale_alimentacao": data['vale_alimentacao'],
                "plano_saude": data['plano_saude'], "previdencia_privada": data['previdencia_privada'],
                "odontologico": data['odontologico'], "premiacao": data['premiacao'],
                "id": existing_profile[0]
            })
        else:
            conn.execute(text('''
                INSERT INTO profiles (user_id, name, salario, quinquenio, vale_alimentacao,
                                      plano_saude, previdencia_privada, odontologico, premiacao)
                VALUES (:user_id, :name, :salario, :quinquenio, :vale_alimentacao,
                        :plano_saude, :previdencia_privada, :odontologico, :premiacao)
            '''), {
                "user_id": user_id, "name": profile_name, "salario": data['salario'], "quinquenio": data['quinquenio'],
                "vale_alimentacao": data['vale_alimentacao'], "plano_saude": data['plano_saude'],
                "previdencia_privada": data['previdencia_privada'], "odontologico": data['odontologico'],
                "premiacao": data['premiacao']
            })
        conn.commit()

def load_profile_from_db(user_id, profile_name):
    """Carrega os dados de um perfil específico de um usuário."""
    with get_db_connection() as conn:
        result = conn.execute(text('SELECT * FROM profiles WHERE user_id = :user_id AND name = :name'),
                             {"user_id": user_id, "name": profile_name})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
    return None

def get_all_profile_names(user_id):
    """Retorna uma lista de nomes de perfis para um usuário específico."""
    with get_db_connection() as conn:
        result = conn.execute(text('SELECT name FROM profiles WHERE user_id = :user_id ORDER BY name'),
                             {"user_id": user_id})
        return [row[0] for row in result.fetchall()]

# --- Tabelas de Cálculo (INSS e IRPF 2025) ---
# [2025-06-17] Os cálculos de IRPF e INSS estão corretos.
INSS_TETO_2025 = 8157.41
INSS_MAX_DESCONTO_2025 = 951.62 # (8157.41 * 0.14) - 190.40

IRPF_TABELA_2025 = [
    {"limite": 2428.80, "aliquota": 0.0, "deducao": 0.0},
    {"limite": 2826.65, "aliquota": 0.075, "deducao": 182.16},
    {"limite": 3751.05, "aliquota": 0.15, "deducao": 394.16},
    {"limite": 4664.68, "aliquota": 0.225, "deducao": 675.49},
    {"limite": float('inf'), "aliquota": 0.275, "deducao": 908.73}
]

def calcular_inss(base_calculo):
    if base_calculo >= INSS_TETO_2025:
        return INSS_MAX_DESCONTO_2025
    
    return min(base_calculo * 0.14, INSS_MAX_DESCONTO_2025) 

def calcular_irpf(base_calculo):
    desconto_irpf = 0.0
    for faixa in IRPF_TABELA_2025:
        if base_calculo <= faixa["limite"] or faixa["limite"] == float('inf'):
            desconto_irpf = (base_calculo * faixa["aliquota"]) - faixa["deducao"]
            break
    return max(0.0, desconto_irpf)

# --- Rotas de Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    html_login = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Calculadora de Salário</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; min-height: 90vh; }
            .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 400px; width: 100%; text-align: center; }
            h2 { color: #333; }
            label { display: block; text-align: left; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"] { width: calc(100% - 22px); padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            input[type="submit"] { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; }
            input[type="submit"]:hover { background-color: #45a049; }
            .link-register { margin-top: 15px; font-size: 0.9em; }
            .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: left; }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Login</h2>
            {% with messages = get_flashed_messages(with_categories=True) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <label for="username">Usuário:</label>
                <input type="text" id="username" name="username" required>
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" required>
                <input type="submit" value="Entrar">
            </form>
            <p class="link-register">Não tem uma conta? <a href="{{ url_for('register') }}">Cadastre-se aqui</a></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_login)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Usuário e senha são obrigatórios.', 'danger')
        elif add_user(username, password):
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
    
    html_register = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cadastro - Calculadora de Salário</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; min-height: 90vh; }
            .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 400px; width: 100%; text-align: center; }
            h2 { color: #333; }
            label { display: block; text-align: left; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"] { width: calc(100% - 22px); padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            input[type="submit"] { background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; }
            input[type="submit"]:hover { background-color: #007bb5; }
            .link-login { margin-top: 15px; font-size: 0.9em; }
            .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: left; }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Cadastro</h2>
            {% with messages = get_flashed_messages(with_categories=True) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <label for="username">Novo Usuário:</label>
                <input type="text" id="username" name="username" required>
                <label for="password">Nova Senha:</label>
                <input type="password" id="password" name="password" required>
                <input type="submit" value="Cadastrar">
            </form>
            <p class="link-login">Já tem uma conta? <a href="{{ url_for('login') }}">Faça login aqui</a></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_register)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

# --- Rota Principal (Protegida) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar a calculadora.', 'info')
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']

    salario_liquido = None
    profile_data = {
        'salario': 0.00, 'quinquenio': 0.00, 'vale_alimentacao': 0.00,
        'plano_saude': 0.00, 'previdencia_privada': 0.00, 'odontologico': 0.00,
        'premiacao': 0.00, 'profile_name': ''
    }
    
    # Lida com mensagens flash (sucesso/erro/info)
    # Não há necessidade de criar uma lista de mensagens aqui, o template as busca diretamente.

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            profile_data['salario'] = float(request.form.get('salario', '0').replace(',', '.'))
            profile_data['quinquenio'] = float(request.form.get('quinquenio', '0').replace(',', '.'))
            profile_data['vale_alimentacao'] = float(request.form.get('vale_alimentacao', '0').replace(',', '.'))
            profile_data['plano_saude'] = float(request.form.get('plano_saude', '0').replace(',', '.'))
            profile_data['previdencia_privada'] = float(request.form.get('previdencia_privada', '0').replace(',', '.'))
            profile_data['odontologico'] = float(request.form.get('odontologico', '0').replace(',', '.'))
            profile_data['premiacao'] = float(request.form.get('premiacao', '0').replace(',', '.'))
            profile_data['profile_name'] = request.form.get('profile_name', '').strip()

            if action == 'save_profile':
                if profile_data['profile_name']:
                    save_profile_to_db(user_id, profile_data['profile_name'], profile_data)
                    flash('Perfil salvo com sucesso!', 'success')
                    return redirect(url_for('index', load_profile=profile_data['profile_name']))
                else:
                    flash('Erro: Nome do perfil é obrigatório para salvar.', 'danger')
            else: # Default action is calculate
                total_rendimentos_base = profile_data['salario'] + profile_data['quinquenio'] + profile_data['premiacao']
                desconto_inss = calcular_inss(total_rendimentos_base)
                base_irpf = total_rendimentos_base - desconto_inss
                desconto_irpf = calcular_irpf(base_irpf)

                total_descontos = (profile_data['vale_alimentacao'] + profile_data['plano_saude'] + 
                                   profile_data['previdencia_privada'] + profile_data['odontologico'] + 
                                   desconto_inss + desconto_irpf) # Premiacao não é um desconto, é rendimento
                                   
                salario_liquido = total_rendimentos_base - total_descontos
                
        except ValueError:
            flash('Erro: Por favor, insira valores numéricos válidos.', 'danger')
        except ConnectionError: # Captura o erro de conexão do get_db_connection
            flash('Erro: Não foi possível conectar ao banco de dados. Tente novamente mais tarde.', 'danger')
            return redirect(url_for('login')) # Ou renderize uma página de erro
    
    profile_to_load = request.args.get('load_profile')
    if profile_to_load:
        loaded_data = load_profile_from_db(user_id, profile_to_load)
        if loaded_data:
            profile_data = {key: loaded_data.get(key, 0.00) for key in profile_data}
            profile_data['profile_name'] = profile_to_load
            flash('Perfil carregado. Clique em "Calcular" para ver o salário líquido.', 'info')
        else:
            flash('Erro: Perfil não encontrado ou não pertence a você.', 'danger')

    profiles = get_all_profile_names(user_id) # Pega apenas os perfis do usuário logado

    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calculadora de Salário Líquido</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
            .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
            header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            header h2 { margin: 0; }
            header .user-info { font-size: 0.9em; }
            header .user-info a { margin-left: 10px; color: #dc3545; text-decoration: none; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], select { width: calc(100% - 22px); padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            .button-group { display: flex; justify-content: space-between; margin-top: 20px;}
            .button-group button, .button-group input[type="submit"] { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; flex-grow: 1; margin: 0 5px; }
            .button-group button.secondary, .button-group input[type="submit"].secondary { background-color: #008CBA; }
            .button-group button:hover, .button-group input[type="submit"]:hover { opacity: 0.9; }
            .result { margin-top: 20px; padding: 15px; border: 1px solid #ccc; border-radius: 4px; background-color: #e9e9e9; font-size: 1.1em; text-align: center; }
            .result strong { color: #333; }
            .profile-section { border: 1px dashed #ccc; padding: 15px; margin-bottom: 20px; border-radius: 8px; background-color: #f9f9f9;}
            .profile-section label { display: inline-block; margin-right: 10px; }
            .profile-section input[type="text"] { width: auto; margin-right: 10px; display: inline-block; }
            .profile-section select { width: auto; display: inline-block; margin-right: 10px; }
            .profile-actions { margin-top: 10px; display: flex; justify-content: flex-start; align-items: center;}
            .profile-actions button { margin-right: 10px; flex-shrink: 0; }
            .profile-actions input[type="text"] { flex-grow: 1; margin-bottom: 0; }
            .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: left; }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .flash-message.warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h2>Calculadora de Salário Líquido</h2>
                <div class="user-info">
                    Olá, <strong>{{ username }}</strong>!
                    <a href="{{ url_for('logout') }}">Sair</a>
                </div>
            </header>

            {% with messages = get_flashed_messages(with_categories=True) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="profile-section">
                <h3>Gerenciar Perfis</h3>
                <label for="profile_select">Carregar Perfil:</label>
                <select id="profile_select" onchange="window.location.href='/?load_profile=' + this.value">
                    <option value="">-- Selecione um Perfil --</option>
                    {% for profile in profiles %}
                        <option value="{{ profile }}" {% if profile == request.args.get('load_profile') %}selected{% endif %}>{{ profile }}</option>
                    {% endfor %}
                </select>
                <p><small>Selecione um perfil para carregar os dados no formulário.</small></p>
            </div>

            <form method="POST">
                <input type="hidden" name="action" id="form_action" value="calculate">

                <label for="salario">Salário Base:</label>
                <input type="text" id="salario" name="salario" value="{{ '%.2f'|format(profile_data.salario)|replace('.', ',') }}" required>

                <label for="quinquenio">Quinquênio:</label>
                <input type="text" id="quinquenio" name="quinquenio" value="{{ '%.2f'|format(profile_data.quinquenio)|replace('.', ',') }}">

                <label for="premiacao">Premiação (se houver, mesmo que seja descontada):</label>
                <input type="text" id="premiacao" name="premiacao" value="{{ '%.2f'|format(profile_data.premiacao)|replace('.', ',') }}">

                <label for="vale_alimentacao">Desconto Vale Alimentação:</label>
                <input type="text" id="vale_alimentacao" name="vale_alimentacao" value="{{ '%.2f'|format(profile_data.vale_alimentacao)|replace('.', ',') }}">

                <label for="plano_saude">Desconto Plano de Saúde:</label>
                <input type="text" id="plano_saude" name="plano_saude" value="{{ '%.2f'|format(profile_data.plano_saude)|replace('.', ',') }}">
                
                <label for="previdencia_privada">Desconto Previdência (seu contracheque):</label>
                <input type="text" id="previdencia_privada" name="previdencia_privada" value="{{ '%.2f'|format(profile_data.previdencia_privada)|replace('.', ',') }}">

                <label for="odontologico">Desconto Odontológico:</label>
                <input type="text" id="odontologico" name="odontologico" value="{{ '%.2f'|format(profile_data.odontologico)|replace('.', ',') }}">
                
                <div class="button-group">
                    <input type="submit" value="Calcular" onclick="document.getElementById('form_action').value='calculate';">
                </div>
                
                <div class="profile-actions">
                    <label for="profile_name">Nome do Perfil para Salvar:</label>
                    <input type="text" id="profile_name" name="profile_name" placeholder="Ex: Meu Salário" value="{{ profile_data.profile_name }}">
                    <button type="submit" name="action" value="save_profile" class="secondary" onclick="document.getElementById('form_action').value='save_profile';">Salvar Perfil</button>
                </div>
            </form>
            
            {% if salario_liquido is not none %}
            <div class="result">
                <p>Seu Salário Líquido Estimado: <strong>R$ {{ "%.2f"|format(salario_liquido)|replace('.', ',') }}</strong></p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_form, salario_liquido=salario_liquido, profile_data=profile_data, profiles=profiles, username=username)

# Garante que o banco de dados seja inicializado quando o aplicativo Flask é iniciado.
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) # Pega a porta da variável de ambiente PORT, senão usa 5000
    app.run(host='0.0.0.0', port=port, debug=False) # '0.0.0.0' para escutar todas as interfaces, debug=False em produção
