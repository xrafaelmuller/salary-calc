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



def save_profile_to_db(user_id_str, profile_name, data):
    """Salva ou atualiza um perfil para um usuário específico."""
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
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 
    names = []
    for doc in profiles_collection.find({"user_id": user_id_obj}, {"name": 1}).sort("name", 1):
        names.append(doc['name'])
    return names

def get_last_profile_name(user_id_str):
    """Retorna o nome do perfil mais recentemente atualizado para um usuário."""
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    user_id_obj = ObjectId(user_id_str) 
    profile_doc_cursor = profiles_collection.find({"user_id": user_id_obj}).sort("updated_at", -1).limit(1)
    
    for doc in profile_doc_cursor: 
        return doc['name']
    return None

def delete_profile_from_db(user_id_str, profile_name):
    """Deleta um perfil específico da coleção de perfis."""
    if profiles_collection is None:
        raise ConnectionError("Coleção de perfis não está disponível.")
    
    user_id_obj = ObjectId(user_id_str)
    
    result = profiles_collection.delete_one(
        {"user_id": user_id_obj, "name": profile_name}
    )
    
    return result.deleted_count > 0