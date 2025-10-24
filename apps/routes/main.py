from flask import Blueprint, render_template

############################################################################################
# Define o Blueprint para as rotas principais da aplicação.
############################################################################################
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """Rota da página inicial (landing page principal)."""
    return render_template('main/landing.html')


@main_bp.route('/casamento')
def casamento():
    """Rota da página do casamento."""
    return render_template('main/jer.html')


@main_bp.route('/pcdonery')
def pcdonery():
    """Rota da landing page dos computadores PCDonery."""
    return render_template('main/pcdonery.html')
