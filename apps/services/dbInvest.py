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