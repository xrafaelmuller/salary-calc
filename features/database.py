import os
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from pymongo.server_api import ServerApi
from datetime import datetime
from bson.objectid import ObjectId

# Configuração do Banco de Dados MongoDB Atlas
MONGODB_URI = os.environ.get('MONGODB_URI')
DATABASE_NAME = 'calculadorasalarioliquidodb'

try:
    client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
    db = client[DATABASE_NAME]

    users_collection = db['users']
    profiles_collection = db['profiles']
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível inicializar a conexão com o MongoDB. {e}")
    # Em uma aplicação real, você poderia usar um logger ou um sistema de alerta aqui.
    client = None
    db = None
    users_collection = None
    profiles_collection = None


def init_db():
    """Inicializa o banco de dados MongoDB, garantindo conexão e índices."""
    if not client:
        raise ConnectionError("A conexão com o MongoDB não foi estabelecida.")
    try:
        client.admin.command('ping')
        print("Conexão com MongoDB Atlas estabelecida com sucesso!")
        
        users_collection.create_index('username', unique=True)
        profiles_collection.create_index([('user_id', 1), ('name', 1)], unique=True)

    except ConnectionFailure as e:
        print(f"Erro ao conectar ao MongoDB Atlas: {e}")
        raise ConnectionError("Não foi possível conectar ao banco de dados MongoDB.") from e
    except Exception as e:
        print(f"Erro ao inicializar MongoDB: {e}")
        raise

def add_user(username, password):
    """Adiciona um novo usuário ao banco de dados."""
    if not users_collection:
        raise ConnectionError("Coleção de usuários não está disponível.")
    hashed_password = generate_password_hash(password)
    try:
        result = users_collection.insert_one({"username": username, "password_hash": hashed_password})
        return result.inserted_id is not None
    except DuplicateKeyError: 
        return False

def get_user_by_username(username):
    """Obtém um usuário pelo nome de usuário."""
    if not users_collection:
        raise ConnectionError("Coleção de usuários não está disponível.")
    user_doc = users_collection.find_one({"username": username})
    if user_doc:
        user_doc['id'] = str(user_doc['_id']) 
        return user_doc
    return None

def save_profile_to_db(user_id_str, profile_name, data):
    """Salva ou atualiza um perfil para um usuário específico."""
    if not profiles_collection:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 

    profile_data_to_save = {
        "user_id": user_id_obj, 
        "name": profile_name,
        "salario": data['salario'],
        "quinquenio": data['quinquenio'],
        "vale_alimentacao": data['vale_alimentacao'],
        "plano_saude": data['plano_saude'],
        "previdencia_privada": data['previdencia_privada'],
        "odontologico": data['odontologico'],
        "premiacao": data['premiacao'],
        "updated_at": datetime.now() 
    }

    result = profiles_collection.update