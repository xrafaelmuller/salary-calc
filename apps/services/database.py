# apps/services/database.py

import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError
from pymongo.server_api import ServerApi
from datetime import datetime
from bson.objectid import ObjectId

load_dotenv()

# Configuração do Banco de Dados MongoDB Atlas
MONGODB_URI = os.environ.get('MONGODB_URI')
DATABASE_NAME = 'calculadorasalarioliquidodb'

try:
    client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
    db = client[DATABASE_NAME]

    users_collection = db['users']
    profiles_collection = db['profiles']
    investments_collection = db['investments']
    app_data_collection = db['app_data']

except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível inicializar a conexão com o MongoDB. {e}")
    client = None
    db = None
    users_collection = None
    profiles_collection = None
    investments_collection = None
    app_data_collection = None


def init_db():
    """Inicializa o banco de dados MongoDB, garantindo conexão e índices."""
    if client is None:
        raise ConnectionError("A conexão com o MongoDB não foi estabelecida.")
    try:
        client.admin.command('ping')
        print("Conexão com MongoDB Atlas estabelecida com sucesso!")
        
        users_collection.create_index('username', unique=True)
        profiles_collection.create_index([('user_id', 1), ('name', 1)], unique=True)
        investments_collection.create_index('user_id')
    except ConnectionFailure as e:
        print(f"Erro ao conectar ao MongoDB Atlas: {e}")
        raise ConnectionError("Não foi possível conectar ao banco de dados MongoDB.") from e
    except Exception as e:
        print(f"Erro ao inicializar MongoDB: {e}")
        raise



def add_user(username, password):
    """Adiciona um novo usuário ao banco de dados."""
    if users_collection is None:
        raise ConnectionError("Coleção de usuários não está disponível.")
    hashed_password = generate_password_hash(password)
    try:
        result = users_collection.insert_one({"username": username, "password_hash": hashed_password})
        return result.inserted_id is not None
    except DuplicateKeyError: 
        return False

def get_user_by_username(username):
    """Obtém um usuário pelo nome de usuário."""
    if users_collection is None:
        raise ConnectionError("Coleção de usuários não está disponível.")
    user_doc = users_collection.find_one({"username": username})
    if user_doc:
        user_doc['id'] = str(user_doc['_id']) 
        return user_doc
    return None

def save_user_status(user_id, new_status_value):
    """Salva o valor da situação atual para um usuário específico."""
    if users_collection is None:
        return False
    try:
        valor_str = str(new_status_value).replace('.', '').replace(',', '.')
        valor_float = float(valor_str)
        
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'situacao_atual': valor_float}}
        )
        return True
    except Exception as e:
        print(f"Erro ao salvar situação do usuário: {e}")
        return False

def get_user_status(user_id):
    """Busca o valor da situação atual para um usuário específico."""
    if users_collection is None:
        return 0.0
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        return user.get('situacao_atual', 0.0)
    except Exception as e:
        print(f"Erro ao buscar situação do usuário: {e}")
        return 0.0