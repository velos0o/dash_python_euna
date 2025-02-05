import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import mysql.connector
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Sistema de Relatórios Euna",
    page_icon="📊",
    layout="wide"
)

# Configurações do Bitrix24 (usando secrets)
BITRIX_BASE_URL = st.secrets["bitrix24_base_url"]
BITRIX_TOKEN = st.secrets["bitrix24_token"]

from bitrix_queries import get_deals_filter, get_deal_uf_filter

def consultar_bitrix(table, filtros=None, start_date=None, end_date=None):
    """Função otimizada para consultar a API do Bitrix24"""
    url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"
    
    # Se não houver filtros específicos, usar os filtros otimizados
    if not filtros:
        if table == "crm_deal":
            filtros = get_deals_filter(start_date, end_date)
        elif table == "crm_deal_uf":
            filtros = get_deal_uf_filter()
    
    try:
        response = requests.post(url, json=filtros, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao consultar Bitrix24: {str(e)}")
        return None

def get_mysql_data():
    """Busca dados do MySQL"""
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

def criar_relatorio_funil():
    """Criar relatório do funil de famílias com análise detalhada"""
    with st.spinner("Analisando dados do Bitrix24..."):
        # 1. Consultar deals da categoria 32
        filtros_deal = {
            "dimensionsFilters": [[
                {
                    "fieldName": "CATEGORY_ID",
                    "values": [32],
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }
            ]],
            "fields": [
                {"name": "ID"},
                {"name": "TITLE"},
                {"name": "STAGE_ID"},
                {"name": "CATEGORY_ID"}
            ]
        }
        
        # Consultar deals
        response_deals = consultar_bitrix("crm_deal", filtros_deal)
        if response_deals is None:
            st.error("❌ Não foi possível obter os dados de deals")
            return None
            
        # Converter para DataFrame
        deals_df = pd.DataFrame(response_deals[1:], columns=response_deals[0])
        total_categoria_32 = len(deals_df)
        
        # 2. Consultar campos personalizados
        response_uf = consultar_bitrix("crm_deal_uf")
        if response_uf is None:
            st.error("❌ Não foi possível obter os dados complementares")
            return None
            
        deals_uf_df = pd.DataFrame(response_uf[1:], columns=response_uf[0])
        
        # Filtrar registros com conteúdo em UF_CRM_1738699062493
        deals_uf_df = deals_uf_df[
            deals_uf_df['UF_CRM_1738699062493'].notna() & 
            (deals_uf_df['UF_CRM_1738699062493'].astype(str) != '')
        ]
        
        # Consultar dados do MySQL para análise de familiares
        try:
            with mysql.connector.connect(
                host=st.secrets["mysql_host"],
                port=st.secrets["mysql_port"],
                database=st.secrets["mysql_database"],
                user=st.secrets["mysql_user"],
                password=st.secrets["mysql_password"]
            ) as conn:
                # Query para análise de familiares
                query = """
                SELECT 
                    f.idfamilia,
                    COUNT(CASE 
                        WHEN f.paymentOption != 'E' AND (
                            f.is_menor = 0 OR 
                            (TIMESTAMPDIFF(YEAR, f.birthdate, CURDATE()) >= 12)
                        ) THEN 1 
                        END
                    ) as total_ativos,
                    COUNT(CASE 
                        WHEN f.paymentOption = 'E' THEN 1 
                        END
                    ) as total_cancelados
                FROM euna_familias f
                GROUP BY f.idfamilia
                """
                df_familias = pd.read_sql(query, conn)
        except Exception as e:
            st.error(f"Erro ao consultar banco de dados: {e}")
            return None
        
        # Juntar dados do Bitrix24 com MySQL
        df_completo = pd.merge(
            deals_df,
            deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778', 'UF_CRM_1738699062493']],
            left_on='ID',
            right_on='DEAL_ID',
            how='left'
        )
        
        # Juntar com dados das famílias
        df_completo = pd.merge(
            df_completo,
            df_familias,
            left_on='UF_CRM_1722605592778',
            right_on='idfamilia',
            how='left'
        )
        
        # Calcular métricas
        total_deals = len(deals_df)
        total_com_conteudo = len(df_completo[df_completo['UF_CRM_1738699062493'].notna()])
        total_ativos = df_completo['total_ativos'].sum()
        total_cancelados = df_completo['total_cancelados'].sum()
        
        # Mostrar métricas em cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Categoria 32",
                f"{total_deals:,}".replace(",", "."),
                help="Total de deals na categoria 32"
            )
        
        with col2:
            st.metric(
                "Com Conteúdo",
                f"{total_com_conteudo:,}".replace(",", "."),
                f"{(total_com_conteudo/total_deals*100):.1f}%",
                help="Deals com conteúdo preenchido (UF_CRM_1738699062493)"
            )
        
        with col3:
            st.metric(
                "Requerentes Ativos",
                f"{total_ativos:,}".replace(",", "."),
                help="Total de requerentes ativos (excluindo menores de 12 anos)"
            )
        
        with col4:
            st.metric(
                "Requerentes Cancelados",
                f"{total_cancelados:,}".replace(",", "."),
                help="Total de requerentes cancelados"
            )
        
        # Criar gráfico de funil
        dados_funil = {
            'Etapa': [
                'Total Categoria 32',
                'Com Conteúdo',
                'Requerentes Ativos',
                'Requerentes Cancelados'
            ],
            'Quantidade': [
                total_deals,
                total_com_conteudo,
                total_ativos,
                total_cancelados
            ]
        }
        
        fig_funil = px.funnel(
            dados_funil,
            x='Quantidade',
            y='Etapa',
            title='Funil de Conversão - Categoria 32'
        )
        
        fig_funil.update_traces(
            textinfo='value+percent initial',
            hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{percentInitial:.1%}"
        )
        
        st.plotly_chart(fig_funil, use_container_width=True)
        
        # Mostrar detalhes por família
        if st.checkbox("Ver detalhes por família"):
            st.subheader("Detalhes por Família")
            
            df_detalhes = df_completo[
                df_completo['UF_CRM_1738699062493'].notna()
            ][[
                'ID', 'TITLE', 'UF_CRM_1722605592778',
                'total_ativos', 'total_cancelados'
            ]].copy()
            
            # Calcular total de requerentes
            df_detalhes['total_requerentes'] = df_detalhes['total_ativos'] + df_detalhes['total_cancelados']
            
            # Renomear colunas
            df_detalhes.columns = [
                'ID do Deal',
                'Nome da Família',
                'ID da Família',
                'Requerentes Ativos',
                'Requerentes Cancelados',
                'Total de Requerentes'
            ]
            
            # Ordenar por total de requerentes
            df_detalhes = df_detalhes.sort_values('Total de Requerentes', ascending=False)
            
            st.dataframe(
                df_detalhes,
                hide_index=True,
                use_container_width=True
            )
        
        if deals_df is None:
            st.error("❌ Não foi possível obter os dados de deals")
            return None
        
        # Converter para DataFrame
        deals_df = pd.DataFrame(deals_df[1:], columns=deals_df[0])
        total_deals = len(deals_df)
        
        # 2. Consultar campos personalizados
        deals_uf = consultar_bitrix("crm_deal_uf")
        if deals_uf is None:
            st.error("❌ Não foi possível obter os dados complementares")
            return None
        
        deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
        
        # 3. Análise dos dados
        # Total de deals na categoria 32
        total_categoria_32 = total_deals
        
        # Total com conteúdo no campo UF_CRM_1722605592778
        deals_uf_df = deals_uf_df[deals_uf_df['UF_CRM_1722605592778'].notna() & 
                                (deals_uf_df['UF_CRM_1722605592778'] != '')]
        total_com_conteudo = len(deals_uf_df)
        
        # Total na etapa C32:UC_GBPN8V
        total_etapa_especifica = len(deals_df[deals_df['STAGE_ID'] == 'C32:UC_GBPN8V'])
        
        return {
            'total_categoria_32': total_categoria_32,
            'total_com_conteudo': total_com_conteudo,
            'total_etapa_especifica': total_etapa_especifica,
            'deals_df': deals_df,
            'deals_uf_df': deals_uf_df
        }

# Sidebar para seleção de relatórios
relatorio_selecionado = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Funil de Famílias", "Status das Famílias"]
)

if relatorio_selecionado == "Funil de Famílias":
    st.title("📊 Funil de Famílias")
    
    # Criar relatório do funil
    dados_funil = criar_relatorio_funil()
    
    if dados_funil:
        # Métricas em cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Categoria 32",
                f"{dados_funil['total_categoria_32']:,}".replace(",", "."),
                help="Total de deals na categoria 32"
            )
        
        with col2:
            st.metric(
                "Com ID Família",
                f"{dados_funil['total_com_conteudo']:,}".replace(",", "."),
                f"{dados_funil['total_com_conteudo']/dados_funil['total_categoria_32']:.1%}",
                help="Deals com conteúdo no campo UF_CRM_1722605592778"
            )
        
        with col3:
            st.metric(
                "Na Etapa C32:UC_GBPN8V",
                f"{dados_funil['total_etapa_especifica']:,}".replace(",", "."),
                f"{dados_funil['total_etapa_especifica']/dados_funil['total_com_conteudo']:.1%}",
                help="Deals na etapa C32:UC_GBPN8V"
            )
        
        # Gráfico Funil
        dados_funil_viz = {
            'Etapa': ['Total Categoria 32', 'Com ID Família', 'Na Etapa C32:UC_GBPN8V'],
            'Quantidade': [
                dados_funil['total_categoria_32'],
                dados_funil['total_com_conteudo'],
                dados_funil['total_etapa_especifica']
            ]
        }
        
        fig_funil = px.funnel(
            dados_funil_viz,
            x='Quantidade',
            y='Etapa',
            title='Funil de Conversão'
        )
        
        fig_funil.update_traces(
            textinfo='value+percent initial',
            hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{percentInitial:.1%}"
        )
        
        st.plotly_chart(fig_funil, use_container_width=True)

elif relatorio_selecionado == "Status das Famílias":
    st.title("👨‍👩‍👧‍👦 Status das Famílias")
    
    # Carregar dados do MySQL
    df_mysql = get_mysql_data()
    
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
        
        deals_data = consultar_bitrix("crm_deal", filtros_deal)
        deals_uf = consultar_bitrix("crm_deal_uf")
        
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
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    f"{len(df_report):,}".replace(",", ".")
                )
            
            with col2:
                st.metric(
                    "Total de Membros",
                    f"{df_report['total_membros'].sum():,}".replace(",", ".")
                )
            
            with col3:
                st.metric(
                    "Total Continua",
                    f"{df_report['continua'].sum():,}".replace(",", "."),
                    f"{df_report['continua'].sum() / df_report['total_membros'].sum():.1%}"
                )
            
            with col4:
                st.metric(
                    "Total Cancelou",
                    f"{df_report['cancelou'].sum():,}".replace(",", "."),
                    f"{df_report['cancelou'].sum() / df_report['total_membros'].sum():.1%}"
                )
            
            # Consultar distribuição das opções de pagamento
            df_payment_options = pd.DataFrame()
            
            try:
                with mysql.connector.connect(
                    host=st.secrets["mysql_host"],
                    port=st.secrets["mysql_port"],
                    database=st.secrets["mysql_database"],
                    user=st.secrets["mysql_user"],
                    password=st.secrets["mysql_password"]
                ) as conn:
                    query = """
                    SELECT 
                        paymentOption,
                        COUNT(*) as total
                    FROM euna_familias
                    WHERE is_menor = 0
                      AND isSpecial = 0
                      AND hasTechnicalProblems = 0
                    GROUP BY paymentOption
                    ORDER BY paymentOption
                    """
                    df_payment_options = pd.read_sql(query, conn)
            except Exception as e:
                st.error(f"Erro ao consultar opções de pagamento: {e}")
                df_payment_options = pd.DataFrame(columns=['paymentOption', 'total'])
            
            # Mapear descrições das opções de pagamento
            payment_descriptions = {
                'A': 'Opção A',
                'B': 'Opção B',
                'C': 'Opção C',
                'D': 'Opção D',
                'E': 'Cancelado'
            }
            
            df_payment_options['Descrição'] = df_payment_options['paymentOption'].map(payment_descriptions)
            
            # Criar visualizações
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de Pizza - Status Geral
                valores_status = [df_report['continua'].sum(), df_report['cancelou'].sum()]
                labels_status = ['Continua', 'Cancelou']
                
                fig_pie = px.pie(
                    values=valores_status,
                    names=labels_status,
                    title='Distribuição de Status',
                    color_discrete_sequence=['#00CC96', '#EF553B']
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Gráfico de Pizza - Distribuição por Opção de Pagamento
                fig_payment = px.pie(
                    df_payment_options,
                    values='total',
                    names='Descrição',
                    title='Distribuição por Opção de Pagamento',
                    color_discrete_sequence=['#00CC96', '#2ECC71', '#3498DB', '#9B59B6', '#EF553B']
                )
                fig_payment.update_traces(
                    textposition='inside',
                    textinfo='percent+label+value'
                )
                st.plotly_chart(fig_payment, use_container_width=True)
            
            # Adicionar tabela com detalhes das opções de pagamento
            st.subheader("Detalhes por Opção de Pagamento")
            df_payment_details = df_payment_options.copy()
            df_payment_details.columns = ['Opção', 'Total', 'Descrição']
            df_payment_details['Percentual'] = (df_payment_details['Total'] / df_payment_details['Total'].sum() * 100).round(1).astype(str) + '%'
            st.dataframe(
                df_payment_details[['Descrição', 'Total', 'Percentual']],
                hide_index=True,
                use_container_width=True
            )
            
            # Tabela detalhada
            st.subheader("Detalhes por Família")
            
            df_display = df_report[['idfamilia', 'TITLE', 'continua', 'cancelou', 'total_membros']].copy()
            df_display.columns = ['ID da Família', 'Nome da Família', 'Continua', 'Cancelou', 'Total de Membros']
            
            st.dataframe(
                df_display.sort_values('Total de Membros', ascending=False),
                hide_index=True
            )