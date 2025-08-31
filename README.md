# Lan Messenger

Lan Messenger é um aplicativo de mensagens instantâneas para redes locais (LAN), desenvolvido em Python com interface moderna baseada em CustomTkinter.

## Funcionalidades
- Chat privado e broadcast em rede local
- Transferência de arquivos
- Histórico de mensagens com banco de dados SQLite
- Suporte a emojis personalizados
- Ícones modernos via fonte customizada
- Notificações e integração com o Windows
- Instalação fácil via instalador Inno Setup

## Requisitos
- Python 3.10+
- Windows 10/11
- Pacotes Python:
  - customtkinter
  - CTkMessagebox
  - (outros: ver `requirements.txt` se disponível)

## Como rodar no modo desenvolvimento
1. Clone o repositório
2. Crie e ative um ambiente virtual:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   Instale as dependências:

pip install customtkinter CTkMessagebox
Execute o programa:

python main.py
Como gerar o executável
Instale o PyInstaller:

pip install pyinstaller
Gere o executável:

pyinstaller --onefile --windowed --icon=icon.ico main.py --add-data "icons.ttf;." --add-data "config.json;." --add-data "emojis;emojis" --add-data "app_icons.py;." --add-data "icon_font_mapping.py;." --add-data "icon_manager.py;." --add-data "messenger_history.db;."
O executável estará na pasta dist/
Como gerar o instalador
Instale o Inno Setup (https://jrsoftware.org/isinfo.php)
Compile o script lanmessenger.iss:

& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" lanmessenger.iss
O instalador será gerado na pasta do projeto
Licença
Consulte os arquivos License free.txt e License premium.txt para informações de licenciamento.

Desenvolvido por Feanorthehulk
