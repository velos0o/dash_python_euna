import streamlit as st
import base64

def get_logo_base64():
    try:
        with open("logo.svg.svg", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

logo_base64 = get_logo_base64()
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon=f"data:image/svg+xml;base64,{logo_base64}" if logo_base64 else "🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

if logo_base64:
    st.sidebar.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem; padding: 1rem;">
            <img src="data:image/svg+xml;base64,{logo_base64}" width="180" height="180" style="margin-bottom: 0.5rem;">
        </div>
    """, unsafe_allow_html=True)

st.title("Eu na Europa - Sistema de Relatórios")
st.write("Versão de teste")
