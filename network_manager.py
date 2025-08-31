import socket
import threading
import json
import time
import uuid
import os

class NetworkManager:
    def __init__(self, username, tcp_port, on_user_online, on_user_offline, on_message_received, on_user_status_change, on_file_offer, on_collab_request, on_collab_response, on_collab_start, on_broadcast_message_received):
        self.username = username
        self.tcp_port = tcp_port
        self.user_id = str(uuid.uuid4())
        self.status = "online"
        
        # Callbacks
        self.on_user_online = on_user_online
        self.on_user_offline = on_user_offline
        self.on_message_received = on_message_received
        self.on_user_status_change = on_user_status_change
        self.on_file_offer = on_file_offer
        self.on_collab_request = on_collab_request
        self.on_collab_response = on_collab_response
        self.on_collab_start = on_collab_start
        self.on_broadcast_message_received = on_broadcast_message_received

        # Sockets
        self.broadcast_port = 50000
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.settimeout(0.2)
        
        self.online_users = {}
        self.user_timeout = 10
        self.pending_transfers = {}
        self.pending_collab_sessions = {}

        self.running = False
        self.broadcast_thread = None
        self.listen_thread = None
        self.tcp_server_thread = None

    def create_presence_message(self):
        message = {
            "type": "presence",
            "id": self.user_id,
            "username": self.username,
            "tcp_port": self.tcp_port,
            "status": self.status
        }
        return json.dumps(message)

    def broadcast_presence(self):
        while self.running:
            message = self.create_presence_message()
            self.broadcast_socket.sendto(message.encode('utf-8'), ('<broadcast>', self.broadcast_port))
            
            current_time = time.time()
            offline_users = [uid for uid, info in self.online_users.items() if current_time - info['last_seen'] > self.user_timeout]
            
            for uid in offline_users:
                if uid in self.online_users:
                    del self.online_users[uid]
                    self.on_user_offline(uid)
            
            time.sleep(2)

    def listen_for_presence(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(('', self.broadcast_port))
        
        while self.running:
            try:
                data, addr = listen_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                msg_type = message.get('type')

                if msg_type == 'presence':
                    uid = message.get('id')
                    if uid and uid != self.user_id:
                        is_new_user = uid not in self.online_users
                        current_status = message.get('status', 'online')

                        if not is_new_user and self.online_users[uid]['status'] != current_status:
                            self.on_user_status_change(uid, current_status)

                        self.online_users[uid] = {
                            "id": uid,
                            "username": message.get('username'),
                            "address": addr[0],
                            "tcp_port": message.get('tcp_port'),
                            "status": current_status,
                            "last_seen": time.time()
                        }

                        if is_new_user:
                            self.on_user_online(uid, self.online_users[uid])
                elif msg_type == 'broadcast_message':
                    sender_id = message.get('sender_id')
                    if sender_id and sender_id != self.user_id:
                        self.on_broadcast_message_received(sender_id, message.get('message'))
            except Exception:
                pass
        listen_socket.close()

    def send_broadcast_message(self, message):
        message_data = {
            "type": "broadcast_message",
            "sender_id": self.user_id,
            "message": message
        }
        self.broadcast_socket.sendto(json.dumps(message_data).encode('utf-8'), ('<broadcast>', self.broadcast_port))

    def update_status(self, new_status):
        self.status = new_status
        message = self.create_presence_message()
        self.broadcast_socket.sendto(message.encode('utf-8'), ('<broadcast>', self.broadcast_port))

    def start_tcp_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.tcp_port))
        server_socket.listen(5)
        
        while self.running:
            try:
                client_socket, addr = server_socket.accept()
                threading.Thread(target=self.handle_tcp_client, args=(client_socket,), daemon=True).start()
            except Exception:
                break
        server_socket.close()

    def handle_tcp_client(self, client_socket):
        try:
            data = client_socket.recv(4096).decode('utf-8')
            message_data = json.loads(data)
            msg_type = message_data.get("type")

            if msg_type == "private_message":
                self.on_message_received(message_data['sender_id'], message_data['message'])
            elif msg_type == "file_offer":
                self.on_file_offer(message_data['sender_id'], message_data['file_info'], message_data['transfer_id'])
            elif msg_type == "collab_request":
                self.on_collab_request(message_data['sender_id'], message_data['session_id'], message_data['file_info'])
            elif msg_type == "collab_response":
                self.on_collab_response(message_data['sender_id'], message_data['session_id'], message_data['response'])
            elif msg_type == "collab_start":
                self.on_collab_start(message_data['sender_id'], message_data['session_id'], message_data['port'])
        except Exception as e:
            print(f"Erro ao receber dados TCP: {e}")
        finally:
            client_socket.close()

    def send_private_message(self, target_id, message):
        if target_id not in self.online_users: return
        target_info = self.online_users[target_id]
        target_ip, target_port = target_info['address'], target_info['tcp_port']
        message_data = {"type": "private_message", "sender_id": self.user_id, "message": message}
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(message_data).encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar mensagem para {target_ip}:{target_port} - {e}")

    def send_file_offer(self, target_id, filepath):
        if target_id not in self.online_users: return None
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            transfer_id = str(uuid.uuid4())
            file_info = {"filename": filename, "filesize": filesize}
            self.pending_transfers[transfer_id] = {"filepath": filepath, "target_id": target_id}
            offer_data = {
                "type": "file_offer",
                "sender_id": self.user_id,
                "transfer_id": transfer_id,
                "file_info": file_info
            }
            target_info = self.online_users[target_id]
            target_ip, target_port = target_info['address'], target_info['tcp_port']
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(offer_data).encode('utf-8'))
            return transfer_id
        except Exception as e:
            print(f"Erro ao enviar oferta de ficheiro: {e}")
            return None

    def send_file_offer_response(self, transfer_id, response, save_path):
        # Esta função será implementada no futuro
        print(f"A enviar resposta '{response}' para a transferência {transfer_id}")
        pass

    def send_collab_request(self, target_id, filepath):
        if target_id not in self.online_users:
            print(f"Erro: Utilizador {target_id} não está online.")
            return None
        try:
            session_id = str(uuid.uuid4())
            
            # Apenas cria file_info se um caminho de ficheiro for fornecido
            file_info = None
            if filepath and os.path.exists(filepath):
                file_info = {
                    "filename": os.path.basename(filepath),
                    "filesize": os.path.getsize(filepath)
                }

            request_data = {
                "type": "collab_request",
                "sender_id": self.user_id,
                "session_id": session_id,
                "file_info": file_info  # Pode ser None
            }

            self.pending_collab_sessions[session_id] = {
                "filepath": filepath,
                "target_id": target_id,
                "status": "pending"
            }

            target_info = self.online_users[target_id]
            target_ip, target_port = target_info['address'], target_info['tcp_port']

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(request_data).encode('utf-8'))

            print(f"Pedido de colaboração enviado para {target_info['username']}")
            return session_id
        except Exception as e:
            print(f"Erro ao enviar pedido de colaboração: {e}")
            return None

    def send_collab_response(self, target_id, session_id, response):
        if target_id not in self.online_users:
            print(f"Erro: Utilizador {target_id} não está online para responder.")
            return

        response_data = {
            "type": "collab_response",
            "sender_id": self.user_id,
            "session_id": session_id,
            "response": response
        }

        target_info = self.online_users[target_id]
        target_ip, target_port = target_info['address'], target_info['tcp_port']

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(response_data).encode('utf-8'))
            print(f"Resposta de colaboração ('{response}') enviada para {target_info['username']}")
        except Exception as e:
            print(f"Erro ao enviar resposta de colaboração: {e}")

    def send_collab_start(self, target_id, session_id, port):
        if target_id not in self.online_users:
            print(f"Erro: Utilizador {target_id} não está online para iniciar a sessão.")
            return

        start_data = {
            "type": "collab_start",
            "sender_id": self.user_id,
            "session_id": session_id,
            "port": port
        }

        target_info = self.online_users[target_id]
        target_ip, target_port = target_info['address'], target_info['tcp_port']

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(start_data).encode('utf-8'))
            print(f"Mensagem para iniciar a colaboração enviada para {target_info['username']} na porta {port}")
        except Exception as e:
            print(f"Erro ao enviar mensagem para iniciar a colaboração: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self.broadcast_thread = threading.Thread(target=self.broadcast_presence, daemon=True)
            self.listen_thread = threading.Thread(target=self.listen_for_presence, daemon=True)
            self.tcp_server_thread = threading.Thread(target=self.start_tcp_server, daemon=True)
            self.broadcast_thread.start()
            self.listen_thread.start()
            self.tcp_server_thread.start()
            print(f"NetworkManager iniciado. ID: {self.user_id}, a ouvir em TCP na porta: {self.tcp_port}")

    def stop(self):
        if self.running:
            print("A parar o NetworkManager...")
            message = self.create_presence_message()
            self.broadcast_socket.sendto(message.encode('utf-8'), ('<broadcast>', self.broadcast_port))
            self.running = False
            self.broadcast_socket.close()
            print("NetworkManager parado.")