import customtkinter as ctk
from settings_window import SettingsWindow
import json

# Configurações de teste
test_config = {
    "username": "TestUser",
    "admin_password": "admin",
    "font_family": "System",
    "font_size": 13
}

class TestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Teste - Configurações")
        self.geometry("300x200")
        
        self.config = test_config
        self.username = "TestUser"
        
        # Botão para abrir configurações
        test_button = ctk.CTkButton(self, text="Abrir Configurações", command=self.open_settings)
        test_button.pack(pady=50)
        
    def open_settings(self):
        settings_window = SettingsWindow(self)
        
    def save_config(self):
        print("Configuração salva:", self.config)
        
    def export_full_history(self):
        print("Exportar histórico chamado")

if __name__ == "__main__":
    app = TestApp()
    app.mainloop()
