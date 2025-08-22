# apps/auth/routes.py
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, session, flash)
from werkzeug.security import check_password_hash
from pymongo.errors import PyMongoError

# Importa as funções de banco de dados do módulo salarycalc
from apps.services.database import get_user_by_username, add_user

# Definição do Blueprint: simples, sem 'template_folder', 
# pois usará a pasta padrão configurada no app.py
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ Rota de login do usuário. """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        next_page = request.form.get('next')
        
        if not username or not password:
            flash('Usuário e senha são obrigatórios.', 'warning')
            return redirect(url_for('auth.login', next=next_page or ''))

        try:
            user = get_user_by_username(username)
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id'] 
                session['username'] = user['username']
                flash(f'Bem-vindo de volta, {user["username"].capitalize()}!', 'success')

                # Redireciona para a página de gastos se veio de lá
                if next_page == 'gastos':
                    return redirect(url_for('gastos.controle_gastos'))
                
                # O destino padrão é a calculadora
                return redirect(url_for('salary.calculator'))
            else:
                flash('Usuário ou senha inválidos.', 'danger')
        except PyMongoError as e:
            flash(f'Erro de banco de dados ao tentar fazer login: {e}', 'danger')

    # Renderiza o template de login
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """ Rota de cadastro de novo usuário. """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Usuário e senha são obrigatórios.', 'warning')
        else:
            try:
                if add_user(username, password):
                    flash('Cadastro realizado com sucesso! Faça login.', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('Nome de usuário já existe. Escolha outro.', 'danger')
            except PyMongoError as e:
                flash(f'Erro de banco de dados ao registrar: {e}', 'danger')

    # Renderiza o template de registro
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """ Rota de logout do usuário. """
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))