# broadcast_window.py
# Define a janela para enviar mensagens de broadcast.

import customtkinter as ctk

class BroadcastWindow(ctk.CTkToplevel):
    """
    Janela para enviar uma mensagem de broadcast para todos os utilizadores online.
    """
    def __init__(self, master_app):
        super().__init__(master_app)
        try:
            from ui_manager import fade_in
            fade_in(self)
        except Exception:
            pass
        self.app = master_app
        self.title("Enviar Broadcast")
        self.geometry("400x200")

    def center_on_screen(self, width=400, height=200):
        self.update_idletasks()
        width = width or self.winfo_width()
        height = height or self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.transient(master_app)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(main_frame, text="Escreva a sua mensagem para todos os utilizadores online:", wraplength=350)
        label.pack(fill="x", padx=10, pady=(10, 5))

        self.message_entry = ctk.CTkEntry(main_frame, placeholder_text="A sua mensagem...", width=300)
        self.message_entry.pack(fill="x", padx=10, pady=5)
        self.message_entry.bind("<Return>", self.send_broadcast)

        send_button = ctk.CTkButton(main_frame, text="Enviar", command=self.send_broadcast)
        send_button.pack(padx=10, pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_broadcast(self, event=None):
        """Envia a mensagem de broadcast através do NetworkManager."""
        message = self.message_entry.get()
        if message:
            # Chama o método da aplicação principal para enviar a mensagem
            self.app.send_broadcast_message(message)
            self.message_entry.delete(0, "end")
            self.master.after(100, self.on_closing) # Fecha a janela após o envio

    def on_closing(self):
        """Lida com o fecho da janela de broadcast."""
        self.app.broadcast_window_closed()
        self.destroy()

class BroadcastMessageWindow(ctk.CTkToplevel):
    """
    Janela para exibir uma mensagem de broadcast recebida.
    """
    def __init__(self, parent, sender_name, message):
        super().__init__(parent)
        self.title("Mensagem Broadcast")
        self.geometry("400x200")
        self.center_on_screen()
        self.resizable(False, False)
        # Configurar janela sempre no topo
        self.attributes("-topmost", True)
        self.transient(parent)
        self.grab_set()

        # Frame principal
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

    def close_window(self):
        """Fecha a janela da mensagem de broadcast."""
        self.destroy()

    def reply_broadcast(self):
        """Inicia uma conversa privada com o remetente da mensagem de broadcast."""
        sender = self.sender_name
        self.app.start_private_chat(sender)

    def auto_close(self):
        """Fecha a janela automaticamente após 10 segundos."""
        self.destroy()

