import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from mysql.connector import Error
import requests
import json
import time
import io
import base64
from datetime import datetime, timedelta

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

# Importar e executar o aplicativo principal
from app_completo import main
main()