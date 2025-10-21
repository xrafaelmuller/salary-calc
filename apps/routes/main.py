from flask import Blueprint, render_template

############################################################################################
# Define o Blueprint para as rotas principais da aplicação.
############################################################################################
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """ Rota da página inicial (landing page). """
    return render_template('main/landing.html')

@main_bp.route('/casamento')
def casamento():
    """ Rota da página do casamento. """
    return render_template('main/jer.html')