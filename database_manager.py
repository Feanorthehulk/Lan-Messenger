# database_manager.py
# Gerencia o banco de dados SQLite e o logging automático de conversas.

import sqlite3
import os
from collections import defaultdict
from datetime import datetime
import json


# Salvar o banco na pasta do usuário
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "Lan Messenger")
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(USER_DATA_DIR, "messenger_history.db")

class DatabaseManager:
    """Gerencia a conexão com o banco de dados e o logging em ficheiro."""
    def __init__(self, config):
        """Inicializa e conecta ao banco de dados, e recebe as configurações da app."""
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.config = config
        self.create_tables()

    def create_tables(self):
        """Cria a tabela de mensagens se não existir."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_name TEXT NOT NULL,
                    receiver_name TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender_instance_id TEXT NOT NULL,
                    receiver_instance_id TEXT NOT NULL
                )
            """)
            self.conn.commit()
            print("Banco de dados e tabelas prontos.")
        except sqlite3.Error as e:
            print(f"Erro ao criar tabelas: {e}")

    def save_message(self, sender, receiver, message, sender_id, receiver_id):
        """Salva uma nova mensagem no banco de dados e no log em ficheiro (se ativo)."""
        if not all([sender, receiver, message, sender_id, receiver_id]):
            print(f"[DB-WARN] Tentativa de salvar mensagem inválida.")
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Salva na base de dados
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_name, receiver_name, message_text, sender_instance_id, receiver_instance_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (sender, receiver, message, sender_id, receiver_id, timestamp)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao salvar mensagem na base de dados: {e}")

        # 2. Salva no log em ficheiro, se a funcionalidade estiver ativa
        if self.config.get("admin_log_enabled"):
            self.log_message_to_file(timestamp, sender, message, sender_id, receiver_id)

    def log_message_to_file(self, timestamp, sender, message, sender_id, receiver_id):
        """Escreve uma única mensagem num ficheiro de log."""
        log_dir = self.config.get("admin_log_directory")
        if not log_dir or not os.path.isdir(log_dir):
            return

        try:
            # BUG FIX: Usar o ID completo para nomear os ficheiros
            conversation_key = tuple(sorted((sender_id, receiver_id)))
            log_filename = f"log_conversa_{conversation_key[0][:8]}_{conversation_key[1][:8]}.txt"
            log_filepath = os.path.join(log_dir, log_filename)

            log_entry = f"[{timestamp}] {sender}: {message}\n"

            with open(log_filepath, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except Exception as e:
            print(f"Erro ao escrever no ficheiro de log: {e}")


    def load_message_history(self, user1_id, user2_id):
        """Carrega o histórico de mensagens entre dois IDs de instância únicos."""
        history = []
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT sender_name, message_text, timestamp, sender_instance_id FROM messages
                WHERE (sender_instance_id = ? AND receiver_instance_id = ?) OR (sender_instance_id = ? AND receiver_instance_id = ?)
                ORDER BY timestamp ASC
                """,
                (user1_id, user2_id, user2_id, user1_id)
            )
            history = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao carregar histórico: {e}")
        return history

    def get_all_conversations(self):
        """Recupera todas as mensagens e agrupa-as por conversa para exportação."""
        conversations = defaultdict(list)
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT timestamp, sender_name, message_text, sender_instance_id, receiver_instance_id FROM messages ORDER BY timestamp ASC")
            all_messages = cursor.fetchall()

            for msg in all_messages:
                ts, sender, text, sender_id, receiver_id = msg
                conversation_key = tuple(sorted((sender_id, receiver_id)))
                conversations[conversation_key].append(f"[{ts}] {sender}: {text}")
            
            return conversations

        except sqlite3.Error as e:
            print(f"Erro ao recuperar todas as conversas: {e}")
            return {}

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
    
    def get_recent_chats(self, limit=5):
        """Retorna os chats mais recentes."""
        try:
            query = """
                SELECT sender_instance_id, sender_name, MAX(timestamp) as last_message
                FROM messages
                GROUP BY sender_instance_id
                ORDER BY last_message DESC
                LIMIT ?
            """
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, (limit,))
            chats = self.cursor.fetchall()
            return [{'id': chat[0], 'name': chat[1]} for chat in chats]
        except Exception as e:
            print(f"[Debug] Erro ao buscar chats recentes: {e}")
            return []
