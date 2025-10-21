# apps/routes/invest.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash

from apps.services.dbInvest import (
    add_public_investment,
    get_all_investments,
    delete_public_investment,
    update_public_investment,
    get_rendimento_atual,
    update_rendimento_atual
)

invest_bp = Blueprint('invest', __name__)

LOGO_MAP = {
    'nubank': 'nubank.png',
    'nuinvest': 'nubank.png',
    'xp': 'xp.png',
    'xp investimentos': 'xp.png',
    'banco inter': 'inter.png',
    'inter': 'inter.png',
    'btg pactual': 'btg.png',
    'btg': 'btg.png',
    'bradesco': 'bradesco.png',
    'itau': 'itau.png'
}

@invest_bp.route('/invest', methods=['GET', 'POST'])
def invest_page():
    if request.method == 'POST':
        # ... (lógica do POST permanece a mesma)
        valor_str = request.form.get('valor', '0').replace('R$', '').strip().replace('.', '').replace(',', '.')
        try:
            valor_float = float(valor_str)
        except ValueError:
            flash("O valor inserido é inválido. Use um formato numérico.", "danger")
            return redirect(url_for('invest.invest_page'))

        form_data = {
            'onde': request.form.get('onde'),
            'aplicacao': request.form.get('aplicacao'),
            'valor': valor_float,
            'resgate': request.form.get('resgate'),
        }
        
        if not all(form_data.get(key) for key in ['onde', 'aplicacao', 'resgate']):
            flash("Todos os campos são obrigatórios!", "danger")
        elif add_public_investment(form_data):
            flash("Investimento adicionado com sucesso!", "success")
        else:
            flash("Erro ao adicionar o investimento.", "danger")
        
        return redirect(url_for('invest.invest_page'))

    investments_list = list(get_all_investments())
    
    # ... (lógica de formatação e cálculos permanece a mesma)
    for inv in investments_list:
        institution_key = inv.get('onde', '').lower().strip()
        logo_filename = LOGO_MAP.get(institution_key)
        inv['logo_filename'] = logo_filename
        valor = inv.get('valor', 0)
        inv['formatted_valor'] = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    total_value = sum(inv.get('valor', 0) for inv in investments_list)
    rendimento_atual_valor = get_rendimento_atual()
    saldo_bruto_valor = total_value + rendimento_atual_valor

    if total_value > 0:
        percentual_rendimento = (rendimento_atual_valor / total_value) * 100
    else:
        percentual_rendimento = 0

    if percentual_rendimento > 0.01:
        rendimento_color_class = "text-success"
    elif percentual_rendimento < -0.01:
        rendimento_color_class = "text-danger"
    else:
        rendimento_color_class = "text-muted"

    desconto_imposto = rendimento_atual_valor * 0.185
    saldo_liquido_valor = saldo_bruto_valor - desconto_imposto

    total_investido_formatado = f"{total_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    saldo_bruto_formatado = f"{saldo_bruto_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    rendimento_atual_formatado = f"{rendimento_atual_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    saldo_liquido_formatado = f"{saldo_liquido_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # REMOVIDO: A variável da senha não é mais necessária.
    # unlock_password = os.getenv('UNLOCK_PASSWORD', '123')

    return render_template(
        'invest/invest.html',
        investments=investments_list,
        total_investido=total_investido_formatado,
        saldo_bruto_formatado=saldo_bruto_formatado,
        saldo_liquido_formatado=saldo_liquido_formatado,
        rendimento_atual=rendimento_atual_valor,
        rendimento_atual_formatado=rendimento_atual_formatado,
        percentual_rendimento=percentual_rendimento,
        rendimento_color_class=rendimento_color_class
        # REMOVIDO: Não passamos mais a senha para o template.
        # unlock_password=unlock_password
    )

# As rotas delete_investment, edit_investment e update_rendimento_atual_route
# permanecem exatamente as mesmas.
@invest_bp.route('/invest/delete/<investment_id>', methods=['POST'])
def delete_investment(investment_id):
    if delete_public_investment(investment_id):
        flash("Investimento removido com sucesso!", "success")
    else:
        flash("Erro ao remover o investimento.", "danger")
    return redirect(url_for('invest.invest_page'))

@invest_bp.route('/invest/edit/<investment_id>', methods=['POST'])
def edit_investment(investment_id):
    valor_str = request.form.get('valor', '0').replace('R$', '').strip().replace('.', '').replace(',', '.')
    form_data = {
        'onde': request.form.get('onde'),
        'aplicacao': request.form.get('aplicacao'),
        'valor': valor_str,
        'resgate': request.form.get('resgate')
    }
    if not all(form_data.values()):
        flash("Todos os campos são obrigatórios para a edição!", "danger")
    elif update_public_investment(investment_id, form_data):
        flash("Investimento atualizado com sucesso!", "success")
    else:
        flash("Erro ao atualizar o investimento. Verifique os dados e tente novamente.", "danger")
    return redirect(url_for('invest.invest_page'))

@invest_bp.route('/update_rendimento_atual', methods=['POST'])
def update_rendimento_atual_route():
    # Adicione '', como valor padrão para o get()
    novo_rendimento = request.form.get('rendimento_atual', '').replace('R$', '').strip()
    
    if not update_rendimento_atual(novo_rendimento):
        flash("Erro ao atualizar o Rendimento Atual. Verifique o valor inserido.", "danger")
    # Você pode até adicionar um 'else' para feedback de sucesso
    else:
        flash("Rendimento atualizado com sucesso!", "success")
        
    return redirect(url_for('invest.invest_page'))