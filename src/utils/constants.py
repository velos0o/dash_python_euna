"""Constantes utilizadas no projeto"""

# Descrições das opções de pagamento
PAYMENT_OPTIONS = {
    'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
    'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
    'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
    'D': 'Parcelamento em até 24 vezes fixas',
    'E': 'Cancelar',
    'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
    'Z': 'Análise especial'
}

# Cores para cada opção
PAYMENT_OPTIONS_COLORS = {
    'A': '#4CAF50',  # Verde
    'B': '#2196F3',  # Azul
    'C': '#9C27B0',  # Roxo
    'D': '#FF9800',  # Laranja
    'E': '#F44336',  # Vermelho
    'F': '#795548',  # Marrom
    'Z': '#607D8B'   # Cinza azulado
}

# Configurações do banco de dados
DATABASE_CONFIG = {
    'host': 'database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com',
    'port': 3306,
    'database': 'whatsapp_euna_data',
    'user': 'lucas',
    'password': 'a9!o98Q80$MM'
}

# Configurações do Bitrix24
BITRIX_CONFIG = {
    'base_url': 'https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php',
    'token': '0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br',
    'timeout': 30,
    'max_retries': 3
}

# Cache TTL em segundos
CACHE_TTL = 300  # 5 minutos