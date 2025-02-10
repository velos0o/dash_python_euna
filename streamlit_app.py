"""
Arquivo de entrada para o Streamlit Cloud
"""
import streamlit as st
import os

# Configurar o ambiente
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

# Importar e executar o aplicativo principal
import app_completo
app_completo.main()