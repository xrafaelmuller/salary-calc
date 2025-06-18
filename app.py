from flask import Flask, render_template_string, request, redirect, url_for, session, flash, get_flashed_messages
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- Importação para MongoDB ---
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError 
from datetime import datetime # Para timestamp em MongoDB

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# --- Configuração do Banco de Dados MongoDB Atlas ---
# A MONGODB_URI será injetada pelo Render via variável de ambiente.
# Em desenvolvimento local, você pode apontar para um MongoDB local.
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/') 
DATABASE_NAME = 'calculadorasalarioliquidodb' # Nome do seu banco de dados no MongoDB Atlas

# Conexão com o cliente MongoDB.
# Esta conexão é global para a aplicação Flask.
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME] 

# Coleções (equivalente a tabelas em DB relacional)
users_collection = db['users']
profiles_collection = db['profiles']

def init_db():
    """
    No MongoDB, a "inicialização" significa principalmente garantir a conexão
    e a criação de índices para otimização e unicidade.
    As coleções (equivalente a tabelas) são criadas automaticamente no primeiro insert.
    """
    try:
        # Testa a conexão com o banco de dados
        client.admin.command('ping') 
        print("Conexão com MongoDB Atlas estabelecida com sucesso!")

        # Garante índices únicos para username e para a combinação user_id+name
        users_collection.create_index('username', unique=True)
        profiles_collection.create_index([('user_id', 1), ('name', 1)], unique=True)

    except ConnectionFailure as e:
        print(f"Erro ao conectar ao MongoDB Atlas: {e}")
        raise ConnectionError("Não foi possível conectar ao banco de dados MongoDB.") from e
    except Exception as e:
        print(f"Erro ao inicializar MongoDB: {e}")
        raise

# --- Funções de Banco de Dados para Usuários (MongoDB) ---
def add_user(username, password):
    hashed_password = generate_password_hash(password)
    try:
        # MongoDB automaticamente gera um _id ao inserir
        result = users_collection.insert_one({"username": username, "password_hash": hashed_password})
        return result.inserted_id is not None
    except DuplicateKeyError: # Para quando o username já existe (graças ao índice único)
        return False

def get_user_by_username(username):
    user_doc = users_collection.find_one({"username": username})
    if user_doc:
        # MongoDB usa '_id' por padrão, renomeamos para 'id' para compatibilidade com o Flask
        user_doc['id'] = str(user_doc['_id']) 
        return user_doc
    return None

# --- Funções de Banco de Dados para Perfis (MongoDB) ---
def save_profile_to_db(user_id, profile_name, data):
    # Converte user_id para int, se vier como str da sessão.
    # No MongoDB, user_id será um número, não um ObjectId.
    user_id_int = int(user_id) 

    # Dados a serem salvos ou atualizados
    profile_data_to_save = {
        "user_id": user_id_int,
        "name": profile_name,
        "salario": data['salario'],
        "quinquenio": data['quinquenio'],
        "vale_alimentacao": data['vale_alimentacao'],
        "plano_saude": data['plano_saude'],
        "previdencia_privada": data['previdencia_privada'],
        "odontologico": data['odontologico'],
        "premiacao": data['premiacao'],
        "updated_at": datetime.now() # Adiciona/atualiza o timestamp com data e hora atual
    }

    # Tenta atualizar um perfil existente ou inserir um novo
    # O filtro {"user_id": user_id_int, "name": profile_name} garante unicidade pelo índice
    result = profiles_collection.update_one(
        {"user_id": user_id_int, "name": profile_name},
        {"$set": profile_data_to_save},
        upsert=True # Se não encontrar, insere um novo documento
    )
    return result.acknowledged # Retorna True se a operação foi bem-sucedida

def load_profile_from_db(user_id, profile_name):
    user_id_int = int(user_id) # Garante que user_id seja int
    profile_doc = profiles_collection.find_one({"user_id": user_id_int, "name": profile_name})
    if profile_doc:
        profile_doc['id'] = str(profile_doc['_id']) # Converte ObjectId para string, se necessário
        return profile_doc
    return None

def get_all_profile_names(user_id):
    user_id_int = int(user_id) # Garante que user_id seja int
    names = []
    # Projeta apenas o campo 'name' e ordena alfabeticamente
    for doc in profiles_collection.find({"user_id": user_id_int}, {"name": 1}).sort("name", 1):
        names.append(doc['name'])
    return names

def get_last_profile_name(user_id):
    user_id_int = int(user_id) # Garante que user_id seja int
    # Encontra documentos para o usuário, ordena por updated_at (decrescente) e pega o primeiro
    profile_doc = profiles_collection.find({"user_id": user_id_int}).sort("updated_at", -1).limit(1)

    # Itera sobre o cursor (espera-se no máximo 1 resultado)
    for doc in profile_doc:
        return doc['name']
    return None

# --- Tabelas de Cálculo (INSS e IRPF 2025) ---
INSS_TETO_2025 = 8157.41
INSS_MAX_DESCONTO_2025 = 951.62

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
            session['user_id'] = user['id'] # Armazena o ID como string (ObjectId convertido)
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
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: Arial, sans-serif; margin: 0; background-color: #f4f4f4; 
                display: flex; justify-content: center; align-items: center; min-height: 100vh;
                padding: 20px; box-sizing: border-box;
            }
            .container { 
                background-color: white; padding: 30px; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 400px; width: 100%; 
                text-align: center;
            }
            h2 { color: #333; margin-bottom: 20px; }
            label { display: block; text-align: left; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"] { 
                width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; 
                border-radius: 4px; box-sizing: border-box; 
            }
            input[type="submit"] { 
                background-color: #4CAF50; color: white; padding: 10px 20px; border: none; 
                border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; 
            }
            input[type="submit"]:hover { background-color: #45a049; }
            .link-register { margin-top: 15px; font-size: 0.9em; }
            .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: left; }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

            /* Media Queries for responsiveness */
            @media (max-width: 600px) {
                .container {
                    padding: 20px;
                }
            }
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
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: Arial, sans-serif; margin: 0; background-color: #f4f4f4; 
                display: flex; justify-content: center; align-items: center; min-height: 100vh;
                padding: 20px; box-sizing: border-box;
            }
            .container { 
                background-color: white; padding: 30px; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 400px; width: 100%; 
                text-align: center;
            }
            h2 { color: #333; margin-bottom: 20px; }
            label { display: block; text-align: left; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"] { 
                width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; 
                border-radius: 4px; box-sizing: border-box; 
            }
            input[type="submit"] { 
                background-color: #008CBA; color: white; padding: 10px 20px; border: none; 
                border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; 
            }
            input[type="submit"]:hover { background-color: #007bb5; }
            .link-login { margin-top: 15px; font-size: 0.9em; }
            .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: left; }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

            /* Media Queries for responsiveness */
            @media (max-width: 600px) {
                .container {
                    padding: 20px;
                }
            }
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

    # Lógica de carregamento automático do último perfil
    profile_to_load = request.args.get('load_profile')
    if not profile_to_load: # Se nenhum perfil foi explicitamente solicitado via URL
        last_profile_name = get_last_profile_name(user_id)
        if last_profile_name:
            profile_to_load = last_profile_name
            flash(f'Último perfil "{last_profile_name}" carregado automaticamente.', 'info')

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            # Tenta carregar dados do profile_data com base nos valores do formulário
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
            else: # Ação padrão é calcular
                total_rendimentos_base = profile_data['salario'] + profile_data['quinquenio'] + profile_data['premiacao']
                desconto_inss = calcular_inss(total_rendimentos_base)
                base_irpf = total_rendimentos_base - desconto_inss
                desconto_irpf = calcular_irpf(base_irpf)

                total_descontos = (profile_data['vale_alimentacao'] + profile_data['plano_saude'] + 
                                   profile_data['previdencia_privada'] + profile_data['odontologico'] + 
                                   desconto_inss + desconto_irpf)

                salario_liquido = total_rendimentos_base - total_descontos

        except ValueError:
            flash('Erro: Por favor, insira valores numéricos válidos.', 'danger')
        except ConnectionError:
            flash('Erro: Não foi possível conectar ao banco de dados. Tente novamente mais tarde.', 'danger')
            return redirect(url_for('login')) 

    # Carrega os dados do perfil após o POST ou carregamento automático
    if profile_to_load:
        loaded_data = load_profile_from_db(user_id, profile_to_load)
        if loaded_data:
            profile_data = {key: loaded_data.get(key, 0.00) for key in profile_data}
            profile_data['profile_name'] = profile_to_load
            # Não flashea novamente se já flasheou pelo auto-carregamento
            if not request.args.get('load_profile') and not request.method == 'POST':
                 flash('Perfil carregado. Clique em "Calcular" para ver o salário líquido.', 'info')
        else:
            flash('Erro: Perfil não encontrado ou não pertence a você.', 'danger')

    profiles = get_all_profile_names(user_id)

    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calculadora de Salário Líquido</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            /* Reset básico para melhor controle */
            body, h1, h2, h3, p, form, div, input, select, button, label {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                background-color: #e9eff2; 
                display: flex; 
                justify-content: center; 
                align-items: flex-start; 
                min-height: 100vh;
                padding: 20px; 
            }

            .container { 
                background-color: white; 
                padding: 30px; 
                border-radius: 12px; 
                box-shadow: 0 6px 20px rgba(0,0,0,0.1); 
                max-width: 960px; 
                width: 100%; 
                display: flex; 
                flex-direction: column; 
                gap: 25px; 
            }

            header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 15px; 
                padding-bottom: 15px; 
                border-bottom: 1px solid #eceff1; 
                flex-wrap: wrap; 
                gap: 10px; 
            }
            header h2 { 
                margin: 0; 
                font-size: 1.8em; 
                color: #334e68; 
            }
            header .user-info { 
                font-size: 0.95em; 
                color: #5a778e;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            header .user-info strong {
                color: #2b3a4a;
            }
            header .user-info a { 
                color: #d9534f; 
                text-decoration: none; 
                font-weight: bold;
                transition: color 0.3s ease;
            }
            header .user-info a:hover {
                color: #c9302c;
            }

            label { 
                display: block; 
                margin-bottom: 6px; 
                font-weight: 600; 
                color: #4a6572; 
            }
            input[type="text"], input[type="password"], select { 
                width: 100%; 
                padding: 12px; 
                margin-bottom: 15px; 
                border: 1px solid #ccd6dd; 
                border-radius: 8px; 
                font-size: 1em;
                color: #333;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
            }
            input[type="text"]:focus, input[type="password"]:focus, select:focus {
                border-color: #007bff; 
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25); 
                outline: none;
            }

            .form-section {
                border: 1px solid #e0e6ea; 
                border-radius: 10px;
                padding: 20px;
                background-color: #fcfdfe; 
                margin-bottom: 20px; 
            }
            .form-section h4 {
                color: #334e68;
                margin-bottom: 15px;
                font-size: 1.2em;
                border-bottom: 1px dashed #e0e6ea;
                padding-bottom: 10px;
            }

            .input-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
                gap: 20px; 
            }

            .button-group { 
                display: flex; 
                justify-content: flex-end; 
                gap: 15px; 
                margin-top: 15px;
                flex-wrap: wrap; 
            }
            .button-group button, .button-group input[type="submit"] { 
                background-color: #28a745; 
                color: white; 
                padding: 12px 25px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 1em; 
                font-weight: bold;
                transition: background-color 0.3s ease, transform 0.2s ease;
                flex-shrink: 0; 
            }
            .button-group button.secondary, .button-group input[type="submit"].secondary { 
                background-color: #007bff; 
            }
            .button-group button:hover, .button-group input[type="submit"]:hover { 
                background-color: #218838; 
                transform: translateY(-2px); 
            }
            .button-group button.secondary:hover, .button-group input[type="submit"].secondary:hover {
                background-color: #0056b3;
            }

            .result { 
                margin-top: 30px; 
                padding: 20px; 
                border: 1px solid #b8daff; 
                border-radius: 10px; 
                background-color: #e7f3ff; 
                font-size: 1.2em; 
                text-align: center; 
                color: #004085; 
                font-weight: bold;
            }
            .result strong { 
                color: #002752; 
                font-size: 1.3em;
            }

            /* --- Seções Colapsáveis --- */
            .collapsible-section { 
                border: 1px dashed #a7c7e0; 
                padding: 20px; 
                margin-bottom: 25px; 
                border-radius: 10px; 
                background-color: #eef7fc; 
            }
            .collapsible-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                cursor: pointer; 
            }
            .collapsible-header h3 {
                color: #334e68;
                font-size: 1.3em;
                margin: 0;
            }
            .collapsible-header button {
                background: none;
                border: none;
                color: #007bff;
                cursor: pointer;
                font-size: 1em;
                font-weight: bold;
                transition: color 0.3s ease;
                display: flex; 
                align-items: center;
                gap: 5px;
            }
            .collapsible-header button:hover {
                color: #0056b3;
                text-decoration: underline;
            }

            .collapsible-content {
                display: flex; /* Mantém flex para organização interna */
                flex-direction: column;
                gap: 15px;
                overflow: hidden; 
                max-height: 0; /* Começa oculto */
                opacity: 0; /* Começa invisível */
                transition: max-height 0.5s ease-out, opacity 0.5s ease-out; 
            }

            .collapsible-content.expanded {
                max-height: 500px; /* Valor grande o suficiente para o conteúdo */
                opacity: 1; /* Visível */
            }


            .profile-load-group {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 10px;
            }
            .profile-load-group label {
                margin-bottom: 0;
                flex-shrink: 0;
            }
            .profile-load-group select {
                flex-grow: 1; 
                min-width: 180px; 
            }
            .profile-actions { 
                display: flex; 
                flex-wrap: wrap; 
                align-items: center;
                gap: 10px; 
                margin-top: 15px; 
            }
            .profile-actions label { margin-bottom: 0; flex-shrink: 0; }
            .profile-actions input[type="text"] { flex-grow: 1; margin-bottom: 0; min-width: 150px; }
            .profile-actions button { flex-shrink: 0; }

            .flash-message { 
                padding: 12px; 
                margin-bottom: 20px; 
                border-radius: 8px; 
                text-align: left; 
                font-weight: bold;
                font-size: 0.95em;
            }
            .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .flash-message.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .flash-message.warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
            .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

            /* Media Queries para Responsividade */

            /* Desktop e Telas Maiores */
            @media (min-width: 768px) {
                form.main-form { 
                    display: flex; 
                    flex-wrap: wrap;
                    gap: 30px; 
                }
                .form-section {
                    flex: 1 1 calc(50% - 15px); 
                    margin-bottom: 0; 
                }
                .button-group {
                    width: 100%; 
                    justify-content: flex-end;
                }
                .profile-actions {
                    width: 100%;
                    justify-content: flex-start;
                }
            }

            /* Mobile e Telas Menores */
            @media (max-width: 767px) {
                body {
                    padding: 10px;
                }
                .container {
                    padding: 20px 15px; 
                    gap: 20px;
                }
                header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 5px;
                }
                header h2 {
                    font-size: 1.6em;
                }
                header .user-info {
                    flex-direction: column;
                    align-items: flex-start;
                    width: 100%;
                    gap: 5px;
                }
                .form-section {
                    padding: 15px;
                    margin-bottom: 15px;
                }
                .form-section h4 {
                    font-size: 1.1em;
                }
                .input-grid {
                    grid-template-columns: 1fr; 
                    gap: 10px;
                }
                .button-group, .profile-actions, .profile-load-group { 
                    flex-direction: column; 
                    align-items: stretch; 
                }
                .button-group button, .button-group input[type="submit"],
                .profile-actions button, .profile-actions input[type="text"],
                .profile-actions select,
                .profile-load-group select { 
                    width: 100%; 
                    margin: 0; 
                }
                .profile-section p small {
                    text-align: center;
                    width: 100%;
                }
            }
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

            <div class="collapsible-section" id="profileSection">
                <div class="collapsible-header" id="profileHeader">
                    <h3>Gerenciar Perfis</h3>
                    <button type="button" id="toggleProfileContent">Expandir <span class="arrow-icon">&#9660;</span></button>
                </div>
                <div class="collapsible-content" id="profileContent">
                    <div class="profile-load-group">
                        <label for="profile_select">Carregar Perfil:</label>
                        <select id="profile_select" onchange="window.location.href='/?load_profile=' + this.value">
                            <option value="">-- Selecione um Perfil --</option>
                            {% for profile in profiles %}
                                <option value="{{ profile }}" {% if profile == profile_data.profile_name %}selected{% endif %}>{{ profile }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <p><small>Selecione um perfil para carregar os dados no formulário.</small></p>
                    <div class="profile-actions">
                        <label for="profile_name">Nome do Perfil para Salvar:</label>
                        <input type="text" id="profile_name" name="profile_name" placeholder="Ex: Meu Salário" value="{{ profile_data.profile_name }}">
                        <button type="submit" name="action" value="save_profile" class="secondary" form="main-calc-form" onclick="document.getElementById('form_action').value='save_profile';">Salvar Perfil</button>
                    </div>
                </div>
            </div>

            <div class="collapsible-section" id="increaseSection">
                <div class="collapsible-header" id="increaseHeader">
                    <h3>Ajustar Salário por Aumento (%)</h3>
                    <button type="button" id="toggleIncreaseContent">Expandir <span class="arrow-icon">&#9660;</span></button>
                </div>
                <div class="collapsible-content" id="increaseContent">
                    <div class="input-grid">
                        <div>
                            <label for="increase_percentage">Percentual de Aumento (%):</label>
                            <input type="text" id="increase_percentage" name="increase_percentage" placeholder="Ex: 5.5">
                            <p><small>O aumento será aplicado sobre o <strong>Salário Base atual do formulário</strong>.</small></p>
                        </div>
                    </div>
                    <div class="button-group">
                        <button type="button" id="applyIncrease" class="secondary">Aplicar Aumento</button>
                        <button type="button" id="saveIncreasedProfile" class="secondary">Salvar como novo perfil</button>
                    </div>
                </div>
            </div>


            <form method="POST" class="main-form" id="main-calc-form">
                <input type="hidden" name="action" id="form_action" value="calculate">

                <div class="form-section">
                    <h4>Rendimentos</h4>
                    <div class="input-grid">
                        <div>
                            <label for="salario">Salário Base:</label>
                            <input type="text" id="salario" name="salario" value="{{ '%.2f'|format(profile_data.salario)|replace('.', ',') }}" required>
                        </div>
                        <div>
                            <label for="quinquenio">Quinquênio:</label>
                            <input type="text" id="quinquenio" name="quinquenio" value="{{ '%.2f'|format(profile_data.quinquenio)|replace('.', ',') }}">
                        </div>
                        <div>
                            <label for="premiacao">Premiação (se houver):</label>
                            <input type="text" id="premiacao" name="premiacao" value="{{ '%.2f'|format(profile_data.premiacao)|replace('.', ',') }}">
                        </div>
                    </div>
                </div>

                <div class="form-section">
                    <h4>Descontos</h4>
                    <div class="input-grid">
                        <div>
                            <label for="vale_alimentacao">Vale Alimentação:</label>
                            <input type="text" id="vale_alimentacao" name="vale_alimentacao" value="{{ '%.2f'|format(profile_data.vale_alimentacao)|replace('.', ',') }}">
                        </div>
                        <div>
                            <label for="plano_saude">Plano de Saúde:</label>
                            <input type="text" id="plano_saude" name="plano_saude" value="{{ '%.2f'|format(profile_data.plano_saude)|replace('.', ',') }}">
                        </div>
                        <div>
                            <label for="previdencia_privada">Previdência (seu contracheque):</label>
                            <input type="text" id="previdencia_privada" name="previdencia_privada" value="{{ '%.2f'|format(profile_data.previdencia_privada)|replace('.', ',') }}">
                        </div>
                        <div>
                            <label for="odontologico">Odontológico:</label>
                            <input type="text" id="odontologico" name="odontologico" value="{{ '%.2f'|format(profile_data.odontologico)|replace('.', ',') }}">
                        </div>
                    </div>
                </div>

                <div class="button-group">
                    <input type="submit" value="Calcular" onclick="document.getElementById('form_action').value='calculate';">
                </div>
            </form>

            {% if salario_liquido is not none %}
            <div class="result">
                <p>Seu Salário Líquido Estimado: <strong>R$ {{ "%.2f"|format(salario_liquido)|replace('.', ',') }}</strong></p>
            </div>
            {% endif %}
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Função genérica para toggle de seções colapsáveis
                function setupCollapsible(headerId, contentId, toggleButtonId) {
                    const header = document.getElementById(headerId);
                    const content = document.getElementById(contentId);
                    const toggleButton = document.getElementById(toggleButtonId);
                    const arrowIcon = toggleButton.querySelector('.arrow-icon');

                    if (!header || !content || !toggleButton || !arrowIcon) {
                        console.error('Um dos elementos do colapsível não foi encontrado:', {headerId, contentId, toggleButtonId});
                        return;
                    }

                    // Função para alternar o estado
                    function toggleSection() {
                        const isExpanded = content.classList.toggle('expanded');
                        arrowIcon.innerHTML = isExpanded ? '&#9650;' : '&#9660;'; // Triângulo para cima/baixo
                        toggleButton.textContent = isExpanded ? 'Recolher ' : 'Expandir ';
                        toggleButton.appendChild(arrowIcon); // Adiciona o ícone de volta
                    }

                    // Adiciona o evento de clique ao header e ao botão
                    header.addEventListener('click', toggleSection);
                    toggleButton.addEventListener('click', function(event) {
                        event.stopPropagation(); // Impede que o clique no botão propague para o header
                        toggleSection();
                    });

                    // --- Lógica de estado inicial (SEMPRE RECOLHIDO, exceto load_profile explícito) ---
                    const urlParams = new URLSearchParams(window.location.search);
                    const loadProfileParam = urlParams.get('load_profile');

                    if (contentId === 'profileContent' && loadProfileParam) { 
                        // A seção de perfis SÓ expande se houver um 'load_profile' na URL
                        content.classList.add('expanded');
                        arrowIcon.innerHTML = '&#9650;';
                        toggleButton.textContent = 'Recolher ';
                        toggleButton.appendChild(arrowIcon);
                    } else { 
                        // Para TODAS as outras situações e seções, iniciar recolhida
                        content.classList.remove('expanded');
                        arrowIcon.innerHTML = '&#9660;';
                        toggleButton.textContent = 'Expandir ';
                        toggleButton.appendChild(arrowIcon);
                    }
                }

                // Configura a seção de Perfis
                setupCollapsible('profileHeader', 'profileContent', 'toggleProfileContent');
                // Configura a seção de Aumento Salarial
                setupCollapsible('increaseHeader', 'increaseContent', 'toggleIncreaseContent');

                // --- Lógica para Aumento Salarial ---
                const applyIncreaseButton = document.getElementById('applyIncrease');
                const saveIncreasedProfileButton = document.getElementById('saveIncreasedProfile');
                const increasePercentageInput = document.getElementById('increase_percentage');
                const salarioBaseInput = document.getElementById('salario');
                const profileNameInput = document.getElementById('profile_name'); 

                if (applyIncreaseButton && salarioBaseInput && increasePercentageInput) {
                    applyIncreaseButton.addEventListener('click', function() {
                        let currentSalario = parseFloat(salarioBaseInput.value.replace(',', '.'));
                        let increasePercentage = parseFloat(increasePercentageInput.value.replace(',', '.'));

                        if (isNaN(currentSalario) || isNaN(increasePercentage)) {
                            flashMessage('Por favor, insira valores numéricos válidos para o salário e o percentual de aumento.', 'danger');
                            return;
                        }
                        if (increasePercentage < 0) {
                             flashMessage('O percentual de aumento não pode ser negativo.', 'danger');
                             return;
                        }

                        let newSalario = currentSalario * (1 + (increasePercentage / 100));
                        salarioBaseInput.value = newSalario.toFixed(2).replace('.', ',');

                        flashMessage('Salário Base atualizado com o aumento! Lembre-se de salvar o perfil se quiser manter a alteração.', 'info');
                    });
                }

                if (saveIncreasedProfileButton && salarioBaseInput && profileNameInput) {
                    saveIncreasedProfileButton.addEventListener('click', function() {
                        const newProfileName = prompt("Digite um nome para o novo perfil com o salário ajustado:");
                        if (newProfileName) {
                            profileNameInput.value = newProfileName; 
                            document.getElementById('form_action').value = 'save_profile'; 
                            document.getElementById('main-calc-form').submit(); 
                        } else if (newProfileName === "") {
                            flashMessage("O nome do perfil não pode ser vazio.", 'danger');
                        }
                    });
                }

                // Função para exibir flash messages via JS
                function flashMessage(message, category = 'info') {
                    let flashContainer = document.querySelector('.flash-messages-js-container');
                    if (!flashContainer) { 
                        const headerElement = document.querySelector('header');
                        if (headerElement) {
                            const newDiv = document.createElement('div');
                            newDiv.className = 'flash-messages-js-container';
                            headerElement.after(newDiv); 
                            flashContainer = newDiv;
                        } else {
                            console.error('Não foi possível encontrar onde inserir a mensagem flash JS.');
                            return;
                        }
                    } else { 
                        flashContainer.innerHTML = '';
                    }

                    const msgDiv = document.createElement('div');
                    msgDiv.className = `flash-message ${category}`;
                    msgDiv.textContent = message;
                    flashContainer.prepend(msgDiv); 

                    setTimeout(() => {
                        msgDiv.remove();
                    }, 5000); 
                }

            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_form, salario_liquido=salario_liquido, profile_data=profile_data, profiles=profiles, username=username)

# Garante que o banco de dados seja inicializado quando o aplicativo Flask é iniciado.
# Esta chamada vai tentar conectar ao MongoDB e criar índices.
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port, debug=False)
