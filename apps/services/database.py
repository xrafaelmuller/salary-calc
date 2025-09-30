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

def add_public_investment(data):
    """Adiciona um novo investimento público ao banco de dados."""
    if investments_collection is None:
        print("ERRO: Coleção de investimentos não está disponível.")
        return False
        
    try:
        valor = float(data['valor'])
        investment_data = {
            'onde': data['onde'],
            'aplicacao': data['aplicacao'],
            'valor': valor,
            'resgate': datetime.strptime(data['resgate'], '%Y-%m-%d')
        }
        
        result = investments_collection.insert_one(investment_data)
        
        return result.inserted_id is not None

    except (ValueError, TypeError, KeyError, PyMongoError) as e:
        print(f"Erro ao processar ou inserir dados do investimento: {e}")
        return False

def get_all_investments():
    """Retorna uma lista de todos os investimentos, ordenados pela data de resgate."""
    if investments_collection is None:
        raise ConnectionError("Coleção de investimentos não está disponível.")
        
    investments = list(investments_collection.find({}).sort("resgate", 1))
    return investments

def delete_public_investment(investment_id_str):
    """Deleta um investimento específico pelo seu ID."""
    if investments_collection is None:
        raise ConnectionError("Coleção de investimentos não está disponível.")
        
    try:
        investment_id_obj = ObjectId(investment_id_str)
        result = investments_collection.delete_one({"_id": investment_id_obj})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Erro ao deletar investimento: {e}")
        return False

def update_public_investment(investment_id_str, data):
    """Atualiza um investimento existente pelo seu ID."""
    if investments_collection is None:
        print("ERRO: Coleção de investimentos não está disponível.")
        return False
    
    try:
        investment_id_obj = ObjectId(investment_id_str)
        
        valor_str = str(data.get('valor', '0')).replace('.', '').replace(',', '.')
        update_data = {
            'onde': data['onde'],
            'aplicacao': data['aplicacao'],
            'valor': float(valor_str),
            'resgate': datetime.strptime(data['resgate'], '%Y-%m-%d')
        }
        
        result = investments_collection.update_one(
            {"_id": investment_id_obj},
            {"$set": update_data}
        )
        return result.modified_count > 0

    except (ValueError, TypeError, KeyError, PyMongoError) as e:
        print(f"Erro ao processar ou atualizar dados do investimento: {e}")
        return False

def get_rendimento_atual():
    """Busca o valor do Rendimento Atual."""
    if app_data_collection is None:
        return 0.0
    try:
        doc = app_data_collection.find_one({"key": "rendimento_atual"})
        if doc:
            return doc.get("value", 0.0)
        return 0.0
    except Exception as e:
        print(f"Erro ao buscar rendimento atual: {e}")
        return 0.0

def update_rendimento_atual(new_value_str):
    """Salva ou atualiza o valor do Rendimento Atual."""
    if app_data_collection is None:
        return False
    try:
        valor_str = str(new_value_str).replace('.', '').replace(',', '.')
        valor_float = float(valor_str)
        
        app_data_collection.update_one(
            {"key": "rendimento_atual"},
            {"$set": {"value": valor_float}},
            upsert=True
        )
        return True
    except (ValueError, TypeError) as e:
        print(f"Erro ao converter ou salvar rendimento atual: {e}")
        return False