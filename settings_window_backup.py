import customtkinter as ctk
from tkinter.colorchooser import askcolor
import json

class SettingsWindow(ctk.CTkToplevel):
    """
    Janela para as configurações da aplicação, com mais opções e segurança.
    """
    def __init__(self, master_app):
        super().__init__(master_app)
        self.app = master_app
        self.config = master_app.config

        self.title("Configurações")
        self.geometry("450x650") # Aumentei a altura novamente
        self.resizable(False, False)
        self.transient(master_app)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=15, pady=15)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.admin_export_button = None
        self.admin_functions_frame = None
        
        self.setup_ui_widgets()
        self.setup_admin_widgets()
        
        save_button = ctk.CTkButton(self.main_frame, text="Salvar e Fechar", command=self.save_and_close)
        save_button.grid(row=8, column=0, columnspan=2, pady=(30, 0), sticky="ew")

    def setup_ui_widgets(self):
        """Cria os widgets de personalização da UI, incluindo a escolha de fonte."""
        
        ui_options_label = ctk.CTkLabel(self.main_frame, text="Opções da Interface", font=ctk.CTkFont(size=16, weight="bold"))
        ui_options_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        font_family_label = ctk.CTkLabel(self.main_frame, text="Fonte:")
        font_family_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        font_options = ["System", "Arial", "Calibri", "Times New Roman"]
        self.font_family_menu = ctk.CTkOptionMenu(self.main_frame, values=font_options)
        self.font_family_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        font_size_label = ctk.CTkLabel(self.main_frame, text="Tamanho da Fonte:")
        font_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.font_size_slider = ctk.CTkSlider(self.main_frame, from_=10, to=20, number_of_steps=10)
        self.font_size_slider.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        colors_label = ctk.CTkLabel(self.main_frame, text="Personalização de Cores", font=ctk.CTkFont(size=16, weight="bold"))
        colors_label.grid(row=3, column=0, columnspan=2, pady=(20, 15), sticky="w")

        text_color_label = ctk.CTkLabel(self.main_frame, text="Cor do Texto:")
        text_color_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.text_color_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('text_color', self.text_color_button))
        self.text_color_button.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        my_bubble_label = ctk.CTkLabel(self.main_frame, text="Meu Balão:")
        my_bubble_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.my_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('my_bubble_color', self.my_bubble_button))
        self.my_bubble_button.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        contact_bubble_label = ctk.CTkLabel(self.main_frame, text="Balão do Contacto:")
        contact_bubble_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.contact_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('contact_bubble_color', self.contact_bubble_button))
        self.contact_bubble_button.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

    def setup_admin_widgets(self):
        """Cria os widgets para as funções de administrador."""
        self.admin_functions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.admin_functions_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        self.admin_functions_frame.grid_columnconfigure(0, weight=1)
        
        admin_button = ctk.CTkButton(self.admin_functions_frame, text="Funções de Administrador", command=self.ask_admin_password)
        admin_button.pack(fill="x")

        self.admin_buttons_container = ctk.CTkFrame(self.admin_functions_frame, fg_color="transparent")

        self.auto_export_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Exportação Automática de Conversas")
        self.auto_export_switch.pack(fill="x", pady=(10, 5), anchor="w")

        self.admin_export_button = ctk.CTkButton(self.admin_buttons_container, text="Exportar Histórico Completo Agora", command=self.app.export_full_history)
        self.admin_export_button.pack(fill="x", pady=(5, 0))

        # --- NOVO BOTÃO ADICIONADO AQUI ---
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
        self.geometry("450x650") # Aumentei a altura novamente
        self.resizable(False, False)
        self.transient(master_app)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=15, pady=15)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.admin_export_button = None
        self.admin_functions_frame = None
        
        self.setup_ui_widgets()
        self.setup_admin_widgets()
        
        save_button = ctk.CTkButton(self.main_frame, text="Salvar e Fechar", command=self.save_and_close)
        save_button.grid(row=8, column=0, columnspan=2, pady=(30, 0), sticky="ew")

    def setup_ui_widgets(self):
        """Cria os widgets de personalização da UI, incluindo a escolha de fonte."""
        
        ui_options_label = ctk.CTkLabel(self.main_frame, text="Opções da Interface", font=ctk.CTkFont(size=16, weight="bold"))
        ui_options_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        font_family_label = ctk.CTkLabel(self.main_frame, text="Fonte:")
        font_family_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        font_options = ["System", "Arial", "Calibri", "Times New Roman"]
        self.font_family_menu = ctk.CTkOptionMenu(self.main_frame, values=font_options)
        self.font_family_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        font_size_label = ctk.CTkLabel(self.main_frame, text="Tamanho da Fonte:")
        font_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.font_size_slider = ctk.CTkSlider(self.main_frame, from_=10, to=20, number_of_steps=10)
        self.font_size_slider.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        colors_label = ctk.CTkLabel(self.main_frame, text="Personalização de Cores", font=ctk.CTkFont(size=16, weight="bold"))
        colors_label.grid(row=3, column=0, columnspan=2, pady=(20, 15), sticky="w")

        text_color_label = ctk.CTkLabel(self.main_frame, text="Cor do Texto:")
        text_color_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.text_color_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('text_color', self.text_color_button))
        self.text_color_button.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        my_bubble_label = ctk.CTkLabel(self.main_frame, text="Meu Balão:")
        my_bubble_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.my_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('my_bubble_color', self.my_bubble_button))
        self.my_bubble_button.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        contact_bubble_label = ctk.CTkLabel(self.main_frame, text="Balão do Contacto:")
        contact_bubble_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.contact_bubble_button = ctk.CTkButton(self.main_frame, text="Padrão", command=lambda: self.pick_color('contact_bubble_color', self.contact_bubble_button))
        self.contact_bubble_button.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

    def setup_admin_widgets(self):
        """Cria os widgets para as funções de administrador."""
        self.admin_functions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.admin_functions_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        self.admin_functions_frame.grid_columnconfigure(0, weight=1)
        
        admin_button = ctk.CTkButton(self.admin_functions_frame, text="Funções de Administrador", command=self.ask_admin_password)
        admin_button.pack(fill="x")

        self.admin_buttons_container = ctk.CTkFrame(self.admin_functions_frame, fg_color="transparent")

        self.auto_export_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Exportação Automática de Conversas")
        self.auto_export_switch.pack(fill="x", pady=(10, 5), anchor="w")

        self.admin_export_button = ctk.CTkButton(self.admin_buttons_container, text="Exportar Histórico Completo Agora", command=self.app.export_full_history)
        self.admin_export_button.pack(fill="x", pady=(5, 0))

        # --- NOVO BOTÃO ADICIONADO AQUI ---
        self.change_password_button = ctk.CTkButton(self.admin_buttons_container, text="Alterar Senha de Administrador", command=self.change_admin_password)
        self.change_password_button.pack(fill="x", pady=(5, 0))

        # --- NOVO: Iniciar com Windows ---
        self.startup_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Iniciar com Windows", command=self.toggle_startup_on_windows)
        self.startup_switch.pack(fill="x", pady=(10, 5), anchor="w")
        self.startup_switch.select() if self.is_app_in_startup() else self.startup_switch.deselect()

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
        app_name = "LanMessenger"
        app_path = self.get_app_executable_path()
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if self.startup_switch.get() == 1: # Switch is ON, add to startup
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                self.app.ui.show_error("Sucesso", "Lan Messenger será iniciado com o Windows.")
            else: # Switch is OFF, remove from startup
                try:
                    winreg.DeleteValue(key, app_name)
                    self.app.ui.show_error("Sucesso", "Lan Messenger não será mais iniciado com o Windows.")
                except FileNotFoundError:
                    # Value not found, already removed or never added
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.app.ui.show_error("Erro", f"Não foi possível alterar a configuração de inicialização: {e}")
            # Revert switch state if error occurs
            if self.startup_switch.get() == 1:
                self.startup_switch.deselect()
            else:
                self.startup_switch.select()

    def ask_admin_password(self):
        """Pede a senha de administrador antes de mostrar as opções."""
        dialog = ctk.CTkInputDialog(text="Digite a senha de administrador:", title="Acesso Restrito")
        password = dialog.get_input()
        
        # Lê a senha do ficheiro de configuração, com "admin" como padrão
        correct_password = self.config.get("admin_password", "admin")
        
        if password == correct_password: 
            self.show_admin_functions()
        elif password is not None:
            self.app.ui.show_error("Erro de Acesso", "Senha incorreta.")

    def show_admin_functions(self):
        """Mostra ou esconde as funções de administrador."""
        if self.admin_buttons_container.winfo_ismapped():
            self.admin_buttons_container.pack_forget()
        else:
            self.admin_buttons_container.pack(fill="x", padx=20, pady=10)

    def change_admin_password(self):
        """Abre diálogos para alterar a senha de administrador."""
        new_pass_dialog = ctk.CTkInputDialog(text="Digite a nova senha:", title="Alterar Senha")
        new_password = new_pass_dialog.get_input()

        if not new_password: # Se o utilizador cancelar
            return

        confirm_pass_dialog = ctk.CTkInputDialog(text="Confirme a nova senha:", title="Confirmar Senha")
        confirm_password = confirm_pass_dialog.get_input()

        if new_password == confirm_password:
            # Atualiza a senha no objeto de configuração
            self.config["admin_password"] = new_password
            # Salva imediatamente no ficheiro
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            self.app.ui.show_error("Sucesso", "Senha alterada com sucesso!") # Usando show_error para mostrar info
        else:
            self.app.ui.show_error("Erro", "As senhas não coincidem.")

    def pick_color(self, config_key, button_to_update):
        """Abre o seletor de cores e atualiza o botão correspondente."""
        color_code = askcolor(title="Escolha uma cor")[1] 
        if color_code:
            self.config[config_key] = color_code
            button_to_update.configure(fg_color=color_code, text=color_code)

    def save_and_close(self):
        """Salva as configurações no ficheiro JSON e fecha a janela."""
        # TODO: Adicionar a lógica para pegar os valores (fonte, slider, switch)
        
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)
        print("Configurações salvas.")
        self.destroy()

    def ask_admin_password(self):
        """Pede a senha de administrador antes de mostrar as opções."""
        dialog = ctk.CTkInputDialog(text="Digite a senha de administrador:", title="Acesso Restrito")
        password = dialog.get_input()
        
        # Lê a senha do ficheiro de configuração, com "admin" como padrão
        correct_password = self.config.get("admin_password", "admin")
        
        if password == correct_password: 
            self.show_admin_functions()
        elif password is not None:
            self.app.ui.show_error("Erro de Acesso", "Senha incorreta.")

    def show_admin_functions(self):
        """Mostra ou esconde as funções de administrador."""
        if self.admin_buttons_container.winfo_ismapped():
            self.admin_buttons_container.pack_forget()
        else:
            self.admin_buttons_container.pack(fill="x", padx=20, pady=10)

    def change_admin_password(self):
        """Abre diálogos para alterar a senha de administrador."""
        new_pass_dialog = ctk.CTkInputDialog(text="Digite a nova senha:", title="Alterar Senha")
        new_password = new_pass_dialog.get_input()

        if not new_password: # Se o utilizador cancelar
            return

        confirm_pass_dialog = ctk.CTkInputDialog(text="Confirme a nova senha:", title="Confirmar Senha")
        confirm_password = confirm_pass_dialog.get_input()

        if new_password == confirm_password:
            # Atualiza a senha no objeto de configuração
            self.config["admin_password"] = new_password
            # Salva imediatamente no ficheiro
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            self.app.ui.show_error("Sucesso", "Senha alterada com sucesso!") # Usando show_error para mostrar info
        else:
            self.app.ui.show_error("Erro", "As senhas não coincidem.")

    def pick_color(self, config_key, button_to_update):
        """Abre o seletor de cores e atualiza o botão correspondente."""
        color_code = askcolor(title="Escolha uma cor")[1] 
        if color_code:
            self.config[config_key] = color_code
            button_to_update.configure(fg_color=color_code, text=color_code)

    def save_and_close(self):
        """Salva as configurações no ficheiro JSON e fecha a janela."""
        # TODO: Adicionar a lógica para pegar os valores (fonte, slider, switch)
        
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)
        print("Configurações salvas.")
        self.destroy()

