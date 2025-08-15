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
    client = None
    db = None
    users_collection = None
    profiles_collection = None


def init_db():
    """Inicializa o banco de dados MongoDB, garantindo conexão e índices."""
    # CORREÇÃO: Usando 'is None' para a verificação.
    if client is None:
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
    # CORREÇÃO: Usando 'is None' para a verificação.
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
    # CORREÇÃO: Usando 'is None' para a verificação.
    if users_collection is None:
        raise ConnectionError("Coleção de usuários não está disponível.")
    user_doc = users_collection.find_one({"username": username})
    if user_doc:
        user_doc['id'] = str(user_doc['_id']) 
        return user_doc
    return None

def save_profile_to_db(user_id_str, profile_name, data):
    """Salva ou atualiza um perfil para um usuário específico."""
    # CORREÇÃO: Usando 'is None' para a verificação.
    if profiles_collection is None:
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

    result = profiles_collection.update_one(
        {"user_id": user_id_obj, "name": profile_name},
        {"$set": profile_data_to_save},
        upsert=True 
    )
    return result.acknowledged 

def load_profile_from_db(user_id_str, profile_name):
    """Carrega os dados de um perfil específico de um usuário."""
    # CORREÇÃO: Usando 'is None' para a verificação.
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 
    profile_doc = profiles_collection.find_one({"user_id": user_id_obj, "name": profile_name})
    if profile_doc:
        profile_doc['id'] = str(profile_doc['_id']) 
        return profile_doc
    return None

def get_all_profile_names(user_id_str):
    """Retorna uma lista de nomes de perfis para um usuário específico."""
    # CORREÇÃO: Usando 'is None' para a verificação.
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 
    names = []
    for doc in profiles_collection.find({"user_id": user_id_obj}, {"name": 1}).sort("name", 1):
        names.append(doc['name'])
    return names

def get_last_profile_name(user_id_str):
    """Retorna o nome do perfil mais recentemente atualizado para um usuário."""
    # CORREÇÃO: Usando 'is None' para a verificação.
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 
    profile_doc_cursor = profiles_collection.find({"user_id": user_id_obj}).sort("updated_at", -1).limit(1)
    
    for doc in profile_doc_cursor: 
        return doc['name']
    return None

def delete_profile_from_db(user_id, profile_name):
    """Deleta um perfil específico do documento de um usuário."""
    db = get_db()
    users_collection = db.users

    # A operação $unset remove a chave do sub-documento 'profiles'
    result = users_collection.update_one(
        {'id': user_id},
        {'$unset': {f'profiles.{profile_name}': ""}}
    )

    # Retorna True se um documento foi modificado, False caso contrário
    return result.modified_count > 0