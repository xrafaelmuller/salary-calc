# apps/routes/contas.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from apps.services.dbContas import (
    add_transaction,
    get_all_transactions,
    delete_transaction,
    update_transaction
)

contas_bp = Blueprint('contas', __name__)

ICON_MAP = {
    'salário': 'fas fa-dollar-sign', 'renda': 'fas fa-dollar-sign',
    'moradia': 'fas fa-home', 'aluguel': 'fas fa-home', 'contas': 'fas fa-receipt',
    'alimentação': 'fas fa-utensils', 'mercado': 'fas fa-shopping-cart',
    'transporte': 'fas fa-car', 'lazer': 'fas fa-glass-cheers',
    'saúde': 'fas fa-heartbeat', 'investimento': 'fas fa-chart-line',
    'educação': 'fas fa-book-open', 'outros': 'fas fa-box'
}
DEFAULT_ICON = 'fas fa-question-circle'

def get_icon_for_category(category):
    category_lower = category.lower()
    for key, icon in ICON_MAP.items():
        if key in category_lower:
            return icon
    return DEFAULT_ICON

@contas_bp.route('/contas', methods=['GET', 'POST'])
def contas_page():
    if request.method == 'POST':
        try:
            valor_str = request.form.get('valor', '0').replace('.', '').replace(',', '.')
            form_data = {
                'tipo': request.form.get('tipo'), 'descricao': request.form.get('descricao'),
                'categoria': request.form.get('categoria'), 'valor': valor_str,
                'data': datetime.now().strftime('%Y-%m-%d')
            }
            if not all(form_data.get(key) for key in ['tipo', 'descricao', 'categoria', 'valor']):
                flash("Todos os campos do lançamento são obrigatórios.", "danger")
            elif add_transaction(form_data):
                flash("Lançamento adicionado com sucesso!", "success")
            else:
                flash("Erro ao adicionar lançamento.", "danger")
        except ValueError:
            flash("Valor inserido para o lançamento é inválido.", "danger")
        return redirect(url_for('contas.contas_page'))

    transactions = get_all_transactions()
    
    entradas_list, saidas_list = [], []
    total_entradas, total_saidas = 0, 0

    for t in transactions:
        valor = t.get('valor', 0)
        t['formatted_valor'] = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        t['icon_class'] = get_icon_for_category(t.get('categoria', ''))
        
        if t['tipo'] == 'entrada':
            total_entradas += valor
            entradas_list.append(t)
        elif t['tipo'] == 'saida':
            total_saidas += valor
            saidas_list.append(t)
            
    saldo_geral = total_entradas - total_saidas

    total_entradas_fmt = f"{total_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    total_saidas_fmt = f"{total_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    saldo_geral_fmt = f"{saldo_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # CORREÇÃO APLICADA AQUI:
    # Garantindo que os nomes das variáveis passadas ao template sejam os mesmos usados no HTML.
    return render_template(
        'contas/contas.html',
        total_entradas_fmt=total_entradas_fmt,
        total_saidas_fmt=total_saidas_fmt,
        saldo_geral_fmt=saldo_geral_fmt,
        entradas_list=entradas_list,
        saidas_list=saidas_list
    )

@contas_bp.route('/contas/edit/<transaction_id>', methods=['POST'])
def edit_trans(transaction_id):
    form_data = {
        'descricao': request.form.get('descricao'), 'categoria': request.form.get('categoria'),
        'valor': request.form.get('valor'), 'tipo': request.form.get('tipo')
    }
    if update_transaction(transaction_id, form_data):
        flash("Lançamento atualizado com sucesso!", "success")
    else:
        flash("Erro ao atualizar o lançamento.", "danger")
    return redirect(url_for('contas.contas_page'))

@contas_bp.route('/contas/delete_transaction/<transaction_id>', methods=['POST'])
def delete_trans(transaction_id):
    if delete_transaction(transaction_id):
        flash("Lançamento removido com sucesso!", "success")
    else:
        flash("Erro ao remover o lançamento.", "danger")
    return redirect(url_for('contas.contas_page'))