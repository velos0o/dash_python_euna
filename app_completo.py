import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from bitrix_api import Bitrix24API
from database import Database

# Cores personalizadas
COLORS = {
    'verde': '#008C45',  # Verde da bandeira italiana
    'branco': '#FFFFFF', # Branco da bandeira italiana
    'vermelho': '#CD212A', # Vermelho da bandeira italiana
    'azul': '#003399'    # Azul da bandeira da UE
}

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon="📊",
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

# Cabeçalho com bandeira italiana
st.markdown(
    f"""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <div style="
            width: 60px;
            height: 40px;
            margin-right: 20px;
            display: flex;
            overflow: hidden;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="flex: 1; background-color: {COLORS['verde']};"></div>
            <div style="flex: 1; background-color: {COLORS['branco']};"></div>
            <div style="flex: 1; background-color: {COLORS['vermelho']};"></div>
        </div>
        <div>
            <h1 style='color: {COLORS['azul']}; margin: 0;'>
                Sistema de Relatórios - Eu na Europa
            </h1>
            <p style='color: {COLORS['azul']}; font-size: 1.2em; margin: 0;'>
                Análise de Famílias e Requerentes
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Inicializar conexões
@st.cache_resource
def get_connections():
    bitrix = Bitrix24API(
        base_url=st.secrets["bitrix24_base_url"],
        token=st.secrets["bitrix24_token"]
    )
    
    db = Database(
        host=st.secrets["mysql_host"],
        port=st.secrets["mysql_port"],
        database=st.secrets["mysql_database"],
        user=st.secrets["mysql_user"],
        password=st.secrets["mysql_password"]
    )
    
    return bitrix, db

bitrix, db = get_connections()

# Funções de dados com cache
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_mysql_data():
    """Busca dados do MySQL"""
    df, df_options = db.get_family_data()
    if df is None:
        st.error("Erro ao buscar dados do MySQL")
    return df, df_options

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_bitrix_data():
    """Busca dados do Bitrix24"""
    deals_df, deals_uf_df = bitrix.get_deals_category_32()
    if deals_df is None:
        st.error("Erro ao buscar dados do Bitrix24")
    return deals_df, deals_uf_df

# Sidebar para seleção de relatórios
relatorio_selecionado = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Funil de Famílias", "Status das Famílias"]
)

if relatorio_selecionado == "Funil de Famílias":
    st.markdown(f"<h1 style='color: {COLORS['azul']}'>📊 Funil de Famílias</h1>", unsafe_allow_html=True)
    
    # Criar relatório do funil
    with st.spinner("Analisando dados..."):
        deals_df, deals_uf_df = get_bitrix_data()
        
        if deals_df is not None and deals_uf_df is not None:
            total_categoria_32 = len(deals_df)
            
            # Filtrar registros com ID de família
            deals_com_id = deals_uf_df[
                deals_uf_df['UF_CRM_1722605592778'].notna() & 
                (deals_uf_df['UF_CRM_1722605592778'].astype(str) != '')
            ]
            total_com_id = len(deals_com_id)
            
            # Métricas em cards
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Total Categoria 32",
                    f"{total_categoria_32:,}".replace(",", "."),
                    help="Total de deals na categoria 32",
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    "Com ID de Família",
                    f"{total_com_id:,}".replace(",", "."),
                    f"{(total_com_id/total_categoria_32*100):.1f}%",
                    help="Deals com ID de família preenchido",
                    delta_color="normal"
                )
            
            # Gráfico de funil
            dados_funil = {
                'Etapa': ['Total Categoria 32', 'Com ID de Família'],
                'Quantidade': [total_categoria_32, total_com_id]
            }
            
            fig_funil = px.funnel(
                dados_funil,
                x='Quantidade',
                y='Etapa',
                title='Funil de Conversão'
            )
            
            fig_funil.update_traces(
                textinfo='value+percent initial',
                hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{percentInitial:.1%}",
                marker_color=[COLORS['azul'], COLORS['verde']]
            )
            
            st.plotly_chart(fig_funil, use_container_width=True)

elif relatorio_selecionado == "Status das Famílias":
    st.markdown(f"<h1 style='color: {COLORS['azul']}'>Status das Famílias</h1>", unsafe_allow_html=True)
    
    # Carregar dados
    df_mysql, df_options = get_mysql_data()
    
    if df_mysql is not None:
        # Buscar nomes das famílias no Bitrix24
        deals_df, deals_uf_df = get_bitrix_data()
        
        if deals_df is not None and deals_uf_df is not None:
            # Juntar os dados
            df_bitrix = pd.merge(
                deals_df[['ID', 'TITLE']],
                deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
                left_on='ID',
                right_on='DEAL_ID',
                how='left'
            )
            
            # Criar relatório final
            df_report = pd.merge(
                df_mysql,
                df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
                left_on='idfamilia',
                right_on='UF_CRM_1722605592778',
                how='left'
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
                    f"{(df_report['continua'].sum() / len(df_report) * 100):.1f}%",
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "Famílias Canceladas",
                    f"{df_report['cancelou'].sum():,}".replace(",", "."),
                    f"{(df_report['cancelou'].sum() / len(df_report) * 100):.1f}%",
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
            
            with col2:
                # Gráfico de Pizza - Opções de Pagamento
                if df_options is not None:
                    fig_options = px.pie(
                        df_options,
                        values='total',
                        names='paymentOption',
                        title='Distribuição por Opção de Pagamento',
                        color_discrete_sequence=[
                            COLORS['verde'],
                            '#2ECC71',
                            '#3498DB',
                            '#9B59B6',
                            COLORS['vermelho']
                        ]
                    )
                    fig_options.update_traces(
                        textinfo='percent+value+label',
                        hovertemplate="<b>Opção %{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                    )
                    st.plotly_chart(fig_options, use_container_width=True)
            
            # Pessoas sem opção de pagamento
            st.subheader("Pessoas sem Opção de Pagamento")
            df_sem_opcao = df_report[df_report['pessoas_sem_opcao'].notna()]
            
            if not df_sem_opcao.empty:
                for _, row in df_sem_opcao.iterrows():
                    with st.expander(f"Família: {row['TITLE']}"):
                        st.text(row['pessoas_sem_opcao'])