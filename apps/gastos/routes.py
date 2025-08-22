# apps/gastos/routes.py
from flask import Blueprint, render_template, session, flash, redirect, url_for

# Cria o Blueprint para o módulo de gastos
gastos_bp = Blueprint('gastos', __name__, template_folder='templates')

@gastos_bp.route('/gastos')
def controle_gastos():
    """ Rota para a página de controle de gastos, protegida por login. """
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar o controle de gastos.', 'info')
        return redirect(url_for('auth.login', next='gastos'))

    return render_template('gastos/gastos.html', 
                           username=session.get('username'))