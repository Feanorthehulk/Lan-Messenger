# --- Animações nativas Tkinter ---
import tkinter as tk

def fade_in(window, duration=300):
    steps = 20
    delay = duration // steps
    def _fade(step=0):
        alpha = step / steps
        window.wm_attributes('-alpha', alpha)
        if step < steps:
            window.after(delay, _fade, step+1)
        else:
            window.wm_attributes('-alpha', 1.0)
    window.wm_attributes('-alpha', 0.0)
    _fade()

def fade_out(window, duration=300, on_end=None):
    steps = 20
    delay = duration // steps
    def _fade(step=steps):
        alpha = step / steps
        window.wm_attributes('-alpha', alpha)
        if step > 0:
            window.after(delay, _fade, step-1)
        else:
            window.wm_attributes('-alpha', 0.0)
            if on_end:
                on_end()
    _fade()

def slide_in(widget, from_x=-300, to_x=0, duration=300):
    steps = 20
    delay = duration // steps
    delta = (to_x - from_x) / steps
    def _slide(step=0):
        x = from_x + delta * step
        widget.place(x=int(x))
        if step < steps:
            widget.after(delay, _slide, step+1)
        else:
            widget.place(x=to_x)
    widget.place(x=from_x)
    _slide()

def expand(widget, from_h=0, to_h=200, duration=300):
    steps = 20
    delay = duration // steps
    delta = (to_h - from_h) / steps
    def _expand(step=0):
        h = from_h + delta * step
        widget.configure(height=int(h))
        if step < steps:
            widget.after(delay, _expand, step+1)
        else:
            widget.configure(height=to_h)
    widget.configure(height=from_h)
    _expand()

# --- Exemplos de uso ---
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    btn_fade = tk.Button(root, text="Fade In", command=lambda: fade_in(root))
    btn_fade.pack(pady=10)
    btn_fade_out = tk.Button(root, text="Fade Out", command=lambda: fade_out(root))
    btn_fade_out.pack(pady=10)
    frame = tk.Frame(root, bg="blue", width=200, height=100)
    btn_slide = tk.Button(root, text="Slide In", command=lambda: slide_in(frame, from_x=-200, to_x=100))
    btn_slide.pack(pady=10)
    btn_expand = tk.Button(root, text="Expandir", command=lambda: expand(frame, from_h=0, to_h=100))
    btn_expand.pack(pady=10)
    frame.place(x=-200, y=200)
    root.mainloop()
import customtkinter as ctk
from icon_manager import IconManager
from CTkMessagebox import CTkMessagebox
from chat_window import ChatWindow
from broadcast_chat_window import BroadcastChatWindow

# As janelas secundárias serão importadas dentro das funções para evitar erros

class UIManager:
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.main_window = app
        self.icon_manager = IconManager()
        self.username_label = None
        self.user_list_frame = None
        self.user_widgets = {}
        self.chat_windows = {}
        self.settings_window_instance = None
        self.broadcast_chat_window_instance = None
        self.transfers_window_instance = None
        self.status_button = None
        self.create_widgets()

    def create_widgets(self):
        try:
            print("[Debug] Criando widgets principais...")
            self.main_window.title("Lan Messenger")
            self.main_window.geometry("350x550")
            self.main_window.grid_columnconfigure(0, weight=1)
            self.main_window.grid_rowconfigure(1, weight=1)
            self.create_header_frame()
            self.create_user_list_frame()
            self.create_status_bar()
            print("[Debug] Widgets principais criados com sucesso.")
        except Exception as e:
            print(f"[Debug][ERRO] Falha ao criar widgets principais: {e}")
            import traceback
            traceback.print_exc()

    def create_header_frame(self):
        try:
            print("[Debug] Criando header_frame...")
            header_frame = ctk.CTkFrame(self.main_window, height=50, corner_radius=0)
            header_frame.grid(row=0, column=0, sticky="ew")
            header_frame.grid_columnconfigure(1, weight=1)

            profile_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            profile_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

            self.status_button = ctk.CTkButton(profile_frame, text="", width=28, height=28, command=self.app.cycle_status)
            self.status_button.pack(side="left")
            self.update_status_display(self.app.status)

            self.username_label = ctk.CTkLabel(profile_frame, text=self.config.get("username", "User"), font=ctk.CTkFont(size=14, weight="bold"))
            self.username_label.pack(side="left", padx=5)

            actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            btn_transfers = ctk.CTkButton(actions_frame, text="", width=28, height=28, command=self.open_transfers_window)
            btn_transfers.pack(side="left", padx=2)
            self.icon_manager.apply_icon(btn_transfers, "transfers")
            
            btn_broadcast = ctk.CTkButton(actions_frame, text="", width=28, height=28, command=self.open_broadcast_chat_window)
            btn_broadcast.pack(side="left", padx=2)
            self.icon_manager.apply_icon(btn_broadcast, "broadcast")

            btn_settings = ctk.CTkButton(actions_frame, text="", width=28, height=28, command=self.open_settings_window)
            btn_settings.pack(side="left", padx=2)
            self.icon_manager.apply_icon(btn_settings, "settings")
            print("[Debug] Header_frame criado com sucesso.")
        except Exception as e:
            print(f"[Debug][ERRO] Falha ao criar header_frame: {e}")
            import traceback
            traceback.print_exc()

    def update_status_display(self, new_status):
        if not self.status_button: return
        if new_status == "online": color, icon_name = "#2E7D32", "status_online"
        elif new_status == "away": color, icon_name = "#C62828", "status_away"
        elif new_status == "dnd": color, icon_name = "#FF8F00", "status_dnd"
        else: color, icon_name = "gray", "status_offline"
        self.icon_manager.apply_icon(self.status_button, icon_name, size=20)
        self.status_button.configure(fg_color=color, hover_color=color)

    def open_settings_window(self):
        from settings_window import SettingsWindow
        # Verificar se a janela existe e está ativa
        if (hasattr(self, 'settings_window_instance') and 
            self.settings_window_instance is not None and 
            self.settings_window_instance.winfo_exists()):
            # Se a janela já existe, apenas focar nela
            self.settings_window_instance.focus()
            self.settings_window_instance.lift()
        else:
            # Criar nova instância da janela
            try:
                self.settings_window_instance = SettingsWindow(self.app)
                self.settings_window_instance.grab_set()
                print(f"[Debug] Janela de configurações criada com sucesso")
            except Exception as e:
                print(f"[Debug] Erro ao criar janela de configurações: {e}")
                # Limpar a instância em caso de erro
                self.settings_window_instance = None

    def open_broadcast_chat_window(self):
        if self.broadcast_chat_window_instance is None or not self.broadcast_chat_window_instance.winfo_exists():
            self.broadcast_chat_window_instance = BroadcastChatWindow(self.app)
        else:
            self.broadcast_chat_window_instance.focus()

    def open_transfers_window(self):
        from transfers_window import TransfersWindow
        if self.transfers_window_instance is None or not self.transfers_window_instance.winfo_exists():
            self.transfers_window_instance = TransfersWindow(self.app)
        else:
            self.transfers_window_instance.focus()

    def create_user_list_frame(self):
        self.user_list_frame = ctk.CTkScrollableFrame(self.main_window, corner_radius=0, fg_color="transparent")
        self.user_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def add_user_to_list(self, user_id, user_info):
        if user_id in self.user_widgets: return
        username = user_info.get('username', 'Unknown')
        status = user_info.get('status', 'online')
        user_entry = ctk.CTkFrame(self.user_list_frame, fg_color="transparent", height=30, cursor="hand2")
        user_entry.pack(fill="x", pady=2, padx=5)
        user_icon = ctk.CTkLabel(user_entry, text="")
        user_icon.pack(side="left")
        
        # Determine color based on status
        if status == "online": color = "#2E7D32"
        elif status == "away": color = "#C62828"
        elif status == "dnd": color = "#FF8F00"
        else: color = "gray"
        
        self.icon_manager.apply_icon(user_icon, f"status_{status}", size=18, color=color)
        user_name_label = ctk.CTkLabel(user_entry, text=username, anchor="w")
        user_name_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # A função lambda é essencial para passar os argumentos corretos no momento do clique
        user_entry.bind("<Double-Button-1>", lambda event, uid=user_id, uinfo=user_info: self.open_chat_window(uid, uinfo))
        user_name_label.bind("<Double-Button-1>", lambda event, uid=user_id, uinfo=user_info: self.open_chat_window(uid, uinfo))
        user_icon.bind("<Double-Button-1>", lambda event, uid=user_id, uinfo=user_info: self.open_chat_window(uid, uinfo))
        
        self.user_widgets[user_id] = {'frame': user_entry, 'icon': user_icon}

    def update_user_status_in_list(self, user_id, new_status):
        if user_id in self.user_widgets:
            user_icon_widget = self.user_widgets[user_id]['icon']
            # Determine color based on new_status
            if new_status == "online": color = "#2E7D32"
            elif new_status == "away": color = "#C62828"
            elif new_status == "dnd": color = "#FF8F00"
            else: color = "gray"
            self.icon_manager.apply_icon(user_icon_widget, f"status_{new_status}", size=18, color=color)

    def open_chat_window(self, user_id, user_info):
        if user_id in self.chat_windows and self.chat_windows[user_id].winfo_exists():
            window = self.chat_windows[user_id]
            window.deiconify()
            window.lift()
            # Garantir frontmost mesmo com outras janelas ativas
            try:
                window.attributes("-topmost", True)
                window.after(150, lambda: window.attributes("-topmost", False))
            except Exception:
                pass
            window.after(10, window.focus_force)
            return window
        chat_win = ChatWindow(master_app=self.app, target_info=user_info)
        self.chat_windows[user_id] = chat_win
        try:
            chat_win.attributes("-topmost", True)
            chat_win.after(150, lambda: chat_win.attributes("-topmost", False))
        except Exception:
            pass
        return chat_win

    def get_chat_window(self, user_id):
        return self.chat_windows.get(user_id)

    def get_or_open_chat_window(self, user_id, user_info):
        if user_id in self.chat_windows and self.chat_windows[user_id].winfo_exists():
            window = self.chat_windows[user_id]
            window.deiconify()
            window.lift()
            try:
                window.attributes("-topmost", True)
                window.after(150, lambda: window.attributes("-topmost", False))
            except Exception:
                pass
            window.after(10, window.focus_force)
            return window
        else:
            window = ChatWindow(master_app=self.app, target_info=user_info)  # Corrija os parâmetros
            self.chat_windows[user_id] = window
            try:
                window.attributes("-topmost", True)
                window.after(150, lambda: window.attributes("-topmost", False))
            except Exception:
                pass
            return window

    def remove_user_from_list(self, user_id):
        if user_id in self.user_widgets:
            self.user_widgets.pop(user_id)['frame'].destroy()
        if user_id in self.chat_windows:
            self.chat_windows.pop(user_id).destroy()

    def create_status_bar(self):
        status_bar = ctk.CTkFrame(self.main_window, height=25, corner_radius=0)
        status_bar.grid(row=2, column=0, sticky="ew")
        status_label = ctk.CTkLabel(status_bar, text="Pronto", font=ctk.CTkFont(size=10))
        status_label.pack(side="left", padx=10)

    def update_profile_display(self, new_username):
        if self.username_label:
            self.username_label.configure(text=new_username)

    def show_error(self, title, message):
        CTkMessagebox(title=title, message=message, icon="cancel")
