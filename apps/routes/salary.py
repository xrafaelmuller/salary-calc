# apps/salarycalc/routes.py
from flask import (Blueprint, render_template, request, redirect, url_for, session, flash)
from pymongo.errors import PyMongoError
from ..services.database import (save_profile_to_db, load_profile_from_db, get_all_profile_names, get_last_profile_name, delete_profile_from_db) 
from ..services.calculations import calcular_inss, calcular_irpf


############################################################################################
# Definição do Blueprint: aponta para a pasta 'templates' DENTRO de 'salarycalc'
############################################################################################

salary_bp = Blueprint('salary', __name__, template_folder='../templates',static_folder='../static')


@salary_bp.route('/calculator', methods=['GET', 'POST'])
def calculator():
    """ Rota principal da calculadora, protegida por login. """
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar a calculadora.', 'info')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    salario_liquido = None
    active_profile_name = request.args.get('load_profile')

    profile_data = {
        'salario': 0.00, 'quinquenio': 0.00, 'vale_alimentacao': 0.00,
        'plano_saude': 0.00, 'previdencia_privada': 0.00, 'odontologico': 0.00,
        'premiacao': 0.00, 'profile_name': active_profile_name or ''
    }

    if not active_profile_name:
        last_profile_name = get_last_profile_name(user_id)
        if last_profile_name:
            return redirect(url_for('salary.calculator', load_profile=last_profile_name))

    if request.method == 'GET' and active_profile_name:
        loaded_data = load_profile_from_db(user_id, active_profile_name)
        if loaded_data:
            profile_data.update(loaded_data)
        else:
            flash('Perfil não encontrado.', 'danger')
            return redirect(url_for('salary.calculator'))

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            form_data = {
                'salario': float(request.form.get('salario', '0').replace(',', '.')),
                'quinquenio': float(request.form.get('quinquenio', '0').replace(',', '.')),
                'vale_alimentacao': float(request.form.get('vale_alimentacao', '0').replace(',', '.')),
                'plano_saude': float(request.form.get('plano_saude', '0').replace(',', '.')),
                'previdencia_privada': float(request.form.get('previdencia_privada', '0').replace(',', '.')),
                'odontologico': float(request.form.get('odontologico', '0').replace(',', '.')),
                'premiacao': float(request.form.get('premiacao', '0').replace(',', '.')),
                'profile_name': request.form.get('profile_name', '').strip()
            }
            profile_data.update(form_data)

            if action == 'save_profile':
                if form_data['profile_name']:
                    save_profile_to_db(user_id, form_data['profile_name'], form_data)
                    flash(f"Perfil '{form_data['profile_name']}' salvo com sucesso!", 'success')
                    return redirect(url_for('salary.calculator', load_profile=form_data['profile_name']))
                else:
                    flash('Nome do perfil é obrigatório para salvar.', 'warning')
            else:
                total_rendimentos_base = form_data['salario'] + form_data['quinquenio'] + form_data['premiacao']
                desconto_inss = calcular_inss(total_rendimentos_base)
                base_irpf = total_rendimentos_base - desconto_inss
                desconto_irpf = calcular_irpf(base_irpf)
                
                total_descontos = (form_data['vale_alimentacao'] + form_data['plano_saude'] + 
                                   form_data['previdencia_privada'] + form_data['odontologico'] + 
                                   desconto_inss + desconto_irpf)
                                   
                salario_liquido = total_rendimentos_base - total_descontos
        except ValueError:
            flash('Erro: Por favor, insira valores numéricos válidos.', 'danger')
        except PyMongoError as e:
            flash(f'Erro de banco de dados: {e}', 'danger')

    try:
        profiles = get_all_profile_names(user_id)
    except PyMongoError as e:
        flash(f'Não foi possível carregar a lista de perfis: {e}', 'danger')
        profiles = []


    return render_template('salarycalc/index.html', 
                           salario_liquido=salario_liquido, 
                           profile_data=profile_data, 
                           profiles=profiles,
                           active_profile=active_profile_name,
                           username=session.get('username'))

@salary_bp.route('/delete_profile/<string:profile_name>', methods=['POST'])
def delete_profile(profile_name):
    """ Rota para deletar um perfil. """
    if 'user_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    try:
        if delete_profile_from_db(user_id, profile_name):
            flash(f'Perfil "{profile_name}" excluído com sucesso!', 'success')
        else:
            flash('Erro: Perfil não encontrado ou não pertence a você.', 'danger')
    except PyMongoError as e:
        flash(f'Erro de banco de dados ao excluir o perfil: {e}', 'danger')

    return redirect(url_for('salary.calculator'))