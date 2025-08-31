import customtkinter as ctk
import socket
import json
import os
import subprocess
import sys
import threading
import time
import platform
import ui_manager
from network_manager import NetworkManager
from database_manager import DatabaseManager

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# Importações para Jump List (apenas no Windows)
if platform.system() == "Windows":
    try:
        import winreg
        import ctypes
        from ctypes import wintypes
        JUMPLIST_AVAILABLE = True
        print("[Debug] Módulos do Windows carregados com sucesso")
    except ImportError as e:
        print(f"[Debug] Módulos do Windows não disponíveis - Jump List desabilitada: {e}")
        JUMPLIST_AVAILABLE = False
else:
    JUMPLIST_AVAILABLE = False

if JUMPLIST_AVAILABLE:
    class JumpListManager:
        def __init__(self, app_id):
            self.app_id = app_id

        def create_jump_list(self, recent_chats):
            # Implemente aqui a lógica para criar a Jump List usando winreg, etc.
            print(f"[Debug] Criando Jump List para {self.app_id} com chats: {recent_chats}")
            # ...sua lógica...

class BroadcastMessageWindow(ctk.CTkToplevel):
    """Janela para exibir mensagens broadcast sobrepostas."""

    def __init__(self, parent, sender_name, message):
        super().__init__(parent)
        self.title("Mensagem Broadcast")
        self.geometry("400x200")
        self.center_on_screen()
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.grab_set()

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Ícone e título
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        icon_label = ctk.CTkLabel(header_frame, text="📢", font=ctk.CTkFont(size=24))
        icon_label.pack(side="left", padx=10, pady=10)
        title_label = ctk.CTkLabel(header_frame, text="Mensagem Broadcast", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=10, pady=10)
        # Remetente
        sender_frame = ctk.CTkFrame(self.main_frame)
        sender_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(sender_frame, text="De:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(sender_frame, text=sender_name).pack(side="left", padx=5, pady=5)
        # Mensagem
        message_frame = ctk.CTkFrame(self.main_frame)
        message_frame.pack(fill="both", expand=True, pady=(0, 10))
        message_text = ctk.CTkTextbox(message_frame, height=60)
        message_text.pack(fill="both", expand=True, padx=10, pady=10)
        message_text.insert("1.0", message)
        message_text.configure(state="disabled")
        # Botões
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x")
        close_btn = ctk.CTkButton(button_frame, text="Fechar", command=self.close_window)
        close_btn.pack(side="right", padx=10, pady=10)
        reply_btn = ctk.CTkButton(button_frame, text="Responder", command=self.reply_broadcast)
        reply_btn.pack(side="right", padx=5, pady=10)
        # Auto-fechar após 10 segundos
        self.auto_close_timer = self.after(10000, self.auto_close)
        # Focar na janela
        self.focus_force()
        # Fade in ao abrir
        try:
            from ui_manager import fade_in
            fade_in(self)
        except Exception:
            pass
        
    def center_window(self):
        """Centraliza a janela na tela."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def close_window(self):
        """Fecha a janela."""
        if hasattr(self, 'auto_close_timer'):
            self.after_cancel(self.auto_close_timer)
        self.grab_release()
    # ...existing code...

    def _create_registry_entries(self, recent_chats=None, tasks=None):
        """Cria entradas no registro do Windows para tarefas rápidas."""
        try:
            app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
            base_key = f"Software\\Classes\\Applications\\{app_name}.exe"
            
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key):
                    pass
            except Exception as e:
                print(f"[Debug] Erro ao criar chave base: {e}")
                return
            
            default_tasks = [
                {
                    "name": "Nova Mensagem", 
                    "command": f'"{sys.executable}" "{os.path.abspath(__file__)}" --new-message',
                    "icon": sys.executable + ",0"
                },
                {
                    "name": "Status Online", 
                    "command": f'"{sys.executable}" "{os.path.abspath(__file__)}" --status online',
                    "icon": sys.executable + ",0"
                },
                {
                    "name": "Histórico", 
                    "command": f'"{sys.executable}" "{os.path.abspath(__file__)}" --history',
                    "icon": sys.executable + ",0"
                }
            ]
            
            shell_key = f"{base_key}\\shell"
            
            for task in default_tasks:
                try:
                    task_key_name = task["name"].replace(" ", "").lower()
                    task_key_path = f"{shell_key}\\{task_key_name}"
                    
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, task_key_path) as task_key:
                        winreg.SetValueEx(task_key, "", 0, winreg.REG_SZ, task["name"])
                        winreg.SetValueEx(task_key, "Icon", 0, winreg.REG_SZ, task["icon"])
                        
                        with winreg.CreateKey(task_key, "command") as cmd_key:
                            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, task["command"])
                            
                except Exception as e:
                    print(f"[Debug] Erro ao criar tarefa {task['name']}: {e}")
                    continue
            
            print("[Debug] Tarefas registradas no Windows Registry")
            
        except Exception as e:
            print(f"[Debug] Erro geral no registro: {e}")

class App(ctk.CTk):
    def update_theme_all_windows(self):
        """Atualiza o tema em todas as janelas abertas do app."""
        if hasattr(self, 'ui') and self.ui:
            # Atualiza widgets do UIManager
            self.ui.create_widgets()  # Força recriação dos widgets principais
            # Atualiza nome do usuário
            self.ui.update_profile_display(self.username)
            # Limpa lista de usuários antes de repopular
            if hasattr(self.ui, 'user_list_frame') and self.ui.user_list_frame:
                for widget in self.ui.user_list_frame.winfo_children():
                    widget.destroy()
            if hasattr(self.ui, 'user_widgets'):
                self.ui.user_widgets.clear()
            # Repopula lista de usuários online
            if hasattr(self.network_manager, 'online_users'):
                for user_id, user_info in self.network_manager.online_users.items():
                    self.ui.add_user_to_list(user_id, user_info)
            # Atualiza janelas de chat abertas
            if hasattr(self.ui, 'chat_windows'):
                for win in self.ui.chat_windows.values():
                    if win and win.winfo_exists():
                        win.update_theme() if hasattr(win, 'update_theme') else None
            # Atualiza janela de broadcast
            if hasattr(self.ui, 'broadcast_chat_window_instance') and self.ui.broadcast_chat_window_instance:
                if self.ui.broadcast_chat_window_instance.winfo_exists():
                    self.ui.broadcast_chat_window_instance.update_theme() if hasattr(self.ui.broadcast_chat_window_instance, 'update_theme') else None
            # Atualiza janela de transferências
            if hasattr(self.ui, 'transfers_window_instance') and self.ui.transfers_window_instance:
                if self.ui.transfers_window_instance.winfo_exists():
                    self.ui.transfers_window_instance.update_theme() if hasattr(self.ui.transfers_window_instance, 'update_theme') else None
    def __init__(self, config, tcp_port):
        super().__init__()
        self.config = config
        self.username = config.get("username", "User")
        self.status = "online"
        self._destroyed = False  # Flag para controlar se a janela foi destruída

        # Aplicar tema conforme configuração do usuário
        try:
            appearance_mode = self.config.get("appearance_mode", "Light")
            print(f"[Debug] Aplicando tema na classe App: {appearance_mode}")
            ctk.set_appearance_mode(appearance_mode)
            
            # Verificar se o tema foi aplicado
            current_mode = ctk.get_appearance_mode()
            print(f"[Debug] Tema atual após aplicação: {current_mode}")
            
        except Exception as e:
            print(f"[Debug] Erro ao configurar tema na classe App: {e}")
            try:
                ctk.set_appearance_mode("Light")
            except:
                pass

        # Pasta padrão de recebidos no diretório do usuário
        self.downloads_folder = self.config.get(
            "downloads_folder",
            os.path.join(os.path.expanduser("~"), "Lan Messenger", "Ficheiros Recebidos"),
        )
        self.ensure_downloads_folder_exists()

        self.db_manager = DatabaseManager(self.config)
        self.pending_file_offers = {}
        self.pending_collab_invites = {}  # Armazena convites de colaboração pendentes
        
        # Inicializar Jump List
        if JUMPLIST_AVAILABLE:
            self.jump_list = JumpListManager("LanMessenger.App")
            self.init_jump_list()
        else:
            self.jump_list = None
        
        self.network_manager = NetworkManager(
            username=self.username,
            tcp_port=tcp_port,
            on_user_online=self.on_user_online,
            on_user_offline=self.on_user_offline,
            on_message_received=self.on_message_received,
            on_user_status_change=self.on_user_status_change,
            on_file_offer=self.on_file_offer_received,
            on_collab_request=self.on_collab_request_received,
            on_collab_response=self.on_collab_response_received,
            on_collab_start=self.on_collab_start_received,
            on_broadcast_message_received=self.on_broadcast_message_received
        )
        
        self.ui = ui_manager.UIManager(self, self.config)
        
        if self.winfo_exists():
            self.ui.update_profile_display(self.username)

        self.network_manager.start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def ensure_downloads_folder_exists(self):
        try:
            if self.downloads_folder and not os.path.exists(self.downloads_folder):
                os.makedirs(self.downloads_folder, exist_ok=True)
        except Exception as e:
            print(f"[Debug] Erro ao criar pasta de recebidos: {e}")

    def safe_after(self, delay, func):
        """Executa after() apenas se a janela não foi destruída."""
        if not self._destroyed:
            try:
                return self.after(delay, func)
            except Exception as e:
                print(f"[Debug] Erro em safe_after: {e}")
                return None
        return None

    def init_jump_list(self):
        """Inicializa a Jump List."""
        if not self.jump_list:
            return
        try:
            recent_chats = []
            try:
                recent_chats = self.db_manager.get_recent_chats(5)
            except:
                pass
                
            self.jump_list.create_jump_list(recent_chats)
            print("[Debug] Jump List inicializada com sucesso")
        except Exception as e:
            print(f"[Debug] Erro ao inicializar Jump List: {e}")

    def update_jump_list(self):
        """Atualiza a Jump List com chats recentes."""
        if not self.jump_list:
            return
        try:
            recent_chats = []
            try:
                recent_chats = self.db_manager.get_recent_chats(5)
            except:
                pass
                
            self.jump_list.create_jump_list(recent_chats)
        except Exception as e:
            print(f"[Debug] Erro ao atualizar Jump List: {e}")

    def save_config(self):
        """Salva as configurações no arquivo config.json"""
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"[Debug] Configurações salvas com sucesso")
        except Exception as e:
            print(f"[Debug] Erro ao salvar configurações: {e}")

    def on_broadcast_message_received(self, sender_id, message):
        """Callback quando uma mensagem broadcast é recebida - exibe janela sobreposta."""
        if self._destroyed:
            return
            
        sender_info = self.network_manager.online_users.get(sender_id, {})
        sender_name = sender_info.get('username', 'Desconhecido')
        
        print(f"[Debug] Mensagem broadcast de {sender_name}: {message}")
        
        # Criar e exibir janela sobreposta
        try:
            broadcast_window = BroadcastMessageWindow(self, sender_name, message)
            
            # Fazer som de notificação (opcional)
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except:
                pass  # Se não conseguir tocar som, continua normalmente
                
        except Exception as e:
            print(f"[Debug] Erro ao exibir janela broadcast: {e}")
            # Fallback - exibir em console se janela falhar
            print(f"BROADCAST de {sender_name}: {message}")

    def on_file_offer_received(self, sender_id, file_info, transfer_id):
        if self._destroyed:
            return
            
        sender_info = self.network_manager.online_users.get(sender_id)
        if not sender_info: return
        self.pending_file_offers[transfer_id] = file_info
        chat_window = self.ui.get_chat_window(sender_id)
        if chat_window:
            chat_window.add_file_banner(file_info, sender_info.get('username'), is_own_message=False, transfer_id=transfer_id)
        else:
            self.ui.open_chat_window(sender_id, sender_info)
            self.safe_after(150, lambda: self.on_file_offer_received(sender_id, file_info, transfer_id))

    def respond_to_file_offer(self, transfer_id, response):
        save_path = None
        file_info = self.pending_file_offers.get(transfer_id)
        if response == "accept" and file_info:
            original_filename = file_info.get('filename', 'ficheiro_recebido')
            if getattr(self, "_batch_accepting", False):
                # Aceitação em lote: salvar direto na pasta padrão
                base_name, ext = os.path.splitext(original_filename)
                candidate = os.path.join(self.downloads_folder, original_filename)
                counter = 1
                while os.path.exists(candidate):
                    candidate = os.path.join(self.downloads_folder, f"{base_name} ({counter}){ext}")
                    counter += 1
                save_path = candidate
            else:
                from tkinter import filedialog
                save_path = filedialog.asksaveasfilename(initialdir=self.downloads_folder, initialfile=original_filename)
                if not save_path:
                    response = "reject"
        print(f"Resposta à transferência {transfer_id}: {response}, Salvar em: {save_path}")
        self.pending_file_offers.pop(transfer_id, None)

    def accept_all_pending_file_offers(self):
        """Aceita todas as ofertas pendentes salvando na pasta padrão do usuário."""
        if not self.pending_file_offers:
            return
        self.ensure_downloads_folder_exists()
        self._batch_accepting = True
        try:
            # Criar lista para evitar alterar dict enquanto itera
            for transfer_id in list(self.pending_file_offers.keys()):
                self.respond_to_file_offer(transfer_id, "accept")
        finally:
            self._batch_accepting = False

    def on_collab_request_received(self, sender_id, session_id, file_info):
        """Novo: Exibe um banner na janela de chat em vez de um diálogo pop-up."""
        if self._destroyed:
            return
            
        sender_info = self.network_manager.online_users.get(sender_id)
        if not sender_info: 
            return
            
        # Guardar informações do convite
        self.pending_collab_invites[session_id] = {
            'sender_id': sender_id,
            'file_info': file_info,
            'timestamp': time.time()
        }
        
        # Exibir banner na janela de chat
        chat_window = self.ui.get_chat_window(sender_id)
        if chat_window:
            # Adicionar banner de colaboração ao chat
            filename = file_info.get('filename', 'um ficheiro') if file_info else 'um documento'
            invite_info = {
                'session_id': session_id,
                'filename': filename
            }
            
            # Adiciona o banner de colaboração
            chat_window.add_collab_banner(
                invite_info, 
                sender_info.get('username'), 
                is_own_message=False, 
                session_id=session_id
            )
            print(f"[Info] Banner de convite de colaboração adicionado ao chat para {filename}")
        else:
            # Se a janela não estiver aberta, abra-a e adicione o banner depois
            self.ui.open_chat_window(sender_id, sender_info)
            self.safe_after(150, lambda: self.on_collab_request_received(sender_id, session_id, file_info))

    def respond_to_collab_invite(self, session_id, response):
        """Responde a um convite de colaboração a partir do banner."""
        print(f"[Debug] respond_to_collab_invite chamado: session_id={session_id}, response={response}")
        
        invite_info = self.pending_collab_invites.get(session_id)
        if not invite_info:
            print(f"[Erro] Convite de colaboração não encontrado: {session_id}")
            return
            
        sender_id = invite_info['sender_id']
        
        # Atualizar o banner local
        chat_window = self.ui.get_chat_window(sender_id)
        if chat_window:
            if response == 'accept':
                chat_window.update_collab_banner_status(session_id, "Aceito! Aguardando...")
            else:
                chat_window.update_collab_banner_status(session_id, "Rejeitado")
        
        # Enviar resposta
        print(f"[Info] Respondendo ao convite de colaboração: {response} para sender_id: {sender_id}")
        self.network_manager.send_collab_response(sender_id, session_id, response)
        
        # Se rejeitado, remover da lista de pendentes
        if response != 'accept':
            self.pending_collab_invites.pop(session_id, None)

    def on_collab_response_received(self, sender_id, session_id, response):
        if self._destroyed:
            return
            
        print(f"[Debug] *** RESPOSTA RECEBIDA *** sender_id={sender_id}, session_id={session_id}, response={response}")
        
        pending_session = self.network_manager.pending_collab_sessions.get(session_id)
        print(f"[Debug] Sessão pendente encontrada: {pending_session}")
        
        if not pending_session:
            print(f"[Debug] ERRO: Nenhuma sessão pendente encontrada para {session_id}")
            print(f"[Debug] Sessões pendentes disponíveis: {list(self.network_manager.pending_collab_sessions.keys())}")
            return
            
        if pending_session.get('status') != 'pending':
            print(f"[Debug] AVISO: Status da sessão não é 'pending': {pending_session.get('status')}")
            return
            
        sender_info = self.network_manager.online_users.get(sender_id, {})
        sender_name = sender_info.get('username', 'Desconhecido')
        
        print(f"[Debug] *** PROCESSANDO RESPOSTA '{response}' DE {sender_name} ***")
        
        # Obter a janela de chat para atualizar o banner
        chat_window = self.ui.get_chat_window(sender_id)
        
        if response == 'accept':
            pending_session['status'] = 'accepted'
            print(f"[Debug] Sessão marcada como aceita, iniciando host_start_session...")
            
            # Atualizar o banner existente no chat
            if chat_window:
                chat_window.update_collab_banner_status(session_id, "Aceito! Abrindo colaboração...")
            
            self.host_start_session(session_id, sender_id)
        else: # response == 'reject'
            print(f"[Debug] Colaboração rejeitada por {sender_name}")
            
            # Atualizar o banner existente no chat
            if chat_window:
                chat_window.update_collab_banner_status(session_id, "Rejeitado")
            
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Pedido Recusado", message=f"{sender_name} recusou o seu pedido de colaboração.", icon="cancel")
            self.network_manager.pending_collab_sessions.pop(session_id, None)

    def on_collab_start_received(self, sender_id, session_id, port):
        """Agora só abre a janela de colaboração se o convite foi aceito."""
        if self._destroyed:
            return
            
        invite_info = self.pending_collab_invites.get(session_id)
        if not invite_info:
            print(f"[Erro] Recebido start para um convite não encontrado: {session_id}")
            return
            
        host_info = self.network_manager.online_users.get(sender_id)
        if not host_info: 
            return
        
        try:
            from collaboration_window import CollaborationWindow
            
            def attempt_connection():
                print(f"[Info] Tentando conectar ao servidor de colaboração na porta {port}")
                
                try:
                    collab_window = CollaborationWindow(
                        self, 
                        host_info, 
                        None, 
                        is_host=False, 
                        session_id=session_id, 
                        conn_details={'host': host_info['address'], 'port': port}
                    )
                    
                    # Aguardar um pouco antes de fazer grab_set para evitar conflitos
                    def set_focus():
                        if not collab_window._destroyed:
                            collab_window.grab_set()
                            collab_window.focus_set()
                    
                    collab_window.after(100, set_focus)
                    print(f"[Info] Janela de colaboração criada com sucesso")
                    
                    # Limpar o convite da lista de pendentes
                    self.pending_collab_invites.pop(session_id, None)
                    
                except Exception as e:
                    print(f"[Erro] Erro ao criar janela de colaboração: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Aguardar 1 segundo antes de tentar conectar (reduzido para melhor responsividade)
            print(f"[Debug] Aguardando 1s antes de conectar ao servidor na porta {port}")
            self.after(1000, attempt_connection)
            
        except Exception as e:
            print(f"[Erro] Erro ao processar início de colaboração: {e}")

    def host_start_session(self, session_id, guest_id):
        if self._destroyed:
            return
            
        print(f"[Debug] *** HOST_START_SESSION CHAMADO *** session_id={session_id}, guest_id={guest_id}")
        
        try:
            # Criar socket do servidor
            session_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            session_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            session_socket.bind(('', 0))
            session_port = session_socket.getsockname()[1]
            
            # Começar a escutar imediatamente
            session_socket.listen(1)
            print(f"[Info] *** SERVIDOR CRIADO E ESCUTANDO NA PORTA {session_port} ***")
            
            pending_session = self.network_manager.pending_collab_sessions[session_id]
            pending_session['socket'] = session_socket
            
            from collaboration_window import CollaborationWindow
            filepath = pending_session['filepath']
            guest_info = self.network_manager.online_users.get(guest_id, {})
            
            print(f"[Debug] Criando janela de colaboração do host para arquivo: {filepath}")
            
            # Criar janela de colaboração do host
            collab_window = CollaborationWindow(self, guest_info, filepath, is_host=True, session_id=session_id)
            
            # Aguardar um momento para a interface estar pronta
            def start_server_and_notify():
                try:
                    print(f"[Debug] Iniciando thread do servidor...")
                    # Iniciar thread do servidor
                    thread = threading.Thread(target=self.collaboration_server_thread, args=(session_id, collab_window), daemon=True)
                    thread.start()
                    
                    # Aguardar mais um pouco antes de notificar o cliente
                    def send_start_notification():
                        print(f"[Debug] *** ENVIANDO NOTIFICAÇÃO DE INÍCIO PARA CLIENTE ***")
                        self.network_manager.send_collab_start(guest_id, session_id, session_port)
                        print(f"[Info] Notificação de início enviada ao cliente na porta {session_port}")
                    
                    # Aguardar 2 segundos para garantir que o servidor está realmente pronto
                    self.after(2000, send_start_notification)
                    
                    # Configurar foco da janela após um delay
                    def set_focus():
                        if not collab_window._destroyed:
                            collab_window.grab_set()
                            collab_window.focus_set()
                    
                    collab_window.after(200, set_focus)
                    
                except Exception as e:
                    print(f"[Erro] Erro ao configurar servidor de colaboração: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Aguardar 200ms para a janela estar pronta, depois iniciar servidor
            self.after(200, start_server_and_notify)
            
        except Exception as e:
            print(f"[Erro] Erro ao iniciar sessão de colaboração: {e}")
            import traceback
            traceback.print_exc()

    def collaboration_server_thread(self, session_id, collab_window):
        server_socket = None
        conn = None
        try:
            pending_session = self.network_manager.pending_collab_sessions.get(session_id)
            if not pending_session: 
                print(f"[Erro] Sessão {session_id} não encontrada")
                return
                
            server_socket = pending_session['socket']
            filepath = pending_session['filepath']
            
            # CORREÇÃO: Verificação mais robusta do filepath
            if not filepath or not os.path.exists(filepath):
                print(f"[Erro] Arquivo não encontrado ou caminho inválido: {filepath}")
                return
                
            # Verificar se o socket está realmente escutando
            try:
                port = server_socket.getsockname()[1]
                print(f"[Info] Servidor confirmado na porta {port}, aguardando conexão para sessão {session_id}...")
            except Exception as e:
                print(f"[Erro] Socket do servidor inválido: {e}")
                return
            
            # Configurar timeout para accept
            server_socket.settimeout(30)  # 30 segundos timeout
            
            try:
                conn, addr = server_socket.accept()
                conn.settimeout(60)
                print(f"[Info] Conexão estabelecida com {addr}")
            except socket.timeout:
                print(f"[Erro] Timeout ao aguardar conexão para sessão {session_id}")
                return
            
            # Configurar conexão com verificação segura
            if not self._destroyed:
                try:
                    # CORREÇÃO: Usar método correto que existe na CollaborationWindow
                    print(f"[Debug] Configurando conexão na janela de colaboração...")
                    self.safe_after(0, lambda: collab_window.start_as_host(conn))
                    print(f"[Debug] Conexão configurada com sucesso")
                except Exception as e:
                    print(f"[Erro] Erro ao configurar conexão: {e}")
            
            # REMOVIDO: Envio automático de arquivo - agora é manual via botão
            print(f"[Info] Servidor pronto. Arquivo será enviado quando o usuário clicar no botão.")

            # Loop de mensagens simplificado
            print(f"[Info] Iniciando loop de mensagens para sessão {session_id}")
            while True:
                try:
                    conn.settimeout(120)  # 2 minutos para mensagens de chat
                    data = conn.recv(4096)
                    if not data:
                        print(f"[Info] Conexão fechada pelo cliente")
                        break
                    
                    messages = data.split(b"\n")
                    for message in messages:
                        if not message:
                            continue
                        
                        try:
                            msg = json.loads(message.decode())
                            if not self._destroyed:
                                self.safe_after(0, lambda m=msg: collab_window.handle_message(m))
                        except json.JSONDecodeError as e:
                            print(f"[Erro] Erro ao decodificar JSON: {e}")
                            continue
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[Erro] Erro na comunicação: {e}")
                    break

        except Exception as e:
            print(f"[Erro] Erro na sessão: {e}")
            
        finally:
            print("[Info] Fechando conexão do servidor")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass

    def cycle_status(self):
        if self.status == "online": self.status = "away"
        elif self.status == "away": self.status = "dnd"
        else: self.status = "online"
        self.ui.update_status_display(self.status)
        self.network_manager.update_status(self.status)

    def on_user_status_change(self, user_id, new_status):
        if self.ui and not self._destroyed: 
            self.ui.update_user_status_in_list(user_id, new_status)

    def transfers_window_closed(self):
        if not self._destroyed:
            self.ui.transfers_window_instance = None

    def on_user_online(self, user_id, user_info):
        if self.ui and not self._destroyed: 
            self.ui.add_user_to_list(user_id, user_info)

    def on_user_offline(self, user_id):
        if self.ui and not self._destroyed: 
            self.ui.remove_user_from_list(user_id)

    def on_message_received(self, sender_id, message):
        if not self.ui or self._destroyed: 
            return
            
        chat_window = self.ui.get_chat_window(sender_id)
        sender_info = self.network_manager.online_users.get(sender_id, {})
        sender_name = sender_info.get('username', 'Desconhecido')
        if chat_window:
            chat_window.add_message_to_chat(message, sender_name, is_own_message=False)
            # Atualizar Jump List quando receber mensagem
            self.update_jump_list()
            
            # Salvar mensagem recebida no banco de dados
            self.db_manager.save_message(
                sender=sender_name,
                receiver=self.username,
                message=message,
                sender_id=sender_id,
                receiver_id=self.network_manager.user_id
            )
        else:
            if sender_info:
                self.ui.open_chat_window(sender_id, sender_info)
                self.safe_after(100, lambda: self.on_message_received(sender_id, message))

    def export_full_history(self):
        if not self._destroyed:
            self.ui.show_error("Informação", "A função de exportação de histórico será implementada aqui.")

    def on_closing(self):
        self._destroyed = True  # Marcar como destruída
        self.network_manager.stop()
        self.destroy()

if __name__ == "__main__":
    try:
        print("[Debug] Iniciando aplicação...")
        # Configuração inicial da aplicação
        config = {
            "username": "User",
            "appearance_mode": "Light",
            "downloads_folder": os.path.join(os.path.expanduser("~"), "Lan Messenger", "Ficheiros Recebidos")
        }
        
        # Encontrar uma porta TCP livre
        tcp_port = find_free_port()
        
        # Criar e iniciar a aplicação
        app = App(config, tcp_port)
        app.mainloop()
        
        print("[Debug] Fim do main (isso não deveria aparecer se mainloop está rodando)")
    except Exception as e:
        import traceback
        print("[ERRO] Exceção não tratada:")
        traceback.print_exc()
        input("Pressione Enter para sair...")
