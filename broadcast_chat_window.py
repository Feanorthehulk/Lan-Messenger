import customtkinter as ctk
from datetime import datetime

class BroadcastChatWindow(ctk.CTkToplevel):
    def update_theme(self):
        """Força atualização do tema na janela de broadcast."""
        self.update_idletasks()
    def __init__(self, master_app):
        super().__init__(master_app)
        try:
            from ui_manager import fade_in
            fade_in(self)
        except Exception:
            pass
        self.app = master_app
        self.title("Mensagens de Broadcast")
        self.geometry("700x600")
        self.center_on_screen()

    def center_on_screen(self, width=700, height=600):
        self.update_idletasks()
        width = width or self.winfo_width()
        height = height or self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(500, 500)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.attributes('-topmost', False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_chat_widgets()
        self.populate_user_list()
        
        self.after(100, self.state, 'normal')

    def on_closing(self):
        if hasattr(self.app.ui, 'broadcast_chat_window_instance'):
            self.app.ui.broadcast_chat_window_instance = None
        self.destroy()

    def create_chat_widgets(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.chat_area = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_area.grid(row=0, column=0, sticky="nsew")

        self.user_list_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.user_list_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(self.user_list_frame, text="Utilizadores Online", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=5)

        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10,0))
        input_frame.grid_columnconfigure(0, weight=1)

        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite uma mensagem...")
        self.chat_entry.grid(row=0, column=0, sticky="ew")
        self.chat_entry.bind("<Return>", self.send_to_all)

        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=(5,0))

        self.send_all_button = ctk.CTkButton(button_frame, text="Enviar a Todos", command=self.send_to_all)
        self.send_all_button.pack(side="left")

        self.send_selected_button = ctk.CTkButton(button_frame, text="Enviar a Selecionados", command=self.send_to_selected)
        self.send_selected_button.pack(side="left", padx=(5,0))

    def populate_user_list(self):
        for widget in self.user_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.destroy()

        self.user_checkboxes = {}
        online_users = self.app.network_manager.online_users
        for user_id, user_info in online_users.items():
            if user_id != self.app.network_manager.user_id:
                username = user_info.get('username', 'Desconhecido')
                checkbox = ctk.CTkCheckBox(self.user_list_frame, text=username)
                checkbox.pack(anchor="w", padx=5, pady=2)
                self.user_checkboxes[user_id] = checkbox

    def send_to_all(self, event=None):
        message = self.chat_entry.get()
        if message.strip() == "": return
        self.app.send_broadcast_message(message)
        self.add_message_to_chat(message, f"{self.app.username} (Eu)")
        self.chat_entry.delete(0, "end")

    def send_to_selected(self):
        message = self.chat_entry.get()
        if message.strip() == "": return
        
        selected_users = []
        for user_id, checkbox in self.user_checkboxes.items():
            if checkbox.get() == 1:
                selected_users.append(user_id)

        if not selected_users:
            # Maybe show a small popup that no user is selected
            return

        self.app.send_private_message_to_many(selected_users, message)
        self.add_message_to_chat(message, f"{self.app.username} (para selecionados)")
        self.chat_entry.delete(0, "end")

    def add_message_to_chat(self, message, sender_name):
        is_own_message = sender_name.startswith(f"{self.app.username} (")
        bubble_color = "#2b59da" if is_own_message else "#363636"
        anchor = "e" if is_own_message else "w"
        
        msg_frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        msg_frame.pack(fill="x", padx=10, pady=5)
        
        bubble = ctk.CTkLabel(msg_frame, text=message, fg_color=bubble_color, corner_radius=10, wraplength=400, justify="left", text_color="white")
        bubble.pack(anchor=anchor, padx=5, pady=(0,2))
        
        timestamp = datetime.now().strftime("%H:%M")
        details_label = ctk.CTkLabel(msg_frame, text=f"{sender_name} - {timestamp}", font=ctk.CTkFont(size=10), text_color="gray")
        details_label.pack(anchor=anchor, padx=10)
        
        self.after(100, self.chat_area._parent_canvas.yview_moveto, 1.0)
