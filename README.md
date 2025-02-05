# Dashboard Euna

Dashboard interativo para análise de dados das famílias Euna.

## Funcionalidades

### 1. Funil de Famílias
- Análise do funil de conversão
- Métricas de categoria 32
- Status de preenchimento de ID de família
- Distribuição por etapas

### 2. Status das Famílias
- Métricas de continuidade
- Análise de cancelamentos
- Distribuição por família
- Detalhamento por membros

## Tecnologias Utilizadas
- Streamlit
- Plotly
- Pandas
- MySQL
- Bitrix24 API

## Como Executar Localmente

1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/dash_python_euna.git
cd dash_python_euna
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Execute o aplicativo
```bash
streamlit run app_completo.py
```

## Dados e Atualizações
- Os dados são atualizados em tempo real via API do Bitrix24
- Conexão com banco MySQL para dados complementares
- Visualizações interativas e responsivas