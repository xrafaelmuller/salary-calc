# apps/auth/routes.py
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, session, flash)
from werkzeug.security import check_password_hash
from pymongo.errors import PyMongoError
from apps.services.database import get_user_by_username, add_user

############################################################################################
# Define o Blueprint para as rotas de autenticação da aplicação.
############################################################################################
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
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

                if next_page == 'gastos':
                    return redirect(url_for('gastos.controle_gastos'))
                
                return redirect(url_for('salary.calculator'))
            else:
                flash('Usuário ou senha inválidos.', 'danger')
        except PyMongoError as e:
            flash(f'Erro de banco de dados ao tentar fazer login: {e}', 'danger')

    return render_template('auth/login.html')



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))