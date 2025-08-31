import sqlite3
import os

# Verificar se o arquivo do banco existe
db_file = "messenger_history.db"
if os.path.exists(db_file):
    print(f"✅ Arquivo do banco existe: {db_file}")
    print(f"📏 Tamanho do arquivo: {os.path.getsize(db_file)} bytes")
else:
    print(f"❌ Arquivo do banco NÃO existe: {db_file}")
    exit()

try:
    # Conectar ao banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📋 Tabelas encontradas: {tables}")
    
    # Verificar se a tabela messages existe
    if ('messages',) in tables:
        print("✅ Tabela 'messages' existe")
        
        # Contar total de mensagens
        cursor.execute("SELECT COUNT(*) FROM messages")
        total = cursor.fetchone()[0]
        print(f"📊 Total de mensagens: {total}")
        
        if total > 0:
            # Mostrar últimas 3 mensagens
            cursor.execute("SELECT sender_name, receiver_name, message_text, timestamp FROM messages ORDER BY timestamp DESC LIMIT 3")
            recent_messages = cursor.fetchall()
            print(f"\n📝 Últimas {len(recent_messages)} mensagens:")
            for i, msg in enumerate(recent_messages, 1):
                sender, receiver, text, timestamp = msg
                print(f"  {i}. [{timestamp}] {sender} → {receiver}: {text[:50]}{'...' if len(text) > 50 else ''}")
        else:
            print("⚠️  Tabela 'messages' está vazia - nenhuma mensagem foi salva ainda")
            
        # Verificar estrutura da tabela
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        print(f"\n🏗️  Estrutura da tabela 'messages':")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
            
    else:
        print("❌ Tabela 'messages' NÃO existe")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"❌ Erro ao acessar banco de dados: {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
