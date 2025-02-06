import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import requests

# Configuração da página
st.set_page_config(
    page_title='Eu na Europa - Sistema de Relatórios',
    page_icon='📊',
    layout='wide'
)

# Título
st.title('Status das Famílias')

# Função para buscar dados do MySQL
def get_mysql_data():
    try:
        conn = mysql.connector.connect(
            host=st.secrets['mysql_host'],
            port=st.secrets['mysql_port'],
            database=st.secrets['mysql_database'],
            user=st.secrets['mysql_user'],
            password=st.secrets['mysql_password']
        )
        
        # Query principal para status das famílias
        query_status = '''
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
        '''
        
        # Query para pessoas sem opção
        query_sem_opcao = '''
        SELECT 
            idfamilia,
            nome_completo,
            telefone,
            `e-mail` as email,
            CASE WHEN is_menor = 1 THEN 'Menor' ELSE 'Maior' END as status_idade
        FROM euna_familias
        WHERE (paymentOption IS NULL OR paymentOption = '')
          AND is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
        ORDER BY idfamilia, nome_completo
        '''
        
        df_status = pd.read_sql(query_status, conn)
        df_sem_opcao = pd.read_sql(query_sem_opcao, conn)
        
        return df_status, df_sem_opcao
        
    except Exception as e:
        st.error(f'Erro ao conectar ao MySQL: {e}')
        return None, None
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
df_status, df_sem_opcao = get_mysql_data()

if df_status is not None:
    # Buscar dados do Bitrix24
    filtros_deal = {
        'dimensionsFilters': [[{
            'fieldName': 'CATEGORY_ID',
            'values': [32],
            'type': 'INCLUDE',
            'operator': 'EQUALS'
        }]]
    }
    
    deals_data = consultar_bitrix('crm_deal', filtros_deal)
    deals_uf = consultar_bitrix('crm_deal_uf')
    
    if deals_data and deals_uf:
        # Converter dados do Bitrix24 para DataFrame
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
        
        # Juntar dados do Bitrix24
        df_bitrix = pd.merge(
            deals_df[['ID', 'TITLE']],
            deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
            left_on='ID',
            right_on='DEAL_ID',
            how='left'
        )
        
        # Juntar com dados do MySQL
        df_final = pd.merge(
            df_status,
            df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
            left_on='idfamilia',
            right_on='UF_CRM_1722605592778',
            how='left'
        )
        
        # Usar idfamilia quando não tiver TITLE
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
                'Total de Famílias',
                str(len(df_exibir))
            )
        
        with col2:
            st.metric(
                'Famílias Ativas',
                str(df_exibir['Ativos'].sum())
            )
        
        with col3:
            st.metric(
                'Famílias Canceladas',
                str(df_exibir['Cancelados'].sum())
            )
        
        # Gráfico de Pizza
        valores_status = [df_exibir['Ativos'].sum(), df_exibir['Cancelados'].sum()]
        labels_status = ['Ativos', 'Cancelados']
        
        fig_pie = px.pie(
            values=valores_status,
            names=labels_status,
            title='Distribuição de Status'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Tabela principal
        st.markdown('### Detalhamento por Família')
        st.dataframe(df_exibir)
        
        # Seção de pessoas sem opção
        if df_sem_opcao is not None and len(df_sem_opcao) > 0:
            st.markdown('---')
            st.markdown('### Pessoas sem Opção de Pagamento')
            
            # Juntar com nomes do Bitrix24
            df_sem_opcao = pd.merge(
                df_sem_opcao,
                df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
                left_on='idfamilia',
                right_on='UF_CRM_1722605592778',
                how='left'
            )
            df_sem_opcao['nome_familia'] = df_sem_opcao['TITLE'].fillna(df_sem_opcao['idfamilia'])
            
            # Agrupar por família
            familias_unicas = df_sem_opcao['nome_familia'].unique()
            
            # Mostrar total
            st.metric(
                'Total de Pessoas sem Opção',
                str(len(df_sem_opcao)),
                f'Em {len(familias_unicas)} famílias'
            )
            
            # Mostrar por família
            for familia in sorted(familias_unicas):
                pessoas = df_sem_opcao[df_sem_opcao['nome_familia'] == familia]
                with st.expander(f'Família: {familia} ({len(pessoas)} pessoas)'):
                    # Preparar dados para exibição
                    df_pessoas = pessoas[[
                        'nome_completo',
                        'telefone',
                        'email',
                        'status_idade'
                    ]].copy()
                    
                    df_pessoas.columns = [
                        'Nome',
                        'Telefone',
                        'Email',
                        'Status'
                    ]
                    
                    st.dataframe(df_pessoas)