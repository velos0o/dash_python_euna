@@ -1,17 +1,15 @@
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import mysql.connector
from datetime import datetime, timedelta
import requests

# Cores personalizadas
# Cores
COLORS = {
    'verde': '#008C45',  # Verde da bandeira italiana
    'branco': '#FFFFFF', # Branco da bandeira italiana
    'vermelho': '#CD212A', # Vermelho da bandeira italiana
    'azul': '#003399'    # Azul da bandeira da UE
    'verde': '#008C45',
    'branco': '#FFFFFF',
    'vermelho': '#CD212A',
    'azul': '#003399'
}

# Configuração da página
@@ -21,62 +19,18 @@
    layout="wide"
)

# Estilo CSS personalizado
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {COLORS['branco']};
    }}
    .stMetric {{
        background-color: {COLORS['branco']};
        border: 1px solid {COLORS['azul']};
        border-radius: 5px;
        padding: 10px;
    }}
    .stMetric:hover {{
        border-color: {COLORS['verde']};
    }}
    .stTitle {{
        color: {COLORS['azul']};
    }}
    </style>
    """,
    unsafe_allow_html=True
)
# Cabeçalho
st.markdown(
    f"""
    <h1 style='color: {COLORS['azul']}'>
        Sistema de Relatórios - Eu na Europa
    </h1>
    <p style='color: {COLORS['azul']}; font-size: 1.2em;'>
        Análise de Famílias e Requerentes
    </p>
    """,
    unsafe_allow_html=True
)
# Configurações do Bitrix24 (usando secrets)
BITRIX_BASE_URL = st.secrets["bitrix24_base_url"]
BITRIX_TOKEN = st.secrets["bitrix24_token"]
# Funções
def consultar_bitrix(table, filtros=None):
    """Função para consultar a API do Bitrix24"""
    url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"
    
    url = f"{st.secrets['bitrix24_base_url']}?token={st.secrets['bitrix24_token']}&table={table}"
    if filtros:
        response = requests.post(url, json=filtros)
    else:
        response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    return None

def get_mysql_data():
    """Busca dados do MySQL"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql_host"],
@@ -85,7 +39,6 @@ def get_mysql_data():
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"]
        )
        
        query = """
        SELECT 
            idfamilia,
@@ -98,7 +51,6 @@ def get_mysql_data():
          AND hasTechnicalProblems = 0
        GROUP BY idfamilia
        """
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
@@ -108,160 +60,73 @@ def get_mysql_data():
        if 'conn' in locals():
            conn.close()

# Sidebar para seleção de relatórios
relatorio_selecionado = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Status das Famílias", "Funil de Famílias"]
)
# Título
st.title("Status das Famílias")
# Carregar dados
df_mysql = get_mysql_data()

if relatorio_selecionado == "Status das Famílias":
    st.markdown(f"<h2 style='color: {COLORS['azul']}'>Status das Famílias</h2>", unsafe_allow_html=True)
if df_mysql is not None:
    # Buscar dados do Bitrix24
    filtros_deal = {
        "dimensionsFilters": [[{
            "fieldName": "CATEGORY_ID",
            "values": [32],
            "type": "INCLUDE",
            "operator": "EQUALS"
        }]]
    }

    # Carregar dados do MySQL
    df_mysql = get_mysql_data()
    deals_data = consultar_bitrix("crm_deal", filtros_deal)
    deals_uf = consultar_bitrix("crm_deal_uf")

    if df_mysql is not None:
        # Buscar nomes das famílias no Bitrix24
        filtros_deal = {
            "dimensionsFilters": [[
                {
                    "fieldName": "CATEGORY_ID",
                    "values": [32],
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }
            ]]
        }
    if deals_data and deals_uf:
        # Preparar dados do Bitrix24
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
        
        # Juntar dados
        df_bitrix = pd.merge(
            deals_df[['ID', 'TITLE']],
            deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
            left_on='ID',
            right_on='DEAL_ID',
            how='left'
        )
        
        # Relatório final
        df_report = pd.merge(
            df_mysql,
            df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
            left_on='idfamilia',
            right_on='UF_CRM_1722605592778',
            how='left'
        )
        
        # Usar idfamilia quando não tiver TITLE
        df_report['TITLE'] = df_report['TITLE'].fillna(df_report['idfamilia'])

        deals_data = consultar_bitrix("crm_deal", filtros_deal)
        deals_uf = consultar_bitrix("crm_deal_uf")
        # Métricas
        col1, col2, col3 = st.columns(3)

        if deals_data and deals_uf:
            # Converter para DataFrames
            deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
            deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
            
            # Juntar os dados
            df_bitrix = pd.merge(
                deals_df[['ID', 'TITLE']],
                deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
                left_on='ID',
                right_on='DEAL_ID',
                how='left'
        with col1:
            st.metric(
                "Total de Famílias",
                str(len(df_report))
            )
            
            # Criar relatório final
            df_report = pd.merge(
                df_mysql,
                df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
                left_on='idfamilia',
                right_on='UF_CRM_1722605592778',
                how='left'
        
        with col2:
            st.metric(
                "Famílias Ativas",
                str(df_report['continua'].sum())
            )
            
            df_report['TITLE'] = df_report['TITLE'].fillna(df_report['idfamilia'])
            
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    f"{len(df_report):,}".replace(",", "."),
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    "Famílias Ativas",
                    f"{df_report['continua'].sum():,}".replace(",", "."),
                    f"{(df_report['continua'].sum() / len(df_report) * 100):.0f}%",
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "Famílias Canceladas",
                    f"{df_report['cancelou'].sum():,}".replace(",", "."),
                    f"{(df_report['cancelou'].sum() / len(df_report) * 100):.0f}%",
                    delta_color="normal"
                )
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de Pizza - Status
                valores_status = [df_report['continua'].sum(), df_report['cancelou'].sum()]
                labels_status = ['Continua', 'Cancelou']
                
                fig_pie = px.pie(
                    values=valores_status,
                    names=labels_status,
                    title='Distribuição de Status',
                    color_discrete_sequence=[COLORS['verde'], COLORS['vermelho']]
                )
                fig_pie.update_traces(
                    textinfo='percent+value',
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Tabela detalhada
            st.markdown("---")
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Detalhamento por Família</h3>", unsafe_allow_html=True)
            
            # Preparar dados para exibição
            df_display = df_report[[
                'TITLE', 'continua', 'cancelou', 'total_membros'
            ]].copy()
            
            df_display.columns = [
                'Família', 'Continua', 'Cancelou', 'Total Membros'
            ]
            
            # Adicionar status
            df_display['Status'] = 'Pendente'
            df_display.loc[df_display['Continua'] > 0, 'Status'] = 'Continua'
            df_display.loc[df_display['Cancelou'] > 0, 'Status'] = 'Cancelou'
            
            # Ordenar por status e nome
            df_display = df_display.sort_values(['Status', 'Família'])
            
            # Adicionar botão de download
            csv = df_display.to_csv(index=False)
            st.download_button(
                "📥 Download Relatório",
                csv,
                "status_familias.csv",
                "text/csv",
                key='download-csv'
        
        with col3:
            st.metric(
                "Famílias Canceladas",
                str(df_report['cancelou'].sum())
            )
            
            # Mostrar tabela
            st.dataframe(
                df_display,
                use_container_width=True,
                column_config={
                    'Família': st.column_config.TextColumn(
                        'Família',
                        width='large'
                    ),
                    'Continua': st.column_config.NumberColumn(
                        'Continua',
                        help='Número de membros que continuam'
                    ),
                    'Cancelou': st.column_config.NumberColumn(
                        'Cancelou',
                        help='Número de membros que cancelaram'
                    ),
                    'Total Membros': st.column_config.NumberColumn(
                        'Total Membros',
                        help='Total de membros da família'
                    ),
                    'Status': st.column_config.TextColumn(
                        'Status',
                        help='Status da família'
                    )
                }
            )
        
        # Tabela
        st.markdown("### Detalhamento por Família")
        st.dataframe(df_report)
