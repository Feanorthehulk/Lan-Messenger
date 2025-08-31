from database_manager import DatabaseManager
import json

# Carregar configuração
with open('config.json', 'r') as f:
    config = json.load(f)

# Criar instância do DatabaseManager
db_manager = DatabaseManager(config)

# Testar salvamento de uma mensagem
print("🧪 Testando salvamento de mensagem...")

try:
    db_manager.save_message(
        sender="Teste_Usuario1", 
        receiver="Teste_Usuario2", 
        message="Esta é uma mensagem de teste para verificar o banco de dados", 
        sender_id="test_id_001", 
        receiver_id="test_id_002"
    )
    print("✅ Mensagem de teste salva com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao salvar mensagem de teste: {e}")

# Verificar se foi salva
import sqlite3
conn = sqlite3.connect('messenger_history.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM messages")
total = cursor.fetchone()[0]
print(f"📊 Total de mensagens após teste: {total}")

if total > 0:
    cursor.execute("SELECT sender_name, receiver_name, message_text, timestamp FROM messages ORDER BY timestamp DESC LIMIT 1")
    last_message = cursor.fetchone()
    print(f"📝 Última mensagem: [{last_message[3]}] {last_message[0]} → {last_message[1]}: {last_message[2]}")

conn.close()
print("\n✅ Teste concluído!")
