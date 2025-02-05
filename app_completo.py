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

# Funções
def consultar_bitrix(table, filtros=None):
    url = f"{st.secrets['bitrix24_base_url']}?token={st.secrets['bitrix24_token']}&table={table}"
    if filtros:
        response = requests.post(url, json=filtros)
    else:
        response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
# Título
st.title("Status das Famílias")

# Função para buscar dados do MySQL
def get_mysql_data():
    try:
        conn = mysql.connector.connect(
@@ -39,6 +24,7 @@ def get_mysql_data():
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"]
        )
        
        query = """
        SELECT 
            idfamilia,
@@ -51,6 +37,7 @@ def get_mysql_data():
          AND hasTechnicalProblems = 0
        GROUP BY idfamilia
        """
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
@@ -60,10 +47,18 @@ def get_mysql_data():
        if 'conn' in locals():
            conn.close()

# Título
st.title("Status das Famílias")
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

# Carregar dados
# Carregar dados do MySQL
df_mysql = get_mysql_data()

if df_mysql is not None:
@@ -81,11 +76,11 @@ def get_mysql_data():
    deals_uf = consultar_bitrix("crm_deal_uf")

    if deals_data and deals_uf:
        # Preparar dados do Bitrix24
        # Converter dados do Bitrix24 para DataFrame
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])

        # Juntar dados
        # Juntar dados do Bitrix24
        df_bitrix = pd.merge(
            deals_df[['ID', 'TITLE']],
            deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
@@ -94,8 +89,8 @@ def get_mysql_data():
            how='left'
        )

        # Relatório final
        df_report = pd.merge(
        # Juntar com dados do MySQL
        df_final = pd.merge(
            df_mysql,
            df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
            left_on='idfamilia',
@@ -104,29 +99,45 @@ def get_mysql_data():
        )

        # Usar idfamilia quando não tiver TITLE
        df_report['TITLE'] = df_report['TITLE'].fillna(df_report['idfamilia'])
        df_final['nome_familia'] = df_final['TITLE'].fillna(df_final['idfamilia'])
        
        # Selecionar colunas para exibição
        df_exibir = df_final[[
            'nome_familia',
            'continua',
            'cancelou',
            'total_membros'
        ]].copy()
        
        # Renomear colunas
        df_exibir.columns = [
            'Família',
            'Ativos',
            'Cancelados',
            'Total'
        ]

        # Métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total de Famílias",
                str(len(df_report))
                str(len(df_exibir))
            )

        with col2:
            st.metric(
                "Famílias Ativas",
                str(df_report['continua'].sum())
                str(df_exibir['Ativos'].sum())
            )

        with col3:
            st.metric(
                "Famílias Canceladas",
                str(df_report['cancelou'].sum())
                str(df_exibir['Cancelados'].sum())
            )

        # Tabela
        st.markdown("### Detalhamento por Família")
        st.dataframe(df_report)
        st.dataframe(df_exibir)
