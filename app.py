import os
from flask import (Flask, render_template, request, redirect, url_for, 
                   session, flash, get_flashed_messages)
from werkzeug.security import check_password_hash
from pymongo.errors import ConnectionFailure

# Importando as funcionalidades dos módulos separados
from features.database import (
    init_db, add_user, get_user_by_username, save_profile_to_db, 
    load_profile_from_db, get_all_profile_names, get_last_profile_name
)
from features.calculations import calcular_inss, calcular_irpf

# Configuração do Flask para usar a pasta 'style' para CSS e 'templates' para HTML
app = Flask(__name__, static_folder='style', static_url_path='/style', template_folder='templates')
app.secret_key = os.urandom(24) 


# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id'] 
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html')

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
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

# Rota Principal (Protegida)
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
        'plano_saude': 0.00, 'previdencia_privada': 0.00, 'odontologico': 0.00,
        'premiacao': 0.00, 'profile_name': ''
    }
    
    profile_to_load = request.args.get('load_profile')
    if not profile_to_load: 
        last_profile_name = get_last_profile_name(user_id)
        if last_profile_name:
            profile_to_load = last_profile_name

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            # Coleta e conversão dos dados do formulário
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
        except ConnectionError as e:
            flash(f'Erro de conexão com o banco de dados: {e}', 'danger')
            return redirect(url_for('login')) 
    
    if profile_to_load and request.method != 'POST':
        loaded_data = load_profile_from_db(user_id, profile_to_load)
        if loaded_data:
            for key in profile_data:
                profile_data[key] = loaded_data.get(key, 0.00)
            profile_data['profile_name'] = profile_to_load
        else:
            flash('Erro: Perfil não encontrado ou não pertence a você.', 'danger')

    profiles = get_all_profile_names(user_id)

    return render_template('index.html', 
                           salario_liquido=salario_liquido, 
                           profile_data=profile_data, 
                           profiles=profiles, 
                           username=username)

# Inicialização do Banco de Dados no contexto da aplicação
try:
    with app.app_context():
        init_db()
except ConnectionError as e:
    print(f"FALHA AO INICIAR A APLICAÇÃO: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port, debug=False)