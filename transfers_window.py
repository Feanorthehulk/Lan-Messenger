import customtkinter as ctk

class TransfersWindow(ctk.CTkToplevel):
    def update_theme(self):
        """Força atualização do tema na janela de transferências."""
        self.update_idletasks()
    def __init__(self, master_app):
        super().__init__(master_app)
        self.app = master_app

        self.title("Gerir Transferências")
        self.geometry("400x300")

        # Criar scrollable_frame ANTES de chamar center_on_screen
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.center_on_screen()

    def center_on_screen(self, width=400, height=300):
        self.update_idletasks()
        width = width or self.winfo_width()
        height = height or self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.transient(self.app)
        self.grab_set()
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.offer_widgets = {}

        # Ações em lote
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        actions_frame.grid_columnconfigure((0,1), weight=1)

        self.accept_all_btn = ctk.CTkButton(actions_frame, text="Aceitar todos para pasta padrão", command=self.accept_all)
        self.accept_all_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.close_btn = ctk.CTkButton(actions_frame, text="Fechar", command=self.on_closing)
        self.close_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_transfer_offer(self, sender_name, file_info, transfer_id):
        filename = file_info.get('filename', 'desconhecido')
        filesize_kb = file_info.get('filesize', 0) / 1024

        offer_frame = ctk.CTkFrame(self.scrollable_frame)
        offer_frame.pack(fill="x", expand=True, padx=5, pady=5)
        offer_frame.grid_columnconfigure(0, weight=1)

        info_label = ctk.CTkLabel(offer_frame, text=f"{sender_name} quer enviar: {filename} ({filesize_kb:.2f} KB)", wraplength=250)
        info_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        button_frame = ctk.CTkFrame(offer_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        accept_button = ctk.CTkButton(button_frame, text="Aceitar", width=70, command=lambda: self.respond(transfer_id, "accept", offer_frame))
        accept_button.pack(side="left", padx=(0, 5))
        
        reject_button = ctk.CTkButton(button_frame, text="Recusar", width=70, fg_color="#E74C3C", hover_color="#C0392B", command=lambda: self.respond(transfer_id, "reject", offer_frame))
        reject_button.pack(side="left")

        self.offer_widgets[transfer_id] = offer_frame

    def respond(self, transfer_id, response, frame):
        """--- LÓGICA ATUALIZADA AQUI ---"""
        # A janela agora só precisa de dizer à App QUAL foi a resposta.
        # A App (main.py) trata do resto.
        self.app.respond_to_file_offer(transfer_id, response)
        
        if frame.winfo_exists():
            frame.destroy()
        if transfer_id in self.offer_widgets:
            del self.offer_widgets[transfer_id]

    def accept_all(self):
        # Chama a App para aceitar em lote; ela gerencia a pasta e nomes
        self.app.accept_all_pending_file_offers()
        # Limpar UI das ofertas
        for tid, frame in list(self.offer_widgets.items()):
            try:
                if frame.winfo_exists():
                    frame.destroy()
            except Exception:
                pass
            self.offer_widgets.pop(tid, None)

    def on_closing(self):
        self.app.transfers_window_closed()
        self.destroy()
