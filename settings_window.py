import customtkinter as ctk
from tkinter.colorchooser import askcolor
import json
import winreg
import sys
import os

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.config = app.config

        self.title("Configurações")
        self.geometry("600x700")

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ScrollableFrame para opções
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        # --- Widgets de Configuração ---
        row = 0

        # Nome de Utilizador
        username_label = ctk.CTkLabel(self.scrollable_frame, text="Nome de Utilizador:")
        username_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.username_entry = ctk.CTkEntry(self.scrollable_frame)
        self.username_entry.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        # Opções de Fonte
        font_options = ["System", "Arial", "Calibri", "Times New Roman"]
        font_label = ctk.CTkLabel(self.scrollable_frame, text="Fonte:")
        font_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.font_family_menu = ctk.CTkOptionMenu(self.scrollable_frame, values=font_options)
        self.font_family_menu.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        font_size_label = ctk.CTkLabel(self.scrollable_frame, text="Tamanho da Fonte:")
        font_size_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.font_size_slider = ctk.CTkSlider(self.scrollable_frame, from_=10, to=20, number_of_steps=10)
        self.font_size_slider.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        bold_label = ctk.CTkLabel(self.scrollable_frame, text="Negrito:")
        bold_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.bold_switch = ctk.CTkSwitch(self.scrollable_frame, text="Ativar negrito")
        self.bold_switch.grid(row=row, column=1, padx=10, pady=8, sticky="w")
        row += 1

        # Personalização de Cores
        section_label = ctk.CTkLabel(self.scrollable_frame, text="Personalização de Cores", font=("", 15, "bold"))
        section_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 8))
        row += 1

        text_color_label = ctk.CTkLabel(self.scrollable_frame, text="Cor do Texto:")
        text_color_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.text_color_button = ctk.CTkButton(self.scrollable_frame, text="Padrão", command=lambda: self.pick_color('text_color', self.text_color_button))
        self.text_color_button.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        balloon_color_label = ctk.CTkLabel(self.scrollable_frame, text="Meu Balão:")
        balloon_color_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.balloon_color_button = ctk.CTkButton(self.scrollable_frame, text="Padrão", command=lambda: self.pick_color('balloon_color', self.balloon_color_button))
        self.balloon_color_button.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        contact_balloon_color_label = ctk.CTkLabel(self.scrollable_frame, text="Balão do Contacto:")
        contact_balloon_color_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.contact_balloon_color_button = ctk.CTkButton(self.scrollable_frame, text="Padrão", command=lambda: self.pick_color('contact_balloon_color', self.contact_balloon_color_button))
        self.contact_balloon_color_button.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        # Tema
        theme_label = ctk.CTkLabel(self.scrollable_frame, text="Tema", font=("", 15, "bold"))
        theme_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 8))
        row += 1

        appearance_label = ctk.CTkLabel(self.scrollable_frame, text="Aparência:")
        appearance_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.appearance_menu = ctk.CTkOptionMenu(self.scrollable_frame, values=["Light", "Dark", "System"])
        self.appearance_menu.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        accent_color_label = ctk.CTkLabel(self.scrollable_frame, text="Cor de Destaque:")
        accent_color_label.grid(row=row, column=0, sticky="w", padx=10, pady=8)
        self.accent_button = ctk.CTkButton(self.scrollable_frame, text="#3A7EBF", command=lambda: self.pick_color('accent_color', self.accent_button))
        self.accent_button.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1

        # Pasta de Recebidos
        downloads_label = ctk.CTkLabel(self.scrollable_frame, text="Pasta de Recebidos", font=("", 15, "bold"))
        downloads_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 8))
        row += 1

        self.downloads_entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text="Selecionar pasta...")
        self.downloads_entry.grid(row=row, column=0, padx=10, pady=8, sticky="ew")
        self.browse_downloads_btn = ctk.CTkButton(self.scrollable_frame, text="Procurar", command=self.choose_downloads_folder)
        self.browse_downloads_btn.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        row += 1
        
        # --- Funções de Administrador ---
        self.setup_admin_widgets()

        # --- Botões Finais ---
        self.bottom_frame = ctk.CTkFrame(self.main_frame)
        self.bottom_frame.pack(fill="x", side="bottom", pady=(10, 10), padx=20)

        self.save_button = ctk.CTkButton(self.bottom_frame, text="Salvar e Fechar", command=self.save_and_close)
        self.save_button.pack(side="right", padx=(10, 0))

        self.reset_button = ctk.CTkButton(self.bottom_frame, text="Restaurar Padrão", command=self.reset_to_default)
        self.reset_button.pack(side="right")

        self.load_current_settings()

    def select_downloads_folder(self):
        import tkinter.filedialog as fd
        folder = fd.askdirectory(title="Selecione a pasta de recebidos")
        if folder:
            self.downloads_entry.delete(0, "end")
            self.downloads_entry.insert(0, folder)

    def reset_to_default(self):
        default_config = {
            "font_family": "System", "font_size": 13, "font_bold": False,
            "text_color": "#FFFFFF", "balloon_color": "#3A7EBF", "contact_balloon_color": "#5CA9F7",
            "appearance_mode": "Light", "accent_color": "#3A7EBF", "downloads_path": ""
        }
        self.config.update(default_config)
        # Remover chaves alternativas de cor de balão para garantir reset
        for key in ["my_bubble_color", "contact_bubble_color"]:
            if key in self.config:
                del self.config[key]
        self.load_current_settings()

    def setup_admin_widgets(self):
        self.admin_functions_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.admin_functions_frame.grid(column=0, columnspan=2, pady=(20, 0), sticky="ew")
        
        admin_button = ctk.CTkButton(self.admin_functions_frame, text="Funções de Administrador", command=self.ask_admin_password)
        admin_button.pack(fill="x")

        self.admin_buttons_container = ctk.CTkFrame(self.admin_functions_frame, fg_color="transparent")
        self.admin_buttons_container.pack(fill="x", pady=(10,0))
        self.admin_buttons_container.pack_forget() # Começa escondido

        self.auto_export_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Exportação Automática de Conversas", command=self.on_auto_export_toggle)
        self.auto_export_switch.pack(fill="x", pady=(5, 5), anchor="w")

        self.admin_export_button = ctk.CTkButton(self.admin_buttons_container, text="Exportar Histórico Completo Agora", command=self.app.export_full_history)
        self.admin_export_button.pack(fill="x", pady=5)

        self.change_password_button = ctk.CTkButton(self.admin_buttons_container, text="Alterar Senha de Administrador", command=self.change_admin_password)
        self.change_password_button.pack(fill="x", pady=5)

        self.startup_switch = ctk.CTkSwitch(self.admin_buttons_container, text="Iniciar com Windows", command=self.toggle_startup_on_windows)
        self.startup_switch.pack(fill="x", pady=(5, 5), anchor="w")
        self.startup_switch.select() if self.is_app_in_startup() else self.startup_switch.deselect()

    def on_auto_export_toggle(self):
        if self.auto_export_switch.get():
            import tkinter.filedialog as fd
            folder = fd.askdirectory(title="Selecione a pasta para exportação automática")
            if folder:
                self.config["auto_export_folder"] = folder
            else:
                self.auto_export_switch.deselect()
        else:
            self.config["auto_export_folder"] = ""

    def load_current_settings(self):
        current_username = self.app.username if hasattr(self.app, 'username') else self.config.get("username", "")
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, current_username)
        
        self.font_family_menu.set(self.config.get("font_family", "System"))
        self.font_size_slider.set(self.config.get("font_size", 13))
        self.bold_switch.select() if self.config.get("font_bold", False) else self.bold_switch.deselect()
        
        self.appearance_menu.set(self.config.get("appearance_mode", "Light"))
        current_accent = self.config.get("accent_color", "#3A7EBF")
        self.accent_button.configure(text=current_accent, fg_color=current_accent)

        downloads_dir = self.config.get("downloads_folder", getattr(self.app, 'downloads_folder', ""))
        if downloads_dir:
            self.downloads_entry.delete(0, "end")
            self.downloads_entry.insert(0, downloads_dir)

    def pick_color(self, color_key, button):
        color = askcolor(title="Escolha uma cor")
        if color and color[1]:
            button.configure(text=color[1], fg_color=color[1])
            self.config[color_key] = color[1]

    def save_and_close(self):
        new_username = self.username_entry.get().strip()
        if new_username:
            self.config["username"] = new_username
            self.app.username = new_username
            if hasattr(self.app, 'ui') and hasattr(self.app.ui, 'update_profile_display'):
                self.app.ui.update_profile_display(new_username)
        
        self.config["font_family"] = self.font_family_menu.get()
        self.config["font_size"] = int(self.font_size_slider.get())
        self.config["font_bold"] = bool(self.bold_switch.get())
        self.config["appearance_mode"] = self.appearance_menu.get()
        self.config["accent_color"] = self.accent_button.cget("text")
        
        path = self.downloads_entry.get().strip()
        if path:
            self.config["downloads_folder"] = path
            self.app.downloads_folder = path
            self.app.ensure_downloads_folder_exists()
        
        try:
            ctk.set_appearance_mode(self.config["appearance_mode"])
            if hasattr(self.app, 'update_theme_all_windows'):
                self.app.update_theme_all_windows()
        except Exception as e:
            print(f"Error applying theme: {e}")

        self.app.save_config()
        
        if hasattr(self.app, 'ui') and hasattr(self.app.ui, 'settings_window_instance'):
            self.app.ui.settings_window_instance = None
        
        self.destroy()

    def ask_admin_password(self):
        dialog = ctk.CTkInputDialog(text="Digite a senha de administrador:", title="Acesso Restrito")
        password = dialog.get_input()
        
        correct_password = self.config.get("admin_password", "admin")
        
        if password == correct_password: 
            self.show_admin_functions()
        elif password is not None:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Erro de Acesso", message="Senha incorreta.", icon="cancel")

    def show_admin_functions(self):
        if self.admin_buttons_container.winfo_ismapped():
            self.admin_buttons_container.pack_forget()
        else:
            self.admin_buttons_container.pack(fill="x", padx=0, pady=0)

    def change_admin_password(self):
        new_pass_dialog = ctk.CTkInputDialog(text="Digite a nova senha:", title="Alterar Senha")
        new_password = new_pass_dialog.get_input()

        if not new_password: return

        confirm_dialog = ctk.CTkInputDialog(text="Confirme a nova senha:", title="Confirmar Senha")
        confirm_password = confirm_dialog.get_input()

        if new_password == confirm_password:
            self.config["admin_password"] = new_password
            self.app.save_config()
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Sucesso", message="Senha de administrador alterada com sucesso!", icon="check")
        else:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Erro", message="As senhas não coincidem. Tente novamente.", icon="cancel")

    def get_app_executable_path(self):
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    def is_app_in_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "LanMessenger")
            winreg.CloseKey(key)
            return str(value).strip('"') == self.get_app_executable_path()
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Erro ao verificar inicialização: {e}")
            return False

    def toggle_startup_on_windows(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if self.startup_switch.get():
                app_path = self.get_app_executable_path()
                winreg.SetValueEx(key, "LanMessenger", 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                winreg.DeleteValue(key, "LanMessenger")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Erro ao modificar startup: {e}")
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Erro", message=f"Erro ao modificar configuração de startup: {e}", icon="cancel")
            self.startup_switch.toggle()

    def choose_downloads_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Selecionar pasta de recebidos")
        if folder:
            self.downloads_entry.delete(0, "end")
            self.downloads_entry.insert(0, folder)