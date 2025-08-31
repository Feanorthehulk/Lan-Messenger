# Lan Messenger/notification_window.py
import customtkinter as ctk

class NotificationWindow(ctk.CTkToplevel):
    """
    Uma janela de notificação pop-up construída inteiramente com CustomTkinter
    para evitar conflitos de bibliotecas de UI.
    """
    def __init__(self, master, title, message, auto_close=True, click_callback=None):
        super().__init__(master)

        self.master = master
        self.click_callback = click_callback

        # Esconde a janela até estar pronta para ser exibida
        self.withdraw()
        # Remove a barra de título e as bordas padrão do Windows
        self.overrideredirect(True)
        
        # Configurações da janela
        self.configure(fg_color=("#E0E0E0", "#2E2E2E"))
        self.attributes("-topmost", True) # Mantém a notificação no topo

        # --- Layout Interno ---
        self.grid_columnconfigure(0, weight=1)
        
        # Título da Notificação
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")

        # Mensagem da Notificação
        self.message_label = ctk.CTkLabel(self, text=message, wraplength=280, justify="left")
        self.message_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        # Associa o evento de clique a toda a janela
        self.bind("<Button-1>", self.on_click)
        self.title_label.bind("<Button-1>", self.on_click)
        self.message_label.bind("<Button-1>", self.on_click)

        # Posiciona e exibe a janela
        self.position_window()
        self.fade_in()

        if auto_close:
            self.after(5000, self.fade_out) # Fecha após 5 segundos

    def position_window(self):
        """Calcula a posição da janela no canto inferior direito do ecrã."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = screen_width - width - 20
        y = screen_height - height - 40 # 40px para dar espaço para a barra de tarefas
        
        self.geometry(f"{width}x{height}+{x}+{y}")

    def fade_in(self):
        """Animação de aparecimento suave."""
        self.attributes("-alpha", 0.0)
        self.deiconify()
        for i in range(101):
            alpha = i / 100
            self.attributes("-alpha", alpha)
            self.update()
            self.after(5) # Pequeno atraso para a animação

    def fade_out(self):
        """Animação de desaparecimento suave e destrói a janela."""
        try:
            for i in range(101):
                alpha = (100 - i) / 100
                self.attributes("-alpha", alpha)
                self.update()
                self.after(5)
        except Exception:
            # A janela pode já ter sido destruída
            pass
        finally:
            if self.winfo_exists():
                self.destroy()

    def on_click(self, event=None):
        """Executa a função de callback ao clicar e fecha a notificação."""
        if self.click_callback:
            self.click_callback()
        self.fade_out()
        
    def update_content(self, title, message):
        """Atualiza o conteúdo de uma notificação existente."""
        self.title_label.configure(text=title)
        self.message_label.configure(text=message)
        self.position_window()
