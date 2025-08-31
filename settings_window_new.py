import customtkinter as ctk
from tkinter.colorchooser import askcolor
import json
import winreg
import sys
import os

class SettingsWindow(ctk.CTkToplevel):
    """
    Janela para as configurações da aplicação, com mais opções e segurança.
    """
    def __init__(self, master_app):
        super().__init__(master_app)
        self.app = master_app
        self.config = master_app.config

        self.title("Configurações")
        self.geometry("450x700") # Aumentei a altura para acomodar novo campo
        self.resizable(False, False)
        self.transient(master_app)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=15, pady=15)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.admin_export_button = None
        self.admin_functions_frame = None
        
        self.setup_ui_widgets()
        self.setup_admin_widgets()
        self.load_current_settings()
        
        save_button = ctk.CTkButton(self.main_frame, text="Salvar e Fechar", command=self.save_and_close)
        save_button.grid(row=10, column=0, columnspan=2, pady=(30, 0), sticky="ew")

    def setup_ui_widgets(self):
        """Cria os widgets de personalização da UI, incluindo a escolha de fonte."""
        
        # Seção de Perfil do Usuário
        profile_label = ctk.CTkLabel(self.main_frame, text="Perfil do Usuário", font=ctk.CTkFont(size=16, weight="bold"))
        profile_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")
        
        username_label = ctk.CTkLabel(self.main_frame, text="Nome de usuário:")
        username_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.username_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Digite seu nome")
        self.username_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Seção de Interface
        ui_options_label = ctk.CTkLabel(self.main_frame, text="Opções da Interface", font=ctk.CTkFont(size=16, weight="bold"))
        ui_options_label.grid(row=2, column=0, columnspan=2, pady=(20, 15), sticky="w")

        font_family_label = ctk.CTkLabel(self.main_frame, text="Fonte:")
        font_family_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        font_options = ["System", "Arial", "Calibri", "Times New Roman"]
        self.font_family_menu = ctk.CTkOptionMenu(self.main_frame, values=font_options)
        self.font_family_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        font_size_label = ctk.CTkLabel(self.main_frame, text="Tamanho da Fonte:")
        font_size_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.font_size_slider = ctk.CTkSlider(self.main_frame, from_=10, to=20, number_of_steps=10)
        self.font_size_slider.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        colors_label = ctk.CTkLabel(self.main_frame, text="Personalização de Cores", font=ctk.CTkFont(size=16, weight="bold"))
        colors_label.grid(row=5, column=0, columnspan=2, pady=(20, 15), sticky="w")

        text_color_label = ctk.CTkLabel(self.main_frame, text="Cor do Texto:")
        text_color_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.text_color_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('text_color', self.text_color_button))
        self.text_color_button.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        my_bubble_label = ctk.CTkLabel(self.main_frame, text="Meu Balão:")
        my_bubble_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.my_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('my_bubble_color', self.my_bubble_button))
        self.my_bubble_button.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

        contact_bubble_label = ctk.CTkLabel(self.main_frame, text="Balão do Contacto:")
        contact_bubble_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.contact_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('contact_bubble_color', self.contact_bubble_button))
        self.contact_bubble_button.grid(row=8, column=1, padx=10, pady=5, sticky="ew")

    def setup_admin_widgets(self):
        """Cria os widgets para as funções de administrador."""
        self.admin_functions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.admin_functions_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        self.admin_functions_frame.grid_columnconfigure(0, weight=1)
        
        admin_button = ctk.CTkButton(self.admin_functions_frame, text="Funções de Administrador", command=self.ask_admin_password)
        admin_button.pack(fill="x")

        self.admin_buttons_container = ctk.CTkFrame(self.admin_functions_frame, fg_color="transparent")

        self.auto_export_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Exportação Automática de Conversas")
        self.auto_export_switch.pack(fill="x", pady=(10, 5), anchor="w")

        self.admin_export_button = ctk.CTkButton(self.admin_buttons_container, text="Exportar Histórico Completo Agora", command=self.app.export_full_history)
        self.admin_export_button.pack(fill="x", pady=(5, 0))

        self.change_password_button = ctk.CTkButton(self.admin_buttons_container, text="Alterar Senha de Administrador", command=self.change_admin_password)
        self.change_password_button.pack(fill="x", pady=(5, 0))

        self.startup_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Iniciar com Windows", command=self.toggle_startup_on_windows)
        self.startup_switch.pack(fill="x", pady=(10, 5), anchor="w")
        self.startup_switch.select() if self.is_app_in_startup() else self.startup_switch.deselect()

    def load_current_settings(self):
        """Carrega as configurações atuais nos widgets"""
        # Carregar username atual
        current_username = self.app.username if hasattr(self.app, 'username') else self.config.get("username", "")
        self.username_entry.insert(0, current_username)
        
        # Carregar outras configurações existentes
        if hasattr(self, 'font_family_menu'):
            self.font_family_menu.set(self.config.get("font_family", "System"))
        if hasattr(self, 'font_size_slider'):
            self.font_size_slider.set(self.config.get("font_size", 13))

    def pick_color(self, color_key, button):
        color = askcolor(title="Escolha uma cor")
        if color[1]:
            button.configure(text=color[1], fg_color=color[1])
            self.config[color_key] = color[1]

    def save_and_close(self):
        """Salva as configurações e fecha a janela"""
        # Salvar username
        new_username = self.username_entry.get().strip()
        if new_username:
            self.config["username"] = new_username
            self.app.username = new_username  # Atualizar na aplicação principal
            
            # Atualizar display do perfil na interface principal
            if hasattr(self.app, 'ui') and hasattr(self.app.ui, 'update_profile_display'):
                self.app.ui.update_profile_display(new_username)
        
        # Salvar outras configurações
        if hasattr(self, 'font_family_menu'):
            self.config["font_family"] = self.font_family_menu.get()
        if hasattr(self, 'font_size_slider'):
            self.config["font_size"] = int(self.font_size_slider.get())
        
        # Salvar configurações no arquivo
        self.app.save_config()
        
        self.destroy()

    def ask_admin_password(self):
        """Solicita a senha de administrador"""
        pass  # Implementação existente

    def change_admin_password(self):
        """Altera a senha de administrador"""
        pass  # Implementação existente

    def get_app_executable_path(self):
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return os.path.abspath(sys.argv[0])

    def is_app_in_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                value, reg_type = winreg.QueryValueEx(key, "LanMessenger")
                return value == self.get_app_executable_path()
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"Erro ao verificar inicialização: {e}")
            return False

    def toggle_startup_on_windows(self):
        """Toggle para iniciar com Windows"""
        pass  # Implementação existente
