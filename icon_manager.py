import customtkinter as ctk
from app_icons import AppIcons # Lembre-se que o nome do ficheiro é app_icons.py e o da classe é AppIcons
import os
import sys

def get_base_path():
    """ Obtém o caminho base para o executável ou script para encontrar ficheiros de recursos. """
    if getattr(sys, 'frozen', False):
        # Se a aplicação for um executável (criado com PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Se estiver a executar como um script .py normal
        return os.path.dirname(os.path.abspath(__file__))

class IconManager:
    """
    Gere o carregamento e a aplicação de ícones a partir de uma fonte de ícones.
    Esta versão usa o método oficial do CustomTkinter para carregar a fonte.
    """
    def __init__(self):
        """
        Inicializa o IconManager.
        """
        font_path = os.path.join(get_base_path(), "icons.ttf")
        
        if os.path.exists(font_path):
            ctk.FontManager.load_font(font_path)
            print(f"Fonte carregada com sucesso via CustomTkinter: {font_path}")
        else:
            print(f"ERRO CRÍTICO: Ficheiro de fonte não encontrado em {font_path}")

        # --- CORREÇÃO FINAL AQUI ---
        # Usamos o nome exato que descobrimos com o script de diagnóstico.
        self.font_family_name = "Material Symbols Outlined" 
        self._font_cache = {}

    def get_icon(self, icon_name):
        """
        Obtém o caractere correspondente a um nome de ícone.
        """
        attr_name = icon_name.upper()
        return getattr(AppIcons, attr_name, "?") # Retorna '?' se o ícone não for encontrado

    def _get_font(self, size):
        """
        Obtém uma fonte da cache ou cria-a se não existir.
        """
        if size not in self._font_cache:
            self._font_cache[size] = ctk.CTkFont(family=self.font_family_name, size=size)
        return self._font_cache[size]

    def apply_icon(self, widget, icon_name, size=20, color=None):
        """
        Aplica um ícone a um widget do customtkinter.
        """
        icon_char = self.get_icon(icon_name)
        icon_font = self._get_font(size)

        widget.configure(font=icon_font, text=icon_char)

        if color:
            widget.configure(text_color=color)
