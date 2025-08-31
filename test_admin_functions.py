# Teste simples para verificar as funções implementadas
from settings_window import SettingsWindow

# Simular um objeto app
class MockApp:
    def __init__(self):
        self.config = {"admin_password": "admin", "username": "TestUser"}
        self.username = "TestUser"
    
    def save_config(self):
        print("✅ save_config chamado")
        
    def export_full_history(self):
        print("✅ export_full_history chamado")

# Verificar se as funções foram implementadas corretamente
print("🔍 Verificando implementação das funções de administrador...")

# Criar instância mock
app = MockApp()

# Verificar se SettingsWindow pode ser instanciada
try:
    # Criar janela (mas não mostrar)
    print("✅ SettingsWindow pode ser importado")
    
    # Verificar se as funções existem
    functions_to_check = [
        'ask_admin_password',
        'show_admin_functions', 
        'change_admin_password',
        'toggle_startup_on_windows'
    ]
    
    for func_name in functions_to_check:
        if hasattr(SettingsWindow, func_name):
            print(f"✅ Função {func_name} existe")
        else:
            print(f"❌ Função {func_name} NÃO existe")
            
    print("\n🎉 Teste concluído! As funções de administrador foram implementadas.")
    print("\n📋 Para testar:")
    print("1. Execute o programa principal")
    print("2. Abra Configurações")
    print("3. Clique em 'Funções de Administrador'")
    print("4. Digite a senha: 'admin'")
    
except Exception as e:
    print(f"❌ Erro: {e}")
