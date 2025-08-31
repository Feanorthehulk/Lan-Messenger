# check_font_name.py
from fontTools.ttLib import TTFont
import os

def get_font_family_name(font_path):
    """
    Inspeciona um ficheiro de fonte .ttf e extrai o seu nome de família.
    """
    try:
        font = TTFont(font_path)
        name_table = font['name']
        
        family_name = None
        
        # A tabela de nomes contém vários registos. O ID 1 é geralmente o nome da família.
        for record in name_table.names:
            if record.nameID == 1:
                # O nome pode estar em diferentes codificações, tentamos descodificar.
                if b'\x00' in record.string:
                    family_name = record.string.decode('utf-16-be').strip()
                else:
                    family_name = record.string.decode('latin-1').strip()
                
                print(f"Encontrado registo de nome (ID {record.nameID}): '{family_name}'")
                # Damos preferência ao primeiro nome de família encontrado.
                break # Paramos assim que encontramos o primeiro
        
        if family_name:
            return family_name
        else:
            return "Nome da família não encontrado na tabela de nomes."

    except Exception as e:
        return f"Ocorreu um erro ao ler o ficheiro da fonte: {e}"

if __name__ == "__main__":
    font_file = "icons.ttf"
    if os.path.exists(font_file):
        print(f"A inspecionar o ficheiro '{font_file}'...")
        result = get_font_family_name(font_file)
        print("-" * 30)
        print(f"O nome da família da fonte é: '{result}'")
        print("-" * 30)
        print("Por favor, copie este nome e use-o no ficheiro 'icon_manager.py'.")
    else:
        print(f"ERRO: O ficheiro '{font_file}' não foi encontrado nesta pasta.")
        print("Por favor, coloque este script na mesma pasta que o seu ficheiro 'icons.ttf'.")
