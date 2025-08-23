# apps/routes/gastos.py
from flask import Blueprint, render_template, session, flash, redirect, url_for

# Cria o Blueprint para o módulo de gastos
gastos_bp = Blueprint('gastos', __name__)

@gastos_bp.route('/gastos')
def controle_gastos():
    """ Rota para a página de controle de gastos, protegida por login. """
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar o controle de gastos.', 'info')
        # Lembre-se que o url_for para login agora é 'auth.login'
        return redirect(url_for('auth.login', next='gastos'))

    return render_template('gastos/gastos.html', 
                           username=session.get('username'))

# Crie um Blueprint para as rotas da API
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/gastos/accounts', methods=['GET'])
@login_required
def get_accounts():
    """Endpoint para buscar todas as contas do usuário logado."""
    try:
        accounts = get_accounts_by_user(current_user.id)
        return jsonify(accounts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/gastos/accounts', methods=['POST'])
@login_required
def create_account():
    """Endpoint para adicionar uma nova conta."""
    data = request.get_json()
    if not data or 'name' not in data or 'balance' not in data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    try:
        new_account_id = add_account(current_user.id, data)
        # Retorna a conta recém-criada
        new_account = data
        new_account['id'] = new_account_id
        return jsonify(new_account), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/gastos/accounts/<string:account_id>', methods=['PUT'])
@login_required
def edit_account(account_id):
    """Endpoint para atualizar uma conta existente."""
    data = request.get_json()
    try:
        success = update_account(current_user.id, account_id, data)
        if success:
            return jsonify({"message": "Conta atualizada com sucesso"})
        else:
            return jsonify({"error": "Conta não encontrada ou permissão negada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/gastos/accounts/<string:account_id>', methods=['DELETE'])
@login_required
def remove_account_endpoint(account_id):
    """Endpoint para deletar uma conta."""
    try:
        # Primeiro, precisamos verificar se a conta não está bloqueada
        # (Essa lógica pode ser mais complexa, mas vamos simplificar por agora)
        # account = get_account_by_id(account_id) -> você pode criar essa função se precisar
        # if account and account.get('locked'):
        #    return jsonify({"error": "Não é possível deletar uma conta bloqueada"}), 403

        success = delete_account(current_user.id, account_id)
        if success:
            return jsonify({"message": "Conta deletada com sucesso"})
        else:
            return jsonify({"error": "Conta não encontrada ou permissão negada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Não se esqueça de registrar o Blueprint no seu app Flask principal
# app.register_blueprint(api_bp)