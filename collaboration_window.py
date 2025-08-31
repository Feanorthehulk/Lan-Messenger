import customtkinter as ctk
from PIL import Image
import fitz  # PyMuPDF
import json
import os
import socket
import threading
import struct
import tempfile
import time
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
import platform

try:
    if platform.system() == "Windows":
        import win32gui
        import win32con
        import ctypes
except ImportError:
    print("A biblioteca pywin32 não está instalada. O recurso de piscar a janela será desativado.")

# --- Classe Auxiliar para o Protocolo de Rede ---
class Protocol:
    @staticmethod
    def send_message(sock, payload):
        try:
            json_data = json.dumps(payload).encode('utf-8')
            msg_len_header = struct.pack('>I', len(json_data))
            sock.sendall(msg_len_header + json_data)
        except (ConnectionError, OSError) as e:
            print(f"[Protocolo] Erro ao enviar mensagem: {e}")
            raise ConnectionError("Falha ao enviar mensagem.")

    @staticmethod
    def receive_message(sock):
        try:
            header_data = Protocol._recv_all(sock, 4)
            if not header_data: return None
            msg_len = struct.unpack('>I', header_data)[0]
            json_data = Protocol._recv_all(sock, msg_len)
            if not json_data: return None
            return json.loads(json_data.decode('utf-8'))
        except (ConnectionError, OSError, struct.error, json.JSONDecodeError) as e:
            print(f"[Protocolo] Erro ao receber mensagem: {e}")
            raise ConnectionError("Falha ao receber mensagem.")

    @staticmethod
    def _recv_all(sock, n):
        data = bytearray()
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet: 
                    print(f"[Debug] Conexão fechada durante _recv_all (recebido {len(data)}/{n} bytes)")
                    return None
                data.extend(packet)
            except socket.timeout:
                print(f"[Debug] Timeout durante _recv_all (recebido {len(data)}/{n} bytes)")
                raise ConnectionError("Timeout durante recepção de dados")
            except (BlockingIOError):
                continue
            except Exception as e:
                print(f"[Debug] Erro durante _recv_all: {e}")
                raise ConnectionError(f"Erro durante recepção: {e}")
        return data

# --- Janela Principal de Colaboração ---
class CollaborationWindow(ctk.CTkToplevel):
    def __init__(self, master_app, target_info, filepath=None, is_host=True, session_id=None, conn_details=None):
        super().__init__(master_app)

        # Variável para rastrear se a janela foi destruída
        self._destroyed = False

        self.app = master_app
        self.target_info = target_info
        self.filepath = filepath
        self.is_host = is_host
        self.session_id = session_id
        self.conn_details = conn_details
        self.connection = None
        self.pdf_document = None
        self.temp_pdf_path = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.has_control = is_host
        self.running = True
        self.last_synced_scroll_pos = None
        self.file_transfer_in_progress = False  # Flag para pausar o loop receptor

        self.current_tool = "cursor"
        self.start_pos = None
        self.current_color = {"stroke": (1, 1, 0)} # Amarelo
        self.color_buttons = []

        try:
            self.title(f"Colaboração com {target_info.get('username', 'Desconhecido')}")
            
            # Obter dimensões da tela para posicionamento adequado
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Definir tamanho da janela considerando o tamanho da tela
            window_width = min(1200, int(screen_width * 0.8))
            window_height = min(800, int(screen_height * 0.8))
            
            # Centralizar a janela
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            self.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.minsize(800, 600)
            
            print(f"[Debug] Janela de colaboração: {window_width}x{window_height} na posição {x},{y}")
            
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.bind("<FocusIn>", lambda e: self.stop_flashing())

            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)

            # Aguardar um pouco antes de configurar a UI para evitar condições de corrida
            self.after(50, self.setup_ui_delayed)
            
        except Exception as e:
            print(f"[Erro] Erro durante inicialização da janela de colaboração: {e}")
            self._destroyed = True

    def setup_ui_delayed(self):
        """Configuração da UI com delay para evitar condições de corrida"""
        if self._destroyed:
            return
            
        try:
            print("[Debug] Iniciando configuração da UI...")
            self.setup_ui()

            if self.is_host:
                self.display_message("Sistema", "Aguardando conexão do parceiro...")
                # Se for host e já tiver um arquivo, apenas preparar para envio (não carregar ainda)
                if self.filepath:
                    self.display_message("Sistema", f"Arquivo selecionado: {os.path.basename(self.filepath)}")
                    self.display_message("Sistema", "Aguardando parceiro conectar para poder enviar o arquivo.")
                elif not self.filepath:
                    self.after(100, self.prompt_for_file)
            else:
                self.after(100, self.connect_to_host)
            
            self.after(250, self.periodic_scroll_sync)
            print("[Debug] UI configurada com sucesso")
            
        except Exception as e:
            print(f"[Erro] Erro durante configuração da UI: {e}")
            self._destroyed = True

    def prompt_for_file(self):
        self.display_message("Sistema", "Por favor, selecione um arquivo PDF para compartilhar.")
        self.attributes("-topmost", True)
        filepath = filedialog.askopenfilename(parent=self, title="Selecione um PDF para colaborar", filetypes=[("PDF files", "*.pdf")])
        self.attributes("-topmost", False)
        if filepath:
            self.filepath = filepath
            self.display_message("Sistema", f"Arquivo selecionado: {os.path.basename(self.filepath)}")
            
            # Sincronizar estado da interface
            self.sync_interface_state()
        else:
            # CORREÇÃO: Cliente não tem arquivo inicialmente - não fechar janela
            if self.is_host:
                self.display_message("Sistema", "Nenhum arquivo selecionado. Fechando colaboração.")
                self.after(2000, self.on_closing)
            else:
                self.display_message("Sistema", "Aguardando o host enviar o arquivo...")

    def setup_ui(self):
        pdf_main_frame = ctk.CTkFrame(self)
        pdf_main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        pdf_main_frame.grid_rowconfigure(1, weight=1)
        pdf_main_frame.grid_columnconfigure(0, weight=1)

        tools_frame = ctk.CTkFrame(pdf_main_frame)
        tools_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.cursor_btn = ctk.CTkButton(tools_frame, text="Cursor", width=80, command=lambda: self.select_tool("cursor"), text_color="black")
        self.cursor_btn.pack(side="left", padx=5, pady=5)
        self.highlight_btn = ctk.CTkButton(tools_frame, text="Marca-Texto", width=100, command=lambda: self.select_tool("highlight"), text_color="black")
        self.highlight_btn.pack(side="left", padx=5, pady=5)

        self.color_palette_frame = ctk.CTkFrame(tools_frame, fg_color="transparent")
        self.color_palette_frame.pack(side="left", padx=10)
        colors = {
            "yellow": {"hex": "#FFD700", "rgb": (1, 1, 0)},
            "green": {"hex": "#ADFF2F", "rgb": (0.68, 1, 0.18)},
            "blue": {"hex": "#87CEEB", "rgb": (0.53, 0.81, 0.92)},
            "pink": {"hex": "#FFB6C1", "rgb": (1, 0.71, 0.76)}
        }
        for color_data in colors.values():
            color_btn = ctk.CTkButton(self.color_palette_frame, text="", width=25, height=25, fg_color=color_data["hex"], command=lambda c=color_data["rgb"]: self.select_color(c), text_color="black")
            color_btn.pack(side="left", padx=2)
            self.color_buttons.append((color_data["rgb"], color_btn))

        self.save_btn = ctk.CTkButton(tools_frame, text="Salvar com Anotações", width=160, command=self.save_with_annotations, text_color="black")
        self.save_btn.pack(side="left", padx=20, pady=5)

        self.pdf_scroll_frame = ctk.CTkScrollableFrame(pdf_main_frame, label_text="Visualizador de PDF")
        self.pdf_scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.pdf_scroll_frame.bind_all("<Control-MouseWheel>", self.on_mouse_wheel_zoom)

        self.pdf_label = ctk.CTkLabel(self.pdf_scroll_frame, text="Aguardando arquivo...", corner_radius=5)
        self.pdf_label.pack(expand=True, padx=5, pady=5)
        self.pdf_label.bind("<ButtonPress-1>", self.on_pdf_press)
        self.pdf_label.bind("<B1-Motion>", self.on_pdf_motion)
        self.pdf_label.bind("<ButtonRelease-1>", self.on_pdf_release)

        controls_frame = ctk.CTkFrame(pdf_main_frame)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        controls_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        self.prev_btn = ctk.CTkButton(controls_frame, text="← Ant", width=50, command=self.prev_page)
        self.prev_btn.grid(row=0, column=0, padx=5, pady=5)
        self.page_label = ctk.CTkLabel(controls_frame, text="Página: -/-")
        self.page_label.grid(row=0, column=1, padx=5)
        self.next_btn = ctk.CTkButton(controls_frame, text="Próx →", width=50, command=self.next_page)
        self.next_btn.grid(row=0, column=2, padx=5)
        self.zoom_out_btn = ctk.CTkButton(controls_frame, text="-", width=30, command=self.zoom_out)
        self.zoom_out_btn.grid(row=0, column=3, padx=(10, 2))
        self.zoom_in_btn = ctk.CTkButton(controls_frame, text="+", width=30, command=self.zoom_in)
        self.zoom_in_btn.grid(row=0, column=4, padx=(2, 5))
        # Botão "Enviar PDF ao Parceiro" (apenas para host)
        if self.is_host:
            self.send_pdf_button = ctk.CTkButton(
                controls_frame,
                text="📤 Enviar PDF ao Parceiro",
                command=self.manual_send_pdf,
                state="disabled",  # Inicialmente desabilitado
                width=160
            )
            self.send_pdf_button.grid(row=0, column=5, padx=5, pady=5)
            
            # Barra de progresso para envio (inicialmente oculta)
            self.progress_frame = ctk.CTkFrame(controls_frame)
            self.progress_label = ctk.CTkLabel(self.progress_frame, text="Enviando: 0%", font=ctk.CTkFont(size=12))
            self.progress_label.pack(side="left", padx=(10, 5), pady=5)
            
            self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=120, height=20)
            self.progress_bar.pack(side="left", padx=5, pady=5)
            self.progress_bar.set(0)
            
            # Frame inicialmente não posicionado (oculto)
            self.progress_frame_visible = False
        else:
            # Para cliente: criar frame de progresso sem botão de envio
            self.progress_frame = ctk.CTkFrame(controls_frame)
            self.progress_label = ctk.CTkLabel(self.progress_frame, text="Recebendo: 0%", font=ctk.CTkFont(size=12))
            self.progress_label.pack(side="left", padx=(10, 5), pady=5)
            
            self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=120, height=20)
            self.progress_bar.pack(side="left", padx=5, pady=5)
            self.progress_bar.set(0)
            
            # Frame inicialmente não posicionado (oculto)
            self.progress_frame_visible = False
            
        self.control_btn = ctk.CTkButton(controls_frame, text="Passar Controle", command=self.pass_control)
        self.control_btn.grid(row=0, column=6, padx=10)

        chat_frame = ctk.CTkFrame(self)
        chat_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_text = ctk.CTkTextbox(chat_frame, state="disabled", wrap="word")
        self.chat_text.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.msg_entry = ctk.CTkEntry(chat_frame, placeholder_text="Digite sua mensagem...")
        self.msg_entry.grid(row=1, column=0, sticky="ew", padx=(5,0), pady=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())
        self.send_btn = ctk.CTkButton(chat_frame, text="Enviar", width=70, command=self.send_message)
        self.send_btn.grid(row=1, column=1, sticky="e", padx=5, pady=5)
        
        self.update_control_ui()
        self.select_tool(self.current_tool)
        self.select_color(self.current_color["stroke"])

    def on_mouse_wheel_zoom(self, event):
        if self.has_control:
            if event.delta > 0: self.zoom_in()
            else: self.zoom_out()
            return "break"

    def select_tool(self, tool):
        self.current_tool = tool
        self.pdf_label.configure(cursor="crosshair" if tool == "highlight" else "")
        self.cursor_btn.configure(fg_color=('#3a7ebf', '#1f538d') if tool == "cursor" else "transparent")
        self.highlight_btn.configure(fg_color=('#3a7ebf', '#1f538d') if tool == "highlight" else "transparent")
        if tool == "highlight": self.color_palette_frame.pack(side="left", padx=10)
        else: self.color_palette_frame.pack_forget()

    def select_color(self, color_rgb):
        self.current_color["stroke"] = color_rgb
        for rgb, button in self.color_buttons:
            button.configure(border_width=2 if rgb == color_rgb else 0, border_color="#3a7ebf")

    def on_pdf_press(self, event):
        if self.has_control and self.current_tool == "highlight": self.start_pos = (event.x, event.y)

    def on_pdf_motion(self, event):
        if self.has_control and self.current_tool == "highlight" and self.start_pos: pass

    def on_pdf_release(self, event):
        if self.has_control and self.current_tool == "highlight" and self.start_pos:
            self.add_highlight(self.start_pos, (event.x, event.y))
            self.start_pos = None

    def add_highlight(self, start_pos, end_pos, color=None, sync=True):
        if not self.pdf_document: return
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        inv_mat = ~mat
        x0, y0, x1, y1 = min(start_pos[0], end_pos[0]), min(start_pos[1], end_pos[1]), max(start_pos[0], end_pos[0]), max(start_pos[1], end_pos[1])
        highlight_rect = fitz.Rect(fitz.Point(x0, y0) * inv_mat, fitz.Point(x1, y1) * inv_mat)
        try:
            page = self.pdf_document[self.current_page]
            annot = page.add_highlight_annot(highlight_rect)
            if annot:
                annot_color = color if color is not None else self.current_color
                annot.set_colors(annot_color)
                annot.update()
                if sync: self.send_annotation_action("add_highlight", {"rect": list(annot.rect), "page": self.current_page, "color": annot_color})
                self.render_current_page()
        except Exception as e: print(f"Erro ao adicionar marcação: {e}")

    def save_with_annotations(self):
        if not self.pdf_document or not self.has_control: return
        try:
            self.attributes("-topmost", True)
            save_path = filedialog.asksaveasfilename(parent=self, title="Salvar PDF com anotações",defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            self.attributes("-topmost", False)
            if save_path:
                self.pdf_document.save(save_path, garbage=4, deflate=True, clean=True)
                self.display_message("Sistema", f"PDF salvo com sucesso em {os.path.basename(save_path)}")
                CTkMessagebox(title="Sucesso", message="O PDF com as anotações foi salvo.")
        except Exception as e:
            CTkMessagebox(title="Erro ao Salvar", message=f"Erro ao salvar o PDF: {e}", icon="cancel")

    def start_as_host(self, conn):
        self.connection = conn
        self.display_message("Sistema", f"Parceiro conectado de {self.connection.getpeername()}!")
        
        # Sincronizar estado da interface
        self.sync_interface_state()
        
        # Se já tiver arquivo, informar sobre possibilidade de envio
        if self.filepath:
            self.display_message("Sistema", "Agora você pode enviar o arquivo clicando no botão 'Enviar PDF ao Parceiro'.")
        else:
            self.display_message("Sistema", "Selecione um arquivo para compartilhar.")
            self.after(100, self.prompt_for_file)

    def set_connection(self, conn):
        """Método para configurar a conexão do servidor - usado pelo main.py"""
        print(f"[Debug] Configurando conexão do servidor...")
        self.start_as_host(conn)

    def initiate_file_transfer(self):
        """Prepara a interface para transferência de arquivo - não envia automaticamente"""
        if self.is_host:
            if self.filepath and os.path.exists(self.filepath):
                self.display_message("Sistema", f"Arquivo selecionado: {os.path.basename(self.filepath)}")
                if self.connection:
                    self.display_message("Sistema", "Clique em 'Enviar PDF ao Parceiro' para compartilhar o arquivo.")
                    self.enable_send_button()
                else:
                    self.display_message("Sistema", "Aguardando parceiro conectar...")
            else:
                self.display_message("Sistema", "Nenhum arquivo selecionado. Selecione um arquivo primeiro.")
        else:
            # Para o cliente: aguardar recebimento
            self.display_message("Sistema", "Aguardando o host enviar o arquivo...")

    def enable_send_button(self):
        """Habilita o botão de envio de PDF para o host"""
        if hasattr(self, 'send_pdf_button') and self.is_host and self.filepath and self.connection:
            self.send_pdf_button.configure(state="normal", text="📤 Enviar PDF ao Parceiro")
            print(f"[Debug] Botão de envio habilitado para arquivo: {os.path.basename(self.filepath)}")
        elif hasattr(self, 'send_pdf_button'):
            print(f"[Debug] Botão não habilitado - is_host: {self.is_host}, filepath: {bool(self.filepath)}, connection: {bool(self.connection)}")
        
    def disable_send_button(self, text="📤 Enviar PDF ao Parceiro"):
        """Desabilita o botão de envio de PDF"""
        if hasattr(self, 'send_pdf_button'):
            self.send_pdf_button.configure(state="disabled", text=text)
            
    def show_progress_bar(self):
        """Mostra a barra de progresso"""
        if hasattr(self, 'progress_frame') and not self.progress_frame_visible:
            self.progress_frame.grid(row=1, column=0, columnspan=7, sticky="ew", padx=5, pady=(0, 5))
            self.progress_frame_visible = True
            self.progress_bar.set(0)
            self.progress_label.configure(text="Enviando: 0%")
            
    def hide_progress_bar(self):
        """Oculta a barra de progresso"""
        if hasattr(self, 'progress_frame') and self.progress_frame_visible and not self._destroyed:
            try:
                if self.progress_frame.winfo_exists():
                    self.progress_frame.grid_remove()
                    self.progress_frame_visible = False
            except Exception as e:
                print(f"[Debug] Erro ao ocultar barra de progresso (não crítico): {e}")
                self.progress_frame_visible = False
            
    def update_progress(self, progress_percent, sent_bytes, total_bytes):
        """Atualiza a barra de progresso"""
        if self._destroyed:
            return
            
        if hasattr(self, 'progress_bar') and self.progress_frame_visible:
            try:
                if self.progress_bar.winfo_exists():
                    self.progress_bar.set(progress_percent / 100.0)
                    
                    # Formatar bytes para exibição amigável
                    def format_bytes(bytes_value):
                        if bytes_value >= 1024 * 1024:
                            return f"{bytes_value / (1024 * 1024):.1f} MB"
                        elif bytes_value >= 1024:
                            return f"{bytes_value / 1024:.1f} KB"
                        else:
                            return f"{bytes_value} bytes"
                    
                    sent_str = format_bytes(sent_bytes)
                    total_str = format_bytes(total_bytes)
                    
                    if self.progress_label.winfo_exists():
                        self.progress_label.configure(text=f"Enviando: {progress_percent:.1f}% ({sent_str}/{total_str})")
            except Exception as e:
                print(f"[Debug] Erro ao atualizar progresso (não crítico): {e}")
            
    def update_receive_progress(self, progress_percent, received_bytes, total_bytes):
        """Atualiza a barra de progresso para recebimento"""
        if self._destroyed:
            return
            
        if hasattr(self, 'progress_bar') and self.progress_frame_visible:
            try:
                if self.progress_bar.winfo_exists():
                    self.progress_bar.set(progress_percent / 100.0)
                    
                    # Formatar bytes para exibição amigável
                    def format_bytes(bytes_value):
                        if bytes_value >= 1024 * 1024:
                            return f"{bytes_value / (1024 * 1024):.1f} MB"
                        elif bytes_value >= 1024:
                            return f"{bytes_value / 1024:.1f} KB"
                        else:
                            return f"{bytes_value} bytes"
                    
                    received_str = format_bytes(received_bytes)
                    total_str = format_bytes(total_bytes)
                    
                    if self.progress_label.winfo_exists():
                        self.progress_label.configure(text=f"Recebendo: {progress_percent:.1f}% ({received_str}/{total_str})")
            except Exception as e:
                print(f"[Debug] Erro ao atualizar progresso de recebimento (não crítico): {e}")
            
    def calculate_dynamic_timeout(self, file_size_bytes):
        """
        Calcula timeout dinâmico baseado no tamanho do arquivo.
        Considera velocidade mínima de 1KB/s para conexões lentas.
        """
        # Velocidade mínima esperada (bytes por segundo)
        min_speed_bps = 1024  # 1 KB/s (muito conservador)
        
        # Timeout base mínimo (30 segundos)
        base_timeout = 30
        
        # Calcular timeout baseado no tamanho do arquivo
        calculated_timeout = (file_size_bytes / min_speed_bps) + base_timeout
        
        # Limites: mínimo 60s, máximo 600s (10 minutos)
        min_timeout = 60
        max_timeout = 600
        
        dynamic_timeout = max(min_timeout, min(max_timeout, calculated_timeout))
        
        # Formatar tamanho para log
        if file_size_bytes >= 1024 * 1024:
            size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
        elif file_size_bytes >= 1024:
            size_str = f"{file_size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{file_size_bytes} bytes"
            
        print(f"[Debug] Timeout dinâmico calculado: {dynamic_timeout:.0f}s para arquivo de {size_str}")
        return int(dynamic_timeout)
        
    def calculate_adaptive_timeout(self, transferred_bytes, total_bytes, elapsed_time):
        """
        Calcula timeout adaptativo baseado na velocidade real de transferência.
        """
        if elapsed_time <= 0 or transferred_bytes <= 0:
            return 60  # Fallback para 60 segundos
            
        # Calcular velocidade atual (bytes por segundo)
        current_speed = transferred_bytes / elapsed_time
        
        # Bytes restantes
        remaining_bytes = total_bytes - transferred_bytes
        
        # Tempo estimado para completar (com margem de segurança de 50%)
        estimated_time = (remaining_bytes / current_speed) * 1.5
        
        # Adicionar buffer mínimo de 30 segundos
        adaptive_timeout = estimated_time + 30
        
        # Limites: mínimo 60s, máximo 600s
        adaptive_timeout = max(60, min(600, adaptive_timeout))
        
        speed_str = self.format_speed(current_speed)
        print(f"[Debug] Timeout adaptativo: {adaptive_timeout:.0f}s (velocidade: {speed_str})")
        
        return int(adaptive_timeout)
        
    def format_speed(self, bytes_per_second):
        """Formata velocidade para exibição"""
        if bytes_per_second >= 1024 * 1024:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
        elif bytes_per_second >= 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second:.0f} B/s"
            
    def sync_interface_state(self):
        """Sincroniza o estado da interface baseado nas condições atuais"""
        print(f"[Debug] Sincronizando interface - is_host: {self.is_host}, filepath: {bool(self.filepath)}, connection: {bool(self.connection)}")
        
        if self.is_host:
            if self.filepath and self.connection:
                # Host tem arquivo e conexão - pode enviar
                if hasattr(self, 'send_pdf_button'):
                    current_text = self.send_pdf_button.cget("text")
                    # Só habilitar se não foi enviado ainda
                    if "✓" not in current_text and "⏳" not in current_text:
                        print(f"[Debug] Habilitando botão de envio")
                        self.enable_send_button()
                    else:
                        print(f"[Debug] Botão não habilitado - status atual: {current_text}")
            else:
                # Host não tem condições para enviar
                print(f"[Debug] Desabilitando botão de envio")
                self.disable_send_button()
        
        # Atualizar display de mensagens baseado no estado
        if self.is_host and self.filepath and not self.connection:
            self.display_message("Sistema", "Aguardando parceiro conectar...")
        elif self.is_host and not self.filepath:
            self.display_message("Sistema", "Selecione um arquivo PDF para compartilhar.")
        elif not self.is_host and not hasattr(self, 'pdf_document'):
            self.display_message("Sistema", "Aguardando o host enviar o arquivo...")
        
    def manual_send_pdf(self):
        """Envia o PDF manualmente quando o host clica no botão"""
        if not self.filepath or not os.path.exists(self.filepath):
            CTkMessagebox(title="Erro", message="Arquivo PDF não encontrado.", icon="cancel")
            return
            
        if not self.connection:
            CTkMessagebox(title="Erro", message="Não há conexão ativa com o parceiro.", icon="cancel")
            return
        
        self.display_message("Sistema", "Enviando arquivo...")
        # Desabilitar botão e mostrar progresso durante envio
        self.disable_send_button("⏳ Enviando...")
        self.after(0, self.show_progress_bar)
            
        # Enviar em thread separada
        threading.Thread(target=self._manual_send_flow, daemon=True).start()
        
    def _manual_send_flow(self):
        """Thread para envio manual do PDF"""
        try:
            # Enviar arquivo direto via protocolo JSON - sem notificação separada
            print("[Debug] Enviando arquivo via protocolo JSON...")
            
            if self.send_pdf_to_client():
                self.display_message("Sistema", "PDF enviado com sucesso!")
                # Carregar o PDF no host também APÓS o envio
                self.after(0, self.load_pdf, self.filepath)
                # Atualizar botão e ocultar progresso após envio bem-sucedido
                self.after(0, lambda: self.disable_send_button("✓ PDF Enviado ao Parceiro"))
                self.after(100, self.hide_progress_bar)
            else:
                self.display_message("Sistema", "Erro ao enviar PDF.")
                # Reabilitar botão e ocultar progresso em caso de erro
                self.after(0, self.enable_send_button)
                self.after(100, self.hide_progress_bar)
        except Exception as e:
            print(f"[Erro] Erro no envio manual: {e}")
            self.display_message("Sistema", f"Erro no envio: {e}")
            self.after(0, self.enable_send_button)
            self.after(100, self.hide_progress_bar)

    def _host_setup_flow(self):
        """Configuração do host - não envia arquivo automaticamente"""
        try:
            print("[Info] Host preparado. Aguardando comando manual para enviar PDF...")
            self.start_receiver_thread()
        except Exception as e:
            print(f"[Erro] Erro no setup do host: {e}")
            import traceback
            traceback.print_exc()

    def connect_to_host(self):
        if self._destroyed:
            return
            
        self.display_message("Sistema", "Conectando ao host...")
        print(f"[Debug] Iniciando conexão com {self.conn_details}")
        # Reduzir delay para melhor responsividade
        self.after(200, lambda: threading.Thread(target=self._client_connection_flow, daemon=True).start())

    def _client_connection_flow(self):
        if self._destroyed:
            return
            
        max_attempts = 3
        attempt = 0
        connected = False
        
        while attempt < max_attempts and not connected and not self._destroyed:
            try:
                attempt += 1
                host_ip = self.conn_details.get("host")
                host_port = int(self.conn_details.get("port", 0))
                
                print(f"[Debug] Tentativa {attempt}/{max_attempts} - Conectando a {host_ip}:{host_port}")
                
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.settimeout(30)  # Timeout de 30 segundos por tentativa (aumentado)
                self.connection.connect((host_ip, host_port))
                
                connected = True
                self.display_message("Sistema", f"Conectado a {host_ip}:{host_port}")
                print(f"[Info] Conexão estabelecida com sucesso na tentativa {attempt}")
                
                # Cliente apenas inicia o receiver thread, aguarda o host enviar
                self.display_message("Sistema", "Conectado! Aguardando o host enviar o arquivo...")
                self.start_receiver_thread()
                
            except Exception as e:
                print(f"[Debug] Tentativa {attempt} falhou: {e}")
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                
                if attempt < max_attempts:
                    print(f"[Debug] Aguardando 2 segundos antes da próxima tentativa...")
                    import time
                    time.sleep(2)
                else:
                    print(f"[Erro] Todas as {max_attempts} tentativas falharam")
                    self.display_message("Sistema", f"Erro de conexão: {e}")
                    error_msg = str(e)
                    
                    def show_error():
                        if not self._destroyed:
                            CTkMessagebox(title="Erro", message=f"Não foi possível conectar ao host: {error_msg}", icon="cancel")
                            self.after(100, self.destroy)
                    
                    self.after(0, show_error)

    def send_pdf_to_client(self):
        try:
            if not self.filepath or not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Arquivo não encontrado: {self.filepath}")
                
            file_size = os.path.getsize(self.filepath)
            print(f"[Debug] Enviando arquivo via protocolo JSON: {self.filepath} ({file_size} bytes)")
            
            # Validação de sanidade do tamanho do arquivo
            if file_size <= 0 or file_size > (100 * 1024 * 1024):  # Max 100MB
                raise ValueError(f"Tamanho de arquivo inválido: {file_size} bytes. Esperado: 1 byte a 100MB")
            
            # Ler arquivo e codificar em base64
            print("[Debug] Lendo e codificando arquivo...")
            with open(self.filepath, 'rb') as f:
                file_data = f.read()
            
            import base64
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            print(f"[Debug] Arquivo codificado: {len(encoded_data)} caracteres base64")
            
            # Enviar arquivo via protocolo JSON normal
            file_message = {
                "type": "file_data",
                "filename": os.path.basename(self.filepath),
                "size": file_size,
                "data": encoded_data
            }
            
            print("[Debug] Enviando arquivo via mensagem JSON...")
            
            # Configurar timeout maior para arquivo grande
            original_timeout = self.connection.gettimeout()
            upload_timeout = max(120, file_size // (10 * 1024))  # Mínimo 2 minutos
            self.connection.settimeout(upload_timeout)
            
            # Enviar mensagem JSON com arquivo
            Protocol.send_message(self.connection, file_message)
            
            # Restaurar timeout original
            self.connection.settimeout(original_timeout)
            
            print(f"[Debug] ✅ Arquivo enviado completamente via JSON: {file_size} bytes")
            self.display_message("Sistema", "PDF enviado com sucesso!")
            return True
            
        except Exception as e: 
            print(f"[Erro] Erro ao enviar PDF: {e}")
            self.display_message("Sistema", f"Erro ao enviar PDF: {e}")
            return False

    # REMOVIDO: receive_pdf_from_host - substituído por handle_file_data via protocolo JSON
    # Não precisamos mais de protocolo binário, marcadores ou sincronização complexa
    def start_receiver_thread(self):
        self.receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self.receiver_thread.start()

    def _receiver_loop(self):
        print("[Debug] Iniciando loop de recepção de mensagens...")
        
        # Configurar timeout para mensagens
        if self.connection:
            self.connection.settimeout(120)  # 2 minutos para mensagens
        
        while self.running and not self._destroyed:
            try:
                if not self.connection:
                    print("[Debug] Conexão perdida, encerrando loop de recepção")
                    break
                    
                msg = Protocol.receive_message(self.connection)
                if msg is None: 
                    print("[Debug] Mensagem nula recebida, parceiro desconectou")
                    self.after(0, self.display_message, "Sistema", "O parceiro desconectou.")
                    break
                    
                self.after(0, self.handle_message, msg)
                
            except ConnectionError as e:
                print(f"[Debug] Erro de conexão no loop de recepção: {e}")
                if "Timeout" in str(e):
                    # Se for timeout, apenas continuar (não há mensagens para processar)
                    continue
                else:
                    # Se for outro erro de conexão, sair do loop
                    if self.running and not self._destroyed: 
                        self.after(0, self.display_message, "Sistema", "A conexão foi perdida.")
                    break
            except Exception as e:
                print(f"[Debug] Erro inesperado no loop de recepção: {e}")
                if self.running and not self._destroyed:
                    self.after(0, self.display_message, "Sistema", f"Erro na comunicação: {e}")
                break
        
        print("[Debug] Loop de recepção encerrado")

    def handle_message(self, msg):
        if not self.running: return
        msg_type = msg.get("type")
        if msg_type == "chat":
            self.display_message(self.target_info.get("username", "Parceiro"), msg.get("message", ""))
        elif msg_type == "sync":
            self.handle_sync_action(msg.get("action"), msg.get("data"))
        elif msg_type == "control":
            self.handle_control_action(msg.get("action"))
        elif msg_type == "annotation":
            self.handle_annotation_action(msg.get("action"), msg.get("data"))
        elif msg_type == "file_data":
            # Receber arquivo via protocolo JSON
            self.handle_file_data(msg)
    
    def handle_file_data(self, msg):
        """Processa arquivo recebido via protocolo JSON"""
        try:
            print("[Debug] Processando arquivo recebido via JSON...")
            
            filename = msg.get("filename", "arquivo_recebido.pdf")
            file_size = msg.get("size", 0)
            encoded_data = msg.get("data", "")
            
            print(f"[Debug] Arquivo: {filename}, Tamanho: {file_size} bytes")
            
            # Decodificar dados base64
            import base64
            file_data = base64.b64decode(encoded_data)
            
            if len(file_data) != file_size:
                print(f"[Aviso] Tamanho decodificado ({len(file_data)}) != esperado ({file_size})")
            
            # Salvar arquivo temporário
            import tempfile
            self.temp_pdf_path = os.path.join(tempfile.gettempdir(), f"collab_{self.session_id}.pdf")
            
            with open(self.temp_pdf_path, 'wb') as f:
                f.write(file_data)
            
            print(f"[Debug] ✅ Arquivo salvo: {self.temp_pdf_path} ({len(file_data)} bytes)")
            
            # Carregar PDF na interface
            self.display_message("Sistema", "PDF recebido com sucesso! Carregando...")
            self.after(0, self.load_pdf, self.temp_pdf_path)
            
        except Exception as e:
            print(f"[Erro] Erro ao processar arquivo JSON: {e}")
            import traceback
            traceback.print_exc()
            self.display_message("Sistema", f"Erro ao processar arquivo: {e}")
            
    # REMOVIDO: clear_connection_buffer - não mais necessário com protocolo JSON puro
        """Limpa buffer da conexão para evitar dados residuais"""
        try:
            # Configurar timeout muito baixo para drenar dados residuais
            original_timeout = self.connection.gettimeout()
            self.connection.settimeout(0.1)
            
            drained_bytes = 0
            while True:
                try:
                    data = self.connection.recv(1024)
                    if not data:
                        break
                    drained_bytes += len(data)
                    if drained_bytes > 10000:  # Limitar a 10KB de limpeza
                        print(f"[Aviso] Muitos dados residuais encontrados: {drained_bytes} bytes")
                        break
                except socket.timeout:
                    break
                except:
                    break
            
            if drained_bytes > 0:
                print(f"[Debug] Buffer limpo: {drained_bytes} bytes removidos")
            else:
                print("[Debug] Buffer já estava limpo")
                
            # Restaurar timeout original
            self.connection.settimeout(original_timeout)
            
        except Exception as e:
            print(f"[Debug] Erro ao limpar buffer (não crítico): {e}")

    def handle_annotation_action(self, action, data):
        if self.has_control: return
        if action == "add_highlight":
            rect_coords, page_num, color = data.get("rect"), data.get("page"), data.get("color")
            if rect_coords and page_num is not None and color:
                try:
                    page = self.pdf_document[page_num]
                    annot = page.add_highlight_annot(fitz.Rect(rect_coords))
                    if annot:
                        annot.set_colors(color)
                        annot.update()
                    if page_num == self.current_page: self.render_current_page()
                except Exception as e: print(f"Erro ao aplicar anotação recebida: {e}")

    def handle_sync_action(self, action, data):
        if self.has_control: return
        if action == "page_change":
            page = data.get("page", 0)
            if self.pdf_document and 0 <= page < len(self.pdf_document): self.current_page = page; self.render_current_page()
        elif action == "zoom_change": self.zoom_level = data.get("level", 1.0); self.render_current_page()
        elif action == "scroll_change":
            if (position := data.get("position")): self.pdf_scroll_frame._parent_canvas.yview_moveto(position[0])

    def handle_control_action(self, action):
        if action == "pass_control":
            self.has_control = True
            self.display_message("Sistema", "Você recebeu o controle!")
            self.update_control_ui()

    def periodic_scroll_sync(self):
        if self._destroyed or not self.running:
            return
            
        try:
            if self.has_control and hasattr(self, 'pdf_scroll_frame'):
                current_pos = self.pdf_scroll_frame._parent_canvas.yview()
                if current_pos != self.last_synced_scroll_pos:
                    self.last_synced_scroll_pos = current_pos
                    self.send_sync_action("scroll_change", {"position": current_pos})
        except Exception as e: 
            print(f"[Debug] Erro no sync de scroll: {e}")
            
        if self.running and not self._destroyed: 
            self.after(250, self.periodic_scroll_sync)

    def load_pdf(self, filepath):
        try:
            print(f"[Debug] Carregando PDF: {filepath} (is_host: {self.is_host})")
            self.pdf_document = fitz.open(filepath)
            self.current_page = 0
            self.render_current_page()
            print(f"[Debug] PDF carregado com sucesso: {len(self.pdf_document)} páginas")
        except Exception as e:
            error_msg = str(e)
            print(f"[Erro] Erro ao carregar PDF: {error_msg}")
            self.after(0, lambda msg=error_msg: CTkMessagebox(title="Erro de Leitura", message=f"Erro ao carregar PDF: {msg}", icon="cancel"))

    def render_current_page(self):
        if not self.pdf_document: return
        try:
            page = self.pdf_document[self.current_page]
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(pix.width, pix.height))
            self.pdf_label.configure(image=photo, text=""); self.pdf_label.image = photo
            self.update_page_label()
        except Exception as e: self.display_message("Sistema", f"Erro ao renderizar página do PDF: {e}")

    def send_annotation_action(self, action, data):
        if self.connection and self.has_control:
            try: Protocol.send_message(self.connection, {"type": "annotation", "action": action, "data": data})
            except ConnectionError: self.display_message("Sistema", "Não foi possível sincronizar a anotação. Conexão perdida.")

    def send_sync_action(self, action, data):
        if self.connection and self.has_control:
            try: Protocol.send_message(self.connection, {"type": "sync", "action": action, "data": data})
            except ConnectionError: self.display_message("Sistema", "Não foi possível sincronizar a ação. Conexão perdida.")

    def prev_page(self):
        if self.pdf_document and self.current_page > 0 and self.has_control:
            self.current_page -= 1; self.render_current_page()
            self.send_sync_action("page_change", {"page": self.current_page})

    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1 and self.has_control:
            self.current_page += 1; self.render_current_page()
            self.send_sync_action("page_change", {"page": self.current_page})

    def zoom_in(self):
        if self.has_control: self.zoom_level = min(3.0, self.zoom_level + 0.1); self.render_current_page(); self.send_sync_action("zoom_change", {"level": self.zoom_level})

    def zoom_out(self):
        if self.has_control: self.zoom_level = max(0.5, self.zoom_level - 0.1); self.render_current_page(); self.send_sync_action("zoom_change", {"level": self.zoom_level})
            
    def pass_control(self):
        if self.connection and self.has_control:
            try:
                Protocol.send_message(self.connection, {"type": "control", "action": "pass_control"})
                self.has_control = False
                self.display_message("Sistema", "Você passou o controle.")
                self.update_control_ui()
            except ConnectionError: self.display_message("Sistema", "Não foi possível passar o controle. Conexão perdida.")

    def send_message(self):
        message = self.msg_entry.get().strip()
        if not message:
            return
            
        if not self.connection:
            self.display_message("Sistema", "Não há conexão ativa para enviar mensagem.")
            return
            
        self.display_message("Eu", message)
        self.msg_entry.delete(0, "end")
        
        try: 
            print(f"[Debug] Enviando mensagem: {message}")
            Protocol.send_message(self.connection, {"type": "chat", "message": message})
            print(f"[Debug] Mensagem enviada com sucesso")
        except ConnectionError as e:
            print(f"[Debug] Erro ao enviar mensagem: {e}")
            self.display_message("Sistema", "Não foi possível enviar a mensagem. Conexão perdida.")
        except Exception as e:
            print(f"[Debug] Erro inesperado ao enviar mensagem: {e}")
            self.display_message("Sistema", f"Erro ao enviar mensagem: {e}")

    def display_message(self, sender, message):
        if self._destroyed:
            return
            
        if sender != "Eu": 
            self.grab_attention()
            
        def _update_chat():
            try:
                if self.winfo_exists() and not self._destroyed:
                    self.chat_text.configure(state="normal")
                    self.chat_text.insert("end", f"{sender}: {message}\n")
                    self.chat_text.configure(state="disabled")
                    self.chat_text.see("end")
            except Exception as e:
                print(f"[Debug] Erro ao atualizar chat: {e}")
                
        if not self._destroyed and self.winfo_exists(): 
            self.after(0, _update_chat)

    def grab_attention(self):
        if self._destroyed:
            return
            
        try:
            if self.state() == "normal" and self.focus_displayof(): 
                return
            self.deiconify()
            self.lift()
            
            if platform.system() == "Windows":
                hwnd = self.winfo_id()
                info = win32gui.FLASHWINFO()
                info.cbSize = ctypes.sizeof(info)
                info.hwnd = hwnd
                info.dwFlags = win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG
                info.uCount = 0
                info.dwTimeout = 0
                win32gui.FlashWindowEx(ctypes.byref(info))
        except Exception as e: print(f"Não foi possível piscar a janela (recurso não essencial): {e}")

    def stop_flashing(self):
        try:
            if platform.system() == "Windows": win32gui.FlashWindow(self.winfo_id(), False)
        except Exception: pass

    def update_control_ui(self):
        state = "normal" if self.has_control else "disabled"
        for btn in [self.prev_btn, self.next_btn, self.zoom_in_btn, self.zoom_out_btn, self.control_btn, self.cursor_btn, self.highlight_btn, self.save_btn]:
            btn.configure(state=state)
        for _, button in self.color_buttons: button.configure(state=state)
        if not self.has_control: self.select_tool("cursor")
        self.pdf_scroll_frame.configure(label_text=f"Visualizador de PDF ({'Você no controle' if self.has_control else 'Aguardando'})")

    def update_page_label(self):
        if self._destroyed:
            return
        try:
            if self.pdf_document and hasattr(self, 'page_label') and self.page_label.winfo_exists(): 
                self.page_label.configure(text=f"Página {self.current_page + 1} de {len(self.pdf_document)}")
        except Exception as e:
            print(f"[Debug] Erro ao atualizar label da página: {e}")

    def on_closing(self):
        if self._destroyed or not self.running: 
            return
        
        print("[Debug] Fechando janela de colaboração...")
        self._destroyed = True
        self.running = False
        
        if self.connection:
            try: 
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            except OSError as e: 
                print(f"[Debug] Erro ao fechar conexão: {e}")
        
        if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
            try: 
                os.remove(self.temp_pdf_path)
            except OSError as e: 
                print(f"[Debug] Erro ao remover arquivo temporário: {e}")
        
        try:
            self.destroy()
        except Exception as e:
            print(f"[Debug] Erro ao destruir janela: {e}")