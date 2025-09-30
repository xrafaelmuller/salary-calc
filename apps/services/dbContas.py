# apps/services/dbContas.py

from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
from datetime import datetime
from .database import db

transactions_collection = db['transactions'] 

def add_transaction(data):
    """Adiciona um novo lançamento (entrada ou saída)."""
    try:
        transaction_data = {
            'descricao': data['descricao'],
            'categoria': data['categoria'],
            'valor': float(data['valor']),
            'tipo': data['tipo'],
            'data': datetime.strptime(data['data'], '%Y-%m-%d'),
            'created_at': datetime.now()
        }
        result = transactions_collection.insert_one(transaction_data)
        return result.inserted_id is not None
    except (PyMongoError, ValueError, KeyError) as e:
        print(f"Erro ao adicionar lançamento: {e}")
        return False

def get_all_transactions():
    """Retorna todos os lançamentos para cálculo dos totais."""
    return list(transactions_collection.find({}).sort("data", -1))

def update_transaction(transaction_id_str, data):
    """Atualiza um lançamento existente pelo seu ID."""
    try:
        # Converte o valor para float, tratando possíveis erros
        valor_float = float(str(data.get('valor', '0')).replace('.', '').replace(',', '.'))

        update_data = {
            'descricao': data['descricao'],
            'categoria': data['categoria'],
            'valor': valor_float,
            'tipo': data['tipo']
            # A data original do lançamento é mantida
        }
        result = transactions_collection.update_one(
            {"_id": ObjectId(transaction_id_str)},
            {"$set": update_data}
        )
        # Retorna True se algum documento foi modificado
        return result.modified_count > 0
    except (PyMongoError, ValueError, KeyError) as e:
        print(f"Erro ao atualizar lançamento: {e}")
        return False

def delete_transaction(transaction_id_str):
    """Deleta um lançamento."""
    try:
        result = transactions_collection.delete_one({"_id": ObjectId(transaction_id_str)})
        return result.deleted_count > 0
    except (PyMongoError, KeyError) as e:
        print(f"Erro ao deletar lançamento: {e}")
        return False