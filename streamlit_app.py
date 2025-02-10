"""
Ponto de entrada para o Streamlit Cloud
"""
import streamlit as st
import base64
import os

# Configurar o ambiente
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# Carregar o logo para usar como ícone
def get_logo_base64():
    try:
        with open("logo.svg.svg", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

# Configurações básicas do Streamlit
logo_base64 = get_logo_base64()
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon=f"data:image/svg+xml;base64,{logo_base64}" if logo_base64 else "🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
        /* Estilo geral */
        .main {
            background-color: #ffffff;
            font-family: 'Montserrat', sans-serif;
            color: #333333;
        }
        
        /* Cores da Eu na Europa */
        :root {
            --primary-color: #003399;  /* Azul principal */
            --secondary-color: #FFD700;  /* Dourado */
            --text-color: #333333;
            --background-color: #ffffff;
            --accent-color: #1a73e8;
        }
        
        /* Cards de métricas */
        .metric-card {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .metric-label {
            font-size: 1rem;
            color: var(--text-color);
            margin-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Logo no sidebar
if logo_base64:
    st.sidebar.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem; padding: 1rem;">
            <img src="data:image/svg+xml;base64,{logo_base64}" width="180" height="180" style="margin-bottom: 0.5rem;">
        </div>
    """, unsafe_allow_html=True)

# Sidebar de navegação
st.sidebar.markdown("""
    <div class="sidebar-title">
        Navegação
    </div>
""", unsafe_allow_html=True)

tipo_relatorio = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise Funil Bitrix24"]
)

# Importar e executar o aplicativo principal
from app_completo import show_status_familias

# Lógica de navegação
if tipo_relatorio == "Status das Famílias":
    show_status_familias()
elif tipo_relatorio == "Análise Funil Bitrix24":
    st.info("Módulo em desenvolvimento")
else:
    st.info("👈 Selecione um relatório no menu lateral para começar")
