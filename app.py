from flask import Flask, render_template_string, request, redirect, url_for, session, flash, get_flashed_messages
import os
from werkzeug.security import generate_password_hash, check_password_hash

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from pymongo.server_api import ServerApi
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração do Banco de Dados MongoDB Atlas
MONGODB_URI = os.environ.get('MONGODB_URI')
DATABASE_NAME = 'calculadorasalarioliquidodb'

client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = client[DATABASE_NAME]

users_collection = db['users']
profiles_collection = db['profiles']

def init_db():
    """Inicializa o banco de dados MongoDB, garantindo conexão e índices."""
    try:
        client.admin.command('ping')
        print("Conexão com MongoDB Atlas estabelecida com sucesso!")
        
        users_collection.create_index('username', unique=True)
        profiles_collection.create_index([('user_id', 1), ('name', 1)], unique=True)

    except ConnectionFailure as e:
        print(f"Erro ao conectar ao MongoDB Atlas: {e}")
        raise ConnectionError("Não foi possível conectar ao banco de dados. Verifique a URI de conexão e o status do servidor.")


# Funções de cálculo (IRPF e INSS) - Mantenha as que você já possui
# Certifique-se de que estas funções estão corretas conforme sua necessidade
def calcular_inss(salario_bruto):
    if salario_bruto <= 1412.00:
        return salario_bruto * 0.075
    elif salario_bruto <= 2666.68:
        return (1412.00 * 0.075) + ((salario_bruto - 1412.00) * 0.09)
    elif salario_bruto <= 4000.03:
        return (1412.00 * 0.075) + ((2666.68 - 1412.00) * 0.09) + ((salario_bruto - 2666.68) * 0.12)
    elif salario_bruto <= 7786.02:
        return (1412.00 * 0.075) + ((2666.68 - 1412.00) * 0.09) + ((4000.03 - 2666.68) * 0.12) + ((salario_bruto - 4000.03) * 0.14)
    else:
        return 908.85 # Teto do INSS para 2024 (7786.02 * 0.14)

def calcular_irpf(base_calculo):
    if base_calculo <= 2259.20:
        return 0
    elif base_calculo <= 2826.65:
        return (base_calculo * 0.075) - 169.44
    elif base_calculo <= 3751.05:
        return (base_calculo * 0.15) - 381.58
    elif base_calculo <= 4664.68:
        return (base_calculo * 0.225) - 662.90
    else:
        return (base_calculo * 0.275) - 896.00


# Funções para gerenciamento de perfil
def get_all_profile_names(user_id_str):
    """Retorna uma lista de nomes de perfis para um usuário."""
    user_id_obj = ObjectId(user_id_str)
    profiles = profiles_collection.find({"user_id": user_id_obj}, {"name": 1}).sort("name", 1)
    return [p['name'] for p in profiles]

def get_last_profile_name(user_id_str):
    """Retorna o nome do último perfil salvo/atualizado pelo usuário."""
    user_id_obj = ObjectId(user_id_str)
    last_profile = profiles_collection.find({"user_id": user_id_obj}).sort("updated_at", -1).limit(1)
    if last_profile and last_profile.count() > 0:
        return last_profile[0]['name']
    return None

def save_profile_to_db(user_id_str, profile_name, data):
    """Salva ou atualiza um perfil para um usuário específico."""
    user_id_obj = ObjectId(user_id_str)

    profile_data_to_save = {
        "user_id": user_id_obj,
        "name": profile_name,
        "salario": data['salario'],
        "quinquenio": data['quinquenio'],
        "vale_alimentacao": data['vale_alimentacao'],
        "plano_saude": data['plano_saude'],
        "previdencia_privada": data['previdencia_privada'], # Manter este para valor fixo
        "previdencia_percentual": data.get('previdencia_percentual', 0.0), # NOVO CAMPO: guardar a porcentagem
        "odontologico": data['odontologico'],
        "premiacao": data['premiacao'],
        "updated_at": datetime.now()
    }

    result = profiles_collection.update_one(
        {"user_id": user_id_obj, "name": profile_name},
        {"$set": profile_data_to_save},
        upsert=True
    )
    return result.acknowledged

def load_profile_from_db(user_id_str, profile_name):
    """Carrega os dados de um perfil específico de um usuário."""
    user_id_obj = ObjectId(user_id_str)
    profile_doc = profiles_collection.find_one({"user_id": user_id_obj, "name": profile_name})
    if profile_doc:
        profile_doc['id'] = str(profile_doc['_id'])
        # Adicionar o campo de percentual ao carregamento, com default 0.0
        if 'previdencia_percentual' not in profile_doc:
            profile_doc['previdencia_percentual'] = 0.0
        return profile_doc
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({"username": username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Calculadora</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e9eff2; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                .login-container { background-color: white; padding: 40px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
                h1 { color: #334e68; margin-bottom: 25px; font-size: 2em; }
                label { display: block; text-align: left; margin-bottom: 8px; font-weight: 600; color: #4a6572; }
                input[type="text"], input[type="password"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 20px; border: 1px solid #ccd6dd; border-radius: 8px; font-size: 1em; color: #333; transition: border-color 0.3s ease, box-shadow 0.3s ease; }
                input[type="text"]:focus, input[type="password"]:focus { border-color: #007bff; box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25); outline: none; }
                button { background-color: #007bff; color: white; padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background-color 0.3s ease, transform 0.2s ease; width: 100%; }
                button:hover { background-color: #0056b3; transform: translateY(-2px); }
                .register-link { margin-top: 20px; font-size: 0.9em; color: #5a778e; }
                .register-link a { color: #28a745; text-decoration: none; font-weight: bold; transition: color 0.3s ease; }
                .register-link a:hover { color: #218838; }
                .flash-message { padding: 12px; margin-bottom: 20px; border-radius: 8px; text-align: left; font-weight: bold; font-size: 0.95em; }
                .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .flash-message.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
                .flash-message.warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
                .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>Login</h1>
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
                    <button type="submit">Entrar</button>
                </form>
                <p class="register-link">Não tem uma conta? <a href="{{ url_for('register') }}">Registre-se aqui</a></p>
            </div>
        </body>
        </html>
    """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            users_collection.insert_one({'username': username, 'password': hashed_password})
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except DuplicateKeyError:
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
        except Exception as e:
            flash(f'Erro ao registrar: {e}', 'danger')
            
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Registro - Calculadora</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e9eff2; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                .register-container { background-color: white; padding: 40px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
                h1 { color: #334e68; margin-bottom: 25px; font-size: 2em; }
                label { display: block; text-align: left; margin-bottom: 8px; font-weight: 600; color: #4a6572; }
                input[type="text"], input[type="password"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 20px; border: 1px solid #ccd6dd; border-radius: 8px; font-size: 1em; color: #333; transition: border-color 0.3s ease, box-shadow 0.3s ease; }
                input[type="text"]:focus, input[type="password"]:focus { border-color: #007bff; box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25); outline: none; }
                button { background-color: #28a745; color: white; padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background-color 0.3s ease, transform 0.2s ease; width: 100%; }
                button:hover { background-color: #218838; transform: translateY(-2px); }
                .login-link { margin-top: 20px; font-size: 0.9em; color: #5a778e; }
                .login-link a { color: #007bff; text-decoration: none; font-weight: bold; transition: color 0.3s ease; }
                .login-link a:hover { color: #0056b3; }
                .flash-message { padding: 12px; margin-bottom: 20px; border-radius: 8px; text-align: left; font-weight: bold; font-size: 0.95em; }
                .flash-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .flash-message.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
                .flash-message.warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
                .flash-message.danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <div class="register-container">
                <h1>Registro</h1>
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
                    <button type="submit">Registrar</button>
                </form>
                <p class="login-link">Já tem uma conta? <a href="{{ url_for('login') }}">Faça login aqui</a></p>
            </div>
        </body>
        </html>
    """)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar o perfil da sua calculadora .', 'info')
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']

    salario_liquido = None
    profile_data = {
        'salario': 0.00, 'quinquenio': 0.00, 'vale_alimentacao': 0.00,
        'plano_saude': 0.00, 'previdencia_privada': 0.00,
        'previdencia_percentual': 0.0, # NOVO: Inicializar o percentual
        'odontologico': 0.00, 'premiacao': 0.00, 'profile_name': ''
    }

    profile_to_load = request.args.get('load_profile')
    if not profile_to_load:
        last_profile_name = get_last_profile_name(user_id)
        if last_profile_name:
            profile_to_load = last_profile_name

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            profile_data['salario'] = float(request.form.get('salario', '0').replace(',', '.'))
            profile_data['quinquenio'] = float(request.form.get('quinquenio', '0').replace(',', '.'))
            profile_data['vale_alimentacao'] = float(request.form.get('vale_alimentacao', '0').replace(',', '.'))
            profile_data['plano_saude'] = float(request.form.get('plano_saude', '0').replace(',', '.'))
            profile_data['odontologico'] = float(request.form.get('odontologico', '0').replace(',', '.'))
            profile_data['premiacao'] = float(request.form.get('premiacao', '0').replace(',', '.'))
            profile_data['profile_name'] = request.form.get('profile_name', '').strip()

            # Lógica para previdência privada: valor fixo ou percentual
            previdencia_tipo = request.form.get('previdencia_tipo') # 'valor_fixo' ou 'porcentagem'
            if previdencia_tipo == 'porcentagem':
                previdencia_percentual_str = request.form.get('previdencia_percentual_input', '0').replace(',', '.')
                profile_data['previdencia_percentual'] = float(previdencia_percentual_str)
                # O valor fixo é zerado se for por porcentagem para evitar duplicação ou confusão na persistência
                profile_data['previdencia_privada'] = 0.0
            else: # 'valor_fixo'
                previdencia_fixa_str = request.form.get('previdencia_privada_input_valor_fixo', '0').replace(',', '.')
                profile_data['previdencia_privada'] = float(previdencia_fixa_str)
                # O percentual é zerado se for por valor fixo
                profile_data['previdencia_percentual'] = 0.0


            if action == 'save_profile':
                if profile_data['profile_name']:
                    # Antes de salvar, garantimos que o valor da previdencia_privada
                    # corresponde ao que seria usado no cálculo, se fosse porcentagem.
                    # Mas para o salvamento, já temos os dois campos separados.
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

                # Calcular Previdência Privada com base na escolha
                desconto_previdencia_privada = profile_data['previdencia_privada'] # Começa com o valor fixo
                if profile_data['previdencia_percentual'] > 0:
                    desconto_previdencia_privada = total_rendimentos_base * (profile_data['previdencia_percentual'] / 100)

                total_descontos = (profile_data['vale_alimentacao'] + profile_data['plano_saude'] +
                                   desconto_previdencia_privada + # Usar o valor calculado/fixo
                                   profile_data['odontologico'] +
                                   desconto_inss + desconto_irpf)

                salario_liquido = total_rendimentos_base - total_descontos

        except ValueError:
            flash('Erro: Por favor, insira valores numéricos válidos.', 'danger')
        except ConnectionError:
            flash('Erro: Não foi possível conectar ao banco de dados. Tente novamente mais tarde.', 'danger')
            return redirect(url_for('login'))

    if profile_to_load:
        loaded_data = load_profile_from_db(user_id, profile_to_load)
        if loaded_data:
            # Copiar dados carregados para profile_data, incluindo o novo campo
            for key in profile_data:
                profile_data[key] = loaded_data.get(key, 0.00)
            profile_data['profile_name'] = profile_to_load
            # Se for carregado um perfil que não tinha previdencia_percentual, ele virá como 0.0, o que é OK
            # Se o valor fixo de previdencia_privada for 0, mas previdencia_percentual > 0,
            # definimos o tipo de seleção para porcentagem.
            # Caso contrário, será valor fixo.
            if profile_data['previdencia_percentual'] > 0.001: # Usar uma pequena margem para float comparisons
                 profile_data['previdencia_tipo_selecionado'] = 'porcentagem'
            else:
                 profile_data['previdencia_tipo_selecionado'] = 'valor_fixo'

        else:
            flash('Erro: Perfil não encontrado ou não pertence a você.', 'danger')
    else: # Primeiro carregamento da página ou sem perfil carregado, define o tipo padrão
        profile_data['previdencia_tipo_selecionado'] = 'valor_fixo' # Default para 'valor_fixo'


    profiles = get_all_profile_names(user_id)

    # Resto do HTML
    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calculadora de Salário Líquido</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            /* Seu CSS existente */
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
            /* Novo estilo para o container da previdência */
            .previdencia-options {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .previdencia-options .radio-group {
                display: flex;
                gap: 15px;
                margin-bottom: 5px;
                align-items: center;
            }
            .previdencia-options .radio-group label {
                margin-bottom: 0;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .previdencia-options .input-container {
                width: 100%;
            }
            .previdencia-options .input-container select,
            .previdencia-options .input-container input[type="text"] {
                margin-bottom: 0; /* Remover margin-bottom padrão */
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
            .button-group button.secondary:hover, .button-group input[type="submit"]:hover {
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
                display: flex;
                flex-direction: column;
                gap: 15px;
                overflow: hidden;
                max-height: 0;
                opacity: 0;
                transition: max-height 0.5s ease-out, opacity 0.5s ease-out;
            }

            .collapsible-content.expanded {
                max-height: 500px;
                opacity: 1;
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
                        <div class="profile-actions">
                            <label for="profile_name">Nome do Perfil para Salvar:</label>
                            <input type="text" id="profile_name" name="profile_name" placeholder="Ex: Meu Salário" value="{{ profile_data.profile_name }}" form="main-calc-form">
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
                            <button type="button" id="resetSalario" class="secondary">Resetar Salário Base</button>
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
                                <label>Previdência (seu contracheque):</label>
                                <div class="previdencia-options">
                                    <div class="radio-group">
                                        <input type="radio" id="previdencia_tipo_valor_fixo" name="previdencia_tipo" value="valor_fixo" {% if profile_data.previdencia_tipo_selecionado == 'valor_fixo' %}checked{% endif %}>
                                        <label for="previdencia_tipo_valor_fixo">Valor Fixo</label>

                                        <input type="radio" id="previdencia_tipo_porcentagem" name="previdencia_tipo" value="porcentagem" {% if profile_data.previdencia_tipo_selecionado == 'porcentagem' %}checked{% endif %}>
                                        <label for="previdencia_tipo_porcentagem">Porcentagem (%)</label>
                                    </div>

                                    <div class="input-container" id="container_previdencia_valor_fixo">
                                        <input type="text" id="previdencia_privada_input_valor_fixo" name="previdencia_privada_input_valor_fixo" placeholder="Ex: 150.00" value="{{ '%.2f'|format(profile_data.previdencia_privada)|replace('.', ',') }}">
                                    </div>

                                    <div class="input-container" id="container_previdencia_porcentagem" style="display:none;">
                                        <select id="previdencia_percentual_input" name="previdencia_percentual_input">
                                            <option value="">-- Selecione a Porcentagem --</option>
                                            {% for i in range(1, 41) %} {# 0.1 * i para ir de 0.1 a 4.0 #}
                                                {% set val = (i * 0.1) %}
                                                <option value="{{ '%.1f'|format(val) }}" {% if '%.1f'|format(profile_data.previdencia_percentual) == '%.1f'|format(val) %}selected{% endif %}>{{ '%.1f'|format(val) }}%</option>
                                            {% endfor %}
                                        </select>
                                    </div>
                                </div>
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
                    function setupCollapsible(headerId, contentId, toggleButtonId) {
                        const header = document.getElementById(headerId);
                        const content = document.getElementById(contentId);
                        const toggleButton = document.getElementById(toggleButtonId);
                        const arrowIcon = toggleButton.querySelector('.arrow-icon');

                        if (!header || !content || !toggleButton || !arrowIcon) {
                            console.error('Elemento colapsível não encontrado:', {headerId, contentId, toggleButtonId});
                            return;
                        }

                        function toggleSection() {
                            const isExpanded = content.classList.toggle('expanded');
                            arrowIcon.innerHTML = isExpanded ? '&#9650;' : '&#9660;';
                            toggleButton.textContent = isExpanded ? 'Recolher ' : 'Expandir ';
                            toggleButton.appendChild(arrowIcon);
                        }

                        header.addEventListener('click', toggleSection);
                        toggleButton.addEventListener('click', function(event) {
                            event.stopPropagation();
                            toggleSection();
                        });

                        const urlParams = new URLSearchParams(window.location.search);
                        const loadProfileParam = urlParams.get('load_profile');

                        if (contentId === 'profileContent' && loadProfileParam) {
                            content.classList.add('expanded');
                            arrowIcon.innerHTML = '&#9650;';
                            toggleButton.textContent = 'Recolher ';
                            toggleButton.appendChild(arrowIcon);
                        } else {
                            content.classList.remove('expanded');
                            arrowIcon.innerHTML = '&#9660;';
                            toggleButton.textContent = 'Expandir ';
                            toggleButton.appendChild(arrowIcon);
                        }
                    }

                    setupCollapsible('profileHeader', 'profileContent', 'toggleProfileContent');
                    setupCollapsible('increaseHeader', 'increaseContent', 'toggleIncreaseContent');

                    const applyIncreaseButton = document.getElementById('applyIncrease');
                    const saveIncreasedProfileButton = document.getElementById('saveIncreasedProfile');
                    const increasePercentageInput = document.getElementById('increase_percentage');
                    const salarioBaseInput = document.getElementById('salario');
                    const profileNameInput = document.getElementById('profile_name');
                    const resetSalarioButton = document.getElementById('resetSalario');

                    let originalSalarioBase = parseFloat(salarioBaseInput.value.replace(',', '.'));

                    if (applyIncreaseButton && salarioBaseInput && increasePercentageInput) {
                        applyIncreaseButton.addEventListener('click', function() {
                            let currentSalario = parseFloat(salarioBaseInput.value.replace(',', '.'));
                            let increasePercentage = parseFloat(increasePercentageInput.value.replace(',', '.'));

                            if (isNaN(currentSalario) || isNaN(increasePercentage)) {
                                flashMessage('Por favor, insira valores numéricos válidos.', 'danger');
                                return;
                            }
                            if (increasePercentage < 0) {
                                 flashMessage('O percentual de aumento não pode ser negativo.', 'danger');
                                 return;
                            }

                            let newSalario = currentSalario * (1 + (increasePercentage / 100));
                            salarioBaseInput.value = newSalario.toFixed(2).replace('.', ',');

                            flashMessage('Salário Base atualizado com o aumento! Lembre-se de salvar o perfil.', 'info');
                        });
                    }

                    if (resetSalarioButton && salarioBaseInput && increasePercentageInput) {
                        resetSalarioButton.addEventListener('click', function() {
                            salarioBaseInput.value = originalSalarioBase.toFixed(2).replace('.', ',');
                            increasePercentageInput.value = ''; // Limpa o campo de aumento
                            flashMessage('Salário Base resetado para o valor original do perfil.', 'info');
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

                    // Lógica para a Previdência Privada (Valor Fixo vs. Porcentagem)
                    const radioValorFixo = document.getElementById('previdencia_tipo_valor_fixo');
                    const radioPorcentagem = document.getElementById('previdencia_tipo_porcentagem');
                    const containerValorFixo = document.getElementById('container_previdencia_valor_fixo');
                    const containerPorcentagem = document.getElementById('container_previdencia_porcentagem');
                    const previdenciaPercentualSelect = document.getElementById('previdencia_percentual_input');
                    const previdenciaValorFixoInput = document.getElementById('previdencia_privada_input_valor_fixo');


                    function togglePrevidenciaInput() {
                        if (radioValorFixo.checked) {
                            containerValorFixo.style.display = 'block';
                            containerPorcentagem.style.display = 'none';
                            // Limpar o valor da porcentagem quando muda para valor fixo
                            previdenciaPercentualSelect.value = "";
                        } else {
                            containerValorFixo.style.display = 'none';
                            containerPorcentagem.style.display = 'block';
                            // Limpar o valor fixo quando muda para porcentagem
                            previdenciaValorFixoInput.value = "0,00";
                        }
                    }

                    // Adicionar listeners para os botões de rádio
                    radioValorFixo.addEventListener('change', togglePrevidenciaInput);
                    radioPorcentagem.addEventListener('change', togglePrevidenciaInput);

                    // Inicializar a exibição correta ao carregar a página
                    togglePrevidenciaInput();

                    // Adicionar um listener para quando o perfil for carregado do dropdown
                    // (Isso já é tratado pelo Flask com o 'selected' no option e pelo 'togglePrevidenciaInput' no DOMContentLoaded)
                    // Mas precisamos garantir que, se o perfil for carregado via query param,
                    // a seleção correta do rádio e o campo correspondente sejam exibidos.
                    // Isso é feito pelo Flask setando 'profile_data.previdencia_tipo_selecionado'
                    // e pelo `togglePrevidenciaInput` que é chamado no DOMContentLoaded.


                });
            </script>
        </body>
        </html>
        """
    return render_template_string(html_form, salario_liquido=salario_liquido, profile_data=profile_data, profiles=profiles, username=username)

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)