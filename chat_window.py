import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog
import os
import re
import webbrowser
from PIL import Image
from pilmoji import Pilmoji
import emoji

class ChatWindow(ctk.CTkToplevel):
    def update_theme(self):
        """Força atualização do tema na janela de chat."""
        # Limpar a área de chat
        for widget in self.chat_area.winfo_children():
            widget.destroy()

        # Recarregar as mensagens com o novo tema
        for msg_data in self.messages:
            self.add_message_to_chat(msg_data['message'], msg_data['sender_name'], msg_data['is_own_message'], from_history=True)

        self.update_idletasks()

    def __init__(self, master_app, target_info):
        # Initialize with master_app as parent
        super().__init__(master_app)
        self.app = master_app
        self.messages = []  # Armazenar histórico de mensagens da janela
        try:
            from ui_manager import fade_in
            fade_in(self)
        except Exception:
            pass
        self.target_info = target_info
        self.target_id = target_info.get('id')
        self.target_name = target_info.get('username', 'Desconhecido')
        self._emoji_cache = {}
        self.image_references = []
        
        self.title(f"Conversa com {self.target_name}")
        
        # Calcular tamanho da tela disponível (excluindo barra de tarefas)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Definir tamanho da janela (máximo 80% da altura da tela)
        window_width = 500
        window_height = min(600, int(screen_height * 0.8))
        
        # Centralizar janela
        x = (screen_width - window_width) // 2
        y = max(50, (screen_height - window_height - 100) // 2)  # 100px para barra de tarefas
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.center_on_screen(window_width, window_height)

    def center_on_screen(self, width=500, height=600):
        self.update_idletasks()
        width = width or self.winfo_width()
        height = height or self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(400, 500)

        # Evitar que a janela principal se sobreponha
        self.lift()
        self.focus_force()

        # Configure window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.attributes('-topmost', False)

        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create widgets
        self.create_chat_widgets()
        
        # Bind events
        self.bind("<FocusIn>", lambda e: self.stop_flashing())
        
        # Initialize window state
        self.after(100, self.state, 'normal')

    def on_closing(self):
        """Handle window closing properly"""
        if hasattr(self.app.ui, 'chat_windows'):
            for user_id, window in list(self.app.ui.chat_windows.items()):
                if window == self:
                    del self.app.ui.chat_windows[user_id]
                    break
        self.destroy()

    def create_chat_widgets(self):
        # --- ALTERADO: Guardar referência ao main_frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self._original_fg_color = self.main_frame.cget("fg_color")

        self.chat_area = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_area.grid(row=0, column=0, columnspan=3, sticky="nsew")
        
        # Adicionar referência para compatibilidade
        self.messages_frame = self.chat_area

        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10,0))
        input_frame.grid_columnconfigure(2, weight=1)

        self.attach_button = ctk.CTkButton(input_frame, text="", width=30, command=self.on_attach_click)
        self.attach_button.grid(row=0, column=0, padx=(0,5))
        self.app.ui.icon_manager.apply_icon(self.attach_button, "attach")

        # Botão de emojis
        self.emoji_button = ctk.CTkButton(input_frame, text="🙂", width=30, command=self.open_emoji_picker)
        self.emoji_button.grid(row=0, column=1, padx=(0,5))

        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite uma mensagem...")
        self.chat_entry.grid(row=0, column=2, sticky="ew")
        self.chat_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(input_frame, text="", width=30, command=self.send_message)
        self.send_button.grid(row=0, column=3, padx=(5,0))
        self.app.ui.icon_manager.apply_icon(self.send_button, "send")

    def attach_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return
        file_info = {
            'filename': os.path.basename(filepath),
            'filesize': os.path.getsize(filepath)
        }
        self.add_file_banner(file_info, self.app.username, is_own_message=True)
        self.app.network_manager.send_file_offer(self.target_id, filepath)

    def on_attach_click(self):
        """Abre um diálogo para escolher o tipo de envio de arquivo."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tipo de Partilha")
        dialog.geometry("320x120")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        label = ctk.CTkLabel(container, text="Como deseja partilhar o ficheiro?")
        label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 10))

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, pady=(5, 5))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        def simple_send():
            dialog.destroy()
            self.attach_file()

        def collab_send():
            dialog.destroy()
            self.start_collaborative_session()

        simple_button = ctk.CTkButton(button_frame, text="Envio Simples", command=simple_send)
        simple_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        collab_button = ctk.CTkButton(button_frame, text="Sessão Colaborativa", command=collab_send)
        collab_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.after(20, lambda: self._center_dialog(dialog))

    def _center_dialog(self, dialog):
        self.update_idletasks()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"+{x}+{y}")

    def open_emoji_picker(self):
        import os
        from PIL import Image
        picker = ctk.CTkToplevel(self, fg_color=ctk.ThemeManager.theme['CTkFrame']['fg_color'])
        try:
            from ui_manager import fade_in
            fade_in(picker)
        except Exception:
            pass
        picker.title("Emojis")
        picker.geometry("420x400")
        picker.minsize(420, 400)
        picker.transient(self)
        picker.grab_set()
        picker.resizable(True, True)

        frame = ctk.CTkScrollableFrame(picker)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        emoji_dir = os.path.join(os.path.dirname(__file__), "emojis")
        emoji_files = [f for f in os.listdir(emoji_dir) if f.endswith('.png')]
        emoji_files.sort()
        self._emoji_picker_images = []  # Evita garbage collection
        cols = 12
        for idx, filename in enumerate(emoji_files):
            codepoint = filename.replace('.png','')
            # Converter codepoint para caractere unicode
            try:
                chars = ''.join([chr(int(cp, 16)) for cp in codepoint.split('-')])
            except Exception:
                continue
            img_path = os.path.join(emoji_dir, filename)
            try:
                img = Image.open(img_path).resize((32,32), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32,32))
                self._emoji_picker_images.append(ctk_img)
                r, c = divmod(idx, cols)
                btn = ctk.CTkButton(frame, text="", image=ctk_img, width=40, height=40, command=lambda e=chars: self.insert_emoji(e, picker))
                btn.grid(row=r, column=c, padx=4, pady=4)
            except Exception:
                continue

    def insert_emoji(self, emoji, picker):
        try:
            pos = self.chat_entry.index("insert")
            self.chat_entry.insert(pos, emoji)
        except Exception:
            self.chat_entry.insert("end", emoji)
        try:
            picker.destroy()
        except Exception:
            pass

    def start_collaborative_session(self):
        """Inicia uma sessão de colaboração pedindo ao usuário para selecionar um arquivo."""
        print(f"Iniciando convite de colaboração para {self.target_name}")
        
        # Pedir ao usuário para selecionar um arquivo PDF
        from tkinter import filedialog
        
        # Temporariamente colocar a janela no topo para o diálogo
        self.attributes("-topmost", True)
        
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Selecione um PDF para colaborar",
            filetypes=[("PDF files", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        
        # Remover do topo
        self.attributes("-topmost", False)
        
        if not filepath:
            print("Nenhum arquivo selecionado para colaboração")
            return
        
        print(f"Arquivo selecionado: {filepath}")
        print(f"Enviando pedido de colaboração para {self.target_name}")
        
        session_id = self.app.network_manager.send_collab_request(self.target_id, filepath)

        def _add_banner():
            if session_id:
                import os
                filename = os.path.basename(filepath)
                self.add_collab_banner(
                    invite_info={"session_id": session_id, "filename": filename},
                    sender_name=self.app.username,
                    is_own_message=True,
                    session_id=session_id
                )
                print(f"[Info] Banner de convite de colaboração adicionado ao chat para {filename}")
            else:
                self.add_collab_banner(
                    invite_info={"session_id": None, "filename": "colaboração (erro)"},
                    sender_name=self.app.username,
                    is_own_message=True
                )
        
        # Agenda a atualização da UI para garantir que seja executada de forma estável
        self.after(1, _add_banner)

    def send_message(self, event=None):
        message = self.chat_entry.get()
        if message.strip() == "": return
        url_pattern = re.compile(r'https?://\S+')
        if url_pattern.match(message.strip()):
            self.add_link_banner(message.strip(), self.app.username, is_own_message=True)
        else:
            self.add_message_to_chat(message, self.app.username, is_own_message=True)
            self.app.network_manager.send_private_message(self.target_id, message)
            
            # Salvar mensagem enviada no banco de dados
            target_info = self.app.network_manager.online_users.get(self.target_id, {})
            target_name = target_info.get('username', 'Desconhecido')
            self.app.db_manager.save_message(
                sender=self.app.username,
                receiver=target_name,
                message=message,
                sender_id=self.app.network_manager.user_id,
                receiver_id=self.target_id
            )
        self.chat_entry.delete(0, "end")

    def add_message_to_chat(self, message, sender_name, is_own_message, from_history=False):
        if not from_history:
            self.messages.append({'message': message, 'sender_name': sender_name, 'is_own_message': is_own_message})

        if not is_own_message: self.grab_attention()
        # Prefer new config keys, but fallback to older key names to remain compatible
        my_color = self.app.config.get("my_bubble_color",
                                     self.app.config.get("balloon_color", "#2b59da"))
        contact_color = self.app.config.get("contact_bubble_color",
                                            self.app.config.get("contact_balloon_color", "#363636"))
        bubble_color = my_color if is_own_message else contact_color
        anchor = "e" if is_own_message else "w"

        # Main frame for the message line
        line_frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        line_frame.pack(fill="x", padx=10, pady=2)

        # Configure columns to align bubble left or right
        if anchor == 'e':
            line_frame.grid_columnconfigure(0, weight=1) # Spacer
            line_frame.grid_columnconfigure(1, weight=0) # Bubble
        else: # 'w'
            line_frame.grid_columnconfigure(0, weight=0) # Bubble
            line_frame.grid_columnconfigure(1, weight=1) # Spacer

        import os
        from PIL import Image
        emoji_matches = emoji.emoji_list(message)
        only_emojis = False
        # Verifica se a mensagem é só emoji(s) (ignorando espaços)
        if emoji_matches and ''.join([m['emoji'] for m in emoji_matches]).replace(' ', '') == message.replace(' ', ''):
            only_emojis = True

        emoji_imgs = []
        for match in emoji_matches:
            emoji_char = match['emoji']
            codepoints = '-'.join(f"{ord(c):x}" for c in emoji_char).lower()
            png_path = os.path.join("emojis", f"{codepoints}.png")
            found = False
            if os.path.exists(png_path):
                found = True
            else:
                codepoints_simple = '-'.join([cp for cp in codepoints.split('-') if cp not in ("fe0f", "200d")])
                png_path_simple = os.path.join("emojis", f"{codepoints_simple}.png")
                if os.path.exists(png_path_simple):
                    png_path = png_path_simple
                    found = True
            if found:
                try:
                    img = Image.open(png_path).resize((32, 32), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32,32))
                    if not hasattr(self, 'image_references'):
                        self.image_references = []
                    self.image_references.append(ctk_img)
                    emoji_imgs.append(ctk_img)
                except Exception:
                    pass

        if only_emojis and emoji_imgs:
            # Só emojis: exibir imagens centralizadas
            emoji_frame = ctk.CTkFrame(line_frame, fg_color="transparent")
            emoji_frame.grid(row=0, column=0, columnspan=2, pady=6)
            for i, tk_img in enumerate(emoji_imgs):
                lbl = ctk.CTkLabel(emoji_frame, image=tk_img, text="", width=36, height=36)
                lbl.grid(row=0, column=i, padx=2)
        else:
            # Texto + emoji: balão + emojis ao lado
            # Use configured text color if provided (fallback to white)
            bubble_text_color = self.app.config.get("text_color", "white")
            font_family = self.app.config.get("font_family", "System")
            font_size = self.app.config.get("font_size", 13)
            font_bold = self.app.config.get("font_bold", False)
            # Se for System e bold, usar Arial bold como fallback visual
            if font_bold:
                if font_family.lower() == "system":
                    text_font = ctk.CTkFont(family="Arial", size=font_size, weight="bold")
                else:
                    text_font = ctk.CTkFont(family=font_family, size=font_size, weight="bold")
            else:
                text_font = ctk.CTkFont(family=font_family, size=font_size, weight="normal")
            bubble = ctk.CTkTextbox(
                line_frame, corner_radius=10, fg_color=bubble_color, text_color=bubble_text_color,
                wrap="word", border_width=0, activate_scrollbars=False, padx=5, pady=5, font=text_font
            )
            # Inserir texto normalmente (sem emojis)
            msg_no_emoji = message
            for match in reversed(emoji_matches):
                start, end = match['match_start'], match['match_end']
                msg_no_emoji = msg_no_emoji[:start] + msg_no_emoji[end:]
            bubble.insert("end", msg_no_emoji.strip())
            bubble.configure(state="disabled")
            bubble.update_idletasks()
            num_lines = int(bubble.index("end-1c").split('.')[0])
            height = (num_lines * (text_font.cget('size') + 8)) + 10
            bubble.configure(height=height)
            # Place bubble
            bubble_col = 1 if anchor == 'e' else 0
            bubble.grid(row=0, column=bubble_col, sticky='w' if anchor == 'w' else 'e')
            # Emojis ao lado do balão
            if emoji_imgs:
                emoji_frame = ctk.CTkFrame(line_frame, fg_color="transparent")
                emoji_col = 0 if anchor == 'e' else 1
                emoji_frame.grid(row=0, column=emoji_col, padx=4)
                for i, tk_img in enumerate(emoji_imgs):
                    lbl = ctk.CTkLabel(emoji_frame, image=tk_img, text="", width=36, height=36)
                    lbl.grid(row=0, column=i, padx=2)
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M")
        details_label = ctk.CTkLabel(line_frame, text=f"{sender_name} - {timestamp}", font=ctk.CTkFont(size=10), text_color="gray")
        details_label.grid(row=1, column=1 if anchor == 'e' else 0, sticky=anchor, padx=5)
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)

    def add_file_banner(self, file_info, sender_name, is_own_message, transfer_id=None):
        if not is_own_message: self.grab_attention()
        filename = file_info.get('filename', 'desconhecido')
        filesize_kb = file_info.get('filesize', 0) / 1024
        banner_frame = ctk.CTkFrame(self.chat_area, border_width=1, border_color="gray")
        banner_frame.pack(fill="x", padx=40, pady=10)
        file_icon = ctk.CTkLabel(banner_frame, text="")
        self.app.ui.icon_manager.apply_icon(file_icon, "attach", size=24)
        file_icon.pack(side="left", padx=10, pady=10)
        info_frame = ctk.CTkFrame(banner_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=10)
        filename_label = ctk.CTkLabel(info_frame, text=filename, font=ctk.CTkFont(weight="bold"), anchor="w")
        filename_label.pack(fill="x")
        status_label = ctk.CTkLabel(info_frame, text=f"{filesize_kb:.2f} KB", font=ctk.CTkFont(size=10), anchor="w")
        status_label.pack(fill="x")
        if not is_own_message and transfer_id:
            button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(5,0))
            accept_button = ctk.CTkButton(button_frame, text="Aceitar", width=70, command=lambda: self.respond_to_offer(transfer_id, "accept", banner_frame))
            accept_button.pack(side="left", padx=(0, 5))
            reject_button = ctk.CTkButton(button_frame, text="Recusar", width=70, fg_color="#E74C3C", hover_color="#C0392B", command=lambda: self.respond_to_offer(transfer_id, "reject", banner_frame))
            reject_button.pack(side="left")
        elif is_own_message:
            sent_status_label = ctk.CTkLabel(info_frame, text="Oferta de ficheiro enviada...", font=ctk.CTkFont(size=10, slant="italic"), anchor="w")
            sent_status_label.pack(fill="x")
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)

    def respond_to_offer(self, transfer_id, response, banner_frame):
        self.app.respond_to_file_offer(transfer_id, response)
        for widget in banner_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for button in widget.winfo_children():
                    button.destroy()
                widget.destroy()

    def grab_attention(self):
        """Chama a atenção do utilizador, piscando a janela na barra de tarefas."""
        if self.state() == "normal" and self.focus_displayof():
            return

        self.deiconify()
        self.lift()

        try:
            import platform
            if platform.system() == "Windows":
                import win32gui
                import win32con
                import ctypes

                # Adicionada verificação de segurança para evitar erros com a biblioteca pywin32
                if not hasattr(win32gui, 'FLASHWINFO') or not hasattr(win32gui, 'FlashWindowEx'):
                    print("[Debug] pywin32 não possui as funções necessárias para piscar a janela.")
                    return

                hwnd = self.winfo_id()
                info = win32gui.FLASHWINFO()
                info.cbSize = ctypes.sizeof(info)
                info.hwnd = hwnd
                info.dwFlags = win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG
                info.uCount = 0
                info.dwTimeout = 0
                win32gui.FlashWindowEx(ctypes.byref(info))
        except (ImportError, Exception) as e:
            print(f"Não foi possível piscar a janela (recurso não essencial): {e}")

    def stop_flashing(self):
        """Para de piscar a janela (se estiver a piscar)."""
        try:
            import platform
            if platform.system() == "Windows":
                import win32gui
                hwnd = self.winfo_id()
                win32gui.FlashWindow(hwnd, False)
        except (ImportError, Exception):
            # Ignora o erro se o pywin32 não estiver instalado ou se houver outro problema
            pass

    def add_link_banner(self, link, sender_name, is_own_message):
        if not is_own_message: self.grab_attention()
        anchor = "e" if is_own_message else "w"
        banner_frame = ctk.CTkFrame(self.chat_area, border_width=1, border_color="gray")
        banner_frame.pack(fill="x", padx=40, pady=10)
        link_icon = ctk.CTkLabel(banner_frame, text="")
        self.app.ui.icon_manager.apply_icon(link_icon, "transfers", size=24)
        link_icon.pack(side="left", padx=10, pady=10)
        info_frame = ctk.CTkFrame(banner_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=10, padx=(0, 10))
        link_label = ctk.CTkLabel(info_frame, text=link, anchor="w", wraplength=200)
        link_label.pack(fill="x", pady=(0, 5))
        open_button = ctk.CTkButton(info_frame, text="Abrir Link", command=lambda: webbrowser.open(link))
        open_button.pack(anchor="w")
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)

    # Método movido para baixo - ver add_collab_banner mais completo

    def add_collab_invitation_banner(self, session_id, sender_id):
        """Adiciona um banner à conversa para um convite de colaboração."""
        self.grab_attention()
        
        banner_frame = ctk.CTkFrame(self.chat_area, border_width=1, border_color="#2E7D32")
        banner_frame.pack(fill="x", padx=40, pady=10)
        
        collab_icon = ctk.CTkLabel(banner_frame, text="")
        self.app.ui.icon_manager.apply_icon(collab_icon, "collaborate", size=24)
        collab_icon.pack(side="left", padx=10, pady=10)
        
        info_frame = ctk.CTkFrame(banner_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=10)
        
        invitation_text = f"{self.target_name} convidou-o para uma sessão de colaboração."
        collab_label = ctk.CTkLabel(info_frame, text=invitation_text, font=ctk.CTkFont(weight="bold"), anchor="w")
        collab_label.pack(fill="x")
        
        # Frame para os botões
        button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5,0))
        
        accept_button = ctk.CTkButton(
            button_frame, 
            text="Aceitar", 
            width=70, 
            command=lambda: self.app.respond_to_collab_request(session_id, "accept", sender_id, banner_frame)
        )
        accept_button.pack(side="left", padx=(0, 5))
        
        reject_button = ctk.CTkButton(
            button_frame, 
            text="Recusar", 
            width=70, 
            fg_color="#E74C3C", 
            hover_color="#C0392B", 
            command=lambda: self.app.respond_to_collab_request(session_id, "reject", sender_id, banner_frame)
        )
        reject_button.pack(side="left")
        
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)

    def add_collab_banner(self, invite_info, sender_name, is_own_message=False, session_id=None):
        """Adiciona um banner de convite de colaboração ao chat."""
        
        # Verificar se já existe um banner para esta sessão
        if hasattr(self, '_collab_banners') and session_id in self._collab_banners:
            # Atualizar banner existente
            self.update_collab_banner_status(session_id, invite_info.get('filename', 'colaboração'))
            return
        
        # Inicializar dicionário de banners se não existir
        if not hasattr(self, '_collab_banners'):
            self._collab_banners = {}
        
        # Criar o frame para o banner
        banner_frame = ctk.CTkFrame(self.messages_frame)
        
        # Determinar a posição (direita se for própria mensagem, esquerda caso contrário)
        side = "right" if is_own_message else "left"
        banner_frame.pack(fill="x", padx=(10 if side == "left" else 50, 50 if side == "left" else 10), 
                         pady=5, anchor="e" if side == "right" else "w")
        
        # Salvar referência do banner
        self._collab_banners[session_id] = {
            'frame': banner_frame,
            'is_own_message': is_own_message
        }
        
        # Área superior: ícone e nome
        header_frame = ctk.CTkFrame(banner_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Ícone
        icon_label = ctk.CTkLabel(header_frame, text="🔄", font=ctk.CTkFont(size=16))
        icon_label.pack(side="left", padx=5)
        
        # Nome do remetente/destinatário
        name_label = ctk.CTkLabel(header_frame, text=sender_name, 
                                  font=ctk.CTkFont(size=12, weight="bold"))
        name_label.pack(side="left", padx=5)
        
        # Texto de convite
        filename = invite_info.get('filename', 'um documento')
        message_text = f"{ 'Enviou' if is_own_message else 'Convidou-o para' } colaborar em \"{filename}\""
        
        message_frame = ctk.CTkFrame(banner_frame)
        message_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        message_label = ctk.CTkLabel(message_frame, text=message_text, 
                                     font=ctk.CTkFont(size=12), 
                                     wraplength=300,
                                     justify="left")
        message_label.pack(fill="x", padx=5, pady=5)
        
        # Área de botões
        buttons_frame = ctk.CTkFrame(banner_frame)
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Salvar referência do frame de botões para atualização
        self._collab_banners[session_id]['buttons_frame'] = buttons_frame
        
        # Se for uma mensagem própria, apenas mostrar "Aguardando..."
        if is_own_message:
            status_label = ctk.CTkLabel(buttons_frame, text="Aguardando resposta...", 
                                        font=ctk.CTkFont(size=11, slant="italic"))
            status_label.pack(side="right", padx=5)
            self._collab_banners[session_id]['status_label'] = status_label
        else:
            # Botões de aceitar/rejeitar
            reject_btn = ctk.CTkButton(
                buttons_frame, 
                text="Recusar", 
                width=80, 
                height=25,
                command=lambda s=session_id: self.app.respond_to_collab_invite(s, "reject")
            )
            reject_btn.pack(side="right", padx=5)
            
            accept_btn = ctk.CTkButton(
                buttons_frame, 
                text="Aceitar", 
                width=80, 
                height=25,
                fg_color="#28a745", 
                hover_color="#218838",
                command=lambda s=session_id: self.app.respond_to_collab_invite(s, "accept")
            )
            accept_btn.pack(side="right", padx=5)
        
        # Rolar para o último item
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)

    def update_collab_banner_status(self, session_id, status_text):
        """Atualiza o status de um banner de colaboração existente."""
        if not hasattr(self, '_collab_banners') or session_id not in self._collab_banners:
            return
        
        banner_info = self._collab_banners[session_id]
        
        # Se for mensagem própria, atualizar o status
        if banner_info['is_own_message'] and 'status_label' in banner_info:
            banner_info['status_label'].configure(text=status_text)
        elif not banner_info['is_own_message']:
            # Para convites recebidos, remover botões e mostrar status
            buttons_frame = banner_info['buttons_frame']
            
            # Limpar botões existentes
            for widget in buttons_frame.winfo_children():
                widget.destroy()
            
            # Adicionar label de status
            status_label = ctk.CTkLabel(buttons_frame, text=status_text,                                        font=ctk.CTkFont(size=11, slant="italic"))
            status_label.pack(side="right", padx=5)
