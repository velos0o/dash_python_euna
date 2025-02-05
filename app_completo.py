import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import requests

# Cores
COLORS = {
    'verde': '#008C45',
    'branco': '#FFFFFF',
    'vermelho': '#CD212A',
    'azul': '#003399'
}

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("Status das Famílias")

# Função para buscar dados do MySQL
def get_mysql_data():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql_host"],
            port=st.secrets["mysql_port"],
            database=st.secrets["mysql_database"],
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"]
        )
        
        query = """
        SELECT 
            idfamilia,
            SUM(CASE WHEN paymentOption IN ('A', 'B', 'C', 'D') THEN 1 ELSE 0 END) as continua,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) as cancelou,
            COUNT(*) as total_membros
        FROM euna_familias
        WHERE is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
        GROUP BY idfamilia
        """
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

# Função para consultar Bitrix24
def consultar_bitrix(table, filtros=None):
    url = f"{st.secrets['bitrix24_base_url']}?token={st.secrets['bitrix24_token']}&table={table}"
    if filtros:
        response = requests.post(url, json=filtros)
    else:
        response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Carregar dados do MySQL
df_mysql = get_mysql_data()

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
    
    deals_data = consultar_bitrix("crm_deal", filtros_deal)
    deals_uf = consultar_bitrix("crm_deal_uf")
    
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
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total de Famílias",
                str(len(df_report))
            )
        
        with col2:
            st.metric(
                "Famílias Ativas",
                str(df_report['continua'].sum())
            )
        
        with col3:
            st.metric(
                "Famílias Canceladas",
                str(df_report['cancelou'].sum())
            )
        
        # Tabela
        st.markdown("### Detalhamento por Família")
        st.dataframe(df_report)

        # Separador visual
        st.markdown("---")

        # Nova seção para Status das Famílias
        st.markdown("### Status das Famílias")
        
        # Query para buscar status das famílias
        query_status = """
        SELECT 
            f.idfamilia,
            f.paymentOption as status,
            f.name,
            f.email,
            f.phone
        FROM euna_familias f
        WHERE f.is_menor = 0
          AND f.isSpecial = 0
          AND f.hasTechnicalProblems = 0
        """
        
        try:
            conn = mysql.connector.connect(
                host=st.secrets["mysql_host"],
                port=st.secrets["mysql_port"],
                database=st.secrets["mysql_database"],
                user=st.secrets["mysql_user"],
                password=st.secrets["mysql_password"]
            )
            
            df_status = pd.read_sql(query_status, conn)
            
            # Dropdown para selecionar o status
            status_selecionado = st.selectbox(
                "Filtrar por Status:",
                ['Todos', 'A', 'B', 'C', 'D', 'E']
            )
            
            # Filtrando os dados
            if status_selecionado != 'Todos':
                df_status_filtrado = df_status[df_status['status'] == status_selecionado]
            else:
                df_status_filtrado = df_status
            
            # Renomeando colunas para exibição
            df_status_filtrado.columns = ['ID Família', 'Status', 'Nome', 'Email', 'Telefone']
            
            # Mostrando a tabela
            if not df_status_filtrado.empty:
                st.dataframe(
                    df_status_filtrado,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Nenhum registro encontrado para este status.")
                
        except Exception as e:
            st.error(f"Erro ao buscar dados de status: {e}")
        finally:
            if 'conn' in locals():
                conn.close()