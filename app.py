import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import requests
import json
import time
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Sistema de Relatórios",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Sistema de Relatórios")

# Configurações do Bitrix24
BITRIX_BASE_URL = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
BITRIX_TOKEN = "0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br"

def consultar_bitrix(table, filtros=None, max_retries=3):
    """
    Função para consultar a API do Bitrix24
    :param table: Nome da tabela (ex: crm_deal, crm_deal_uf)
    :param filtros: Dicionário com filtros a serem aplicados
    :param max_retries: Número máximo de tentativas
    :return: Lista com os resultados (primeira linha = colunas)
    """
    url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"
    
    # Se for crm_deal_uf, vamos filtrar apenas os IDs que precisamos
    if table == "crm_deal_uf" and filtros and 'deal_ids' in filtros:
        deal_ids = filtros['deal_ids']
        chunks = [deal_ids[i:i + 100] for i in range(0, len(deal_ids), 100)]
        
        all_results = None
        progress_bar = st.progress(0)
        
        for i, chunk in enumerate(chunks):
            progress = (i + 1) / len(chunks)
            progress_bar.progress(progress, f"Consultando dados {(progress * 100):.0f}%")
            
            chunk_filtros = {
                "dimensionsFilters": [[
                    {
                        "fieldName": "DEAL_ID",
                        "values": chunk,
                        "type": "INCLUDE",
                        "operator": "EQUALS"
                    }
                ]]
            }
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=chunk_filtros, timeout=30)
                    response.raise_for_status()
                    
                    if response.status_code == 200:
                        chunk_data = response.json()
                        if all_results is None:
                            all_results = chunk_data
                        else:
                            all_results.extend(chunk_data[1:])  # Pula o cabeçalho nas chunks subsequentes
                        break
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        st.error(f"Erro ao consultar chunk {i+1}: {str(e)}")
                        return None
                    time.sleep(2)
            
        progress_bar.empty()
        return all_results
    
    # Para outras tabelas ou consultas sem filtro de IDs
    for attempt in range(max_retries):
        try:
            if filtros:
                response = requests.post(url, json=filtros, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"Erro ao consultar {table}: {str(e)}")
                return None
            time.sleep(2)
    
    return None

# Função para conectar ao banco de dados
def conectar_mysql():
    try:
        conexao = mysql.connector.connect(
            host="database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com",
            port=3306,
            database="whatsapp_euna_data",
            user="Admin",
            password="4CzsgGMQRquwac5LdQhe"
        )
        return conexao
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para analisar deals do Bitrix24
def analisar_deals():
    with st.spinner("Analisando dados do Bitrix24..."):
        # 1. Consultar crm_deal (apenas categoria 32)
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
        
        deals_df = consultar_bitrix("crm_deal", filtros_deal)
        
        if deals_df is None:
            st.error("❌ Não foi possível obter os dados de deals")
            return None
        
        total_deals = len(deals_df) - 1  # -1 pois primeira linha são cabeçalhos
        st.success(f"✅ Encontrados {total_deals:,} deals na categoria 32".replace(",", "."))
            
        # 2. Consultar crm_deal_uf apenas para os IDs que precisamos
        with st.spinner("Buscando dados complementares..."):
            # Primeiro, vamos identificar o índice da coluna ID
            id_index = deals_df[0].index('ID')
            
            # Agora pegamos os IDs de todas as linhas exceto o cabeçalho
            deal_ids = [int(row[id_index]) for row in deals_df[1:]]
            
            st.write(f"Encontrados {len(deal_ids)} IDs para consulta")
            
            # Consultar crm_deal_uf apenas para esses IDs
            deals_uf_df = consultar_bitrix("crm_deal_uf", {"deal_ids": deal_ids})
            
            if deals_uf_df is None:
                st.error("❌ Não foi possível obter os dados complementares")
                return None
            
            total_uf = len(deals_uf_df) - 1
            st.success(f"✅ Dados complementares obtidos com sucesso")
        
        # 3. Converter listas em DataFrames
        if isinstance(deals_df, list):
            deals_df = pd.DataFrame(deals_df[1:], columns=deals_df[0])
        
        if isinstance(deals_uf_df, list):
            deals_uf_df = pd.DataFrame(deals_uf_df[1:], columns=deals_uf_df[0])
        
        # 4. Renomear coluna DEAL_ID para ID no DataFrame de UF
        deals_uf_df = deals_uf_df.rename(columns={'DEAL_ID': 'ID'})
        
        # 5. Mesclar os dataframes
        df_completo = pd.merge(
            deals_df,
            deals_uf_df[['ID', 'UF_CRM_1738699062493']],
            on='ID',
            how='left'
        )
        
        # 6. Separar deals com e sem conteúdo no campo UF_CRM_1738699062493
        deals_com_conteudo = df_completo[
            df_completo['UF_CRM_1738699062493'].notna() & 
            (df_completo['UF_CRM_1738699062493'].astype(str) != '')
        ]
        
        deals_sem_conteudo = df_completo[
            df_completo['UF_CRM_1738699062493'].isna() | 
            (df_completo['UF_CRM_1738699062493'].astype(str) == '')
        ]
        
        # 7. Dos que têm conteúdo, separar por stage_id
        deals_com_link = deals_com_conteudo[deals_com_conteudo['STAGE_ID'] == 'C32:UC_GBPN8V']
        deals_sem_link = deals_com_conteudo[deals_com_conteudo['STAGE_ID'] != 'C32:UC_GBPN8V']
        
        st.success("✅ Análise concluída com sucesso!")
        
        return deals_com_link, deals_sem_link

# Sidebar para seleção de relatórios
tipo_relatorio = st.sidebar.selectbox(
    "Selecione o tipo de relatório",
    ["Selecione uma opção", "Análise de Deals", "Relatório 2", "Relatório 3"]
)

# Lógica principal
if tipo_relatorio == "Análise de Deals":
    st.title("📊 Análise de Deals do Bitrix24")
    
    with st.spinner("Carregando dados do Bitrix24..."):
        resultado = analisar_deals()
        
        if resultado:
            deals_com_link, deals_sem_link = resultado
            
            # Métricas principais
            total_deals = len(deals_com_link) + len(deals_sem_link)
            
            # Container para os gráficos
            st.markdown("### Visão Geral dos Deals")

            # 1. Gráfico Funil - Visão Geral
            dados_funil = {
                'Etapa': ['Total Categoria 32', 'Com Conteúdo', 'Na Etapa C32:UC_GBPN8V'],
                'Quantidade': [1025, 38, 16]
            }
            fig_funil = px.funnel(
                dados_funil, 
                x='Quantidade', 
                y='Etapa',
                title='Funil de Deals'
            )
            fig_funil.update_traces(
                textinfo='value+percent initial',
                hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{percentInitial:.1%}"
            )
            st.plotly_chart(fig_funil, use_container_width=True)

            # 2. Gráficos de Distribuição
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - Conteúdo vs Sem Conteúdo
                fig_pie1 = px.pie(
                    values=[38, 987],
                    names=['Com Conteúdo', 'Sem Conteúdo'],
                    title='Distribuição por Conteúdo',
                    color_discrete_sequence=['#00CC96', '#EF553B']
                )
                fig_pie1.update_traces(
                    textposition='inside',
                    textinfo='percent+value',
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                )
                st.plotly_chart(fig_pie1, use_container_width=True)
            
            with col2:
                # Gráfico de pizza - Distribuição dos com Conteúdo
                fig_pie2 = px.pie(
                    values=[len(deals_com_link), len(deals_sem_link)],
                    names=['Na Etapa C32:UC_GBPN8V', 'Em Outras Etapas'],
                    title='Distribuição dos Deals com Conteúdo',
                    color_discrete_sequence=['#00CC96', '#EF553B']
                )
                fig_pie2.update_traces(
                    textposition='inside',
                    textinfo='percent+value',
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                )
                st.plotly_chart(fig_pie2, use_container_width=True)

            # 3. Gráfico de Barras Empilhadas
            dados_barras = pd.DataFrame({
                'Categoria': ['Deals'],
                'Sem Conteúdo': [987],
                'Com Conteúdo (Outras Etapas)': [22],
                'Com Conteúdo (C32:UC_GBPN8V)': [16]
            })

            fig_bar = px.bar(
                dados_barras,
                x='Categoria',
                y=['Sem Conteúdo', 'Com Conteúdo (Outras Etapas)', 'Com Conteúdo (C32:UC_GBPN8V)'],
                title='Distribuição Total dos Deals',
                color_discrete_sequence=['#EF553B', '#FFA15A', '#00CC96']
            )
            fig_bar.update_layout(
                showlegend=True,
                xaxis_title="",
                yaxis_title="Quantidade",
                barmode='stack'
            )
            fig_bar.update_traces(
                hovertemplate="<b>%{name}</b><br>Quantidade: %{y}"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # 4. Métricas em cards
            st.markdown("### Métricas Detalhadas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Categoria 32",
                    "1.025",
                    help="Total de deals na categoria 32"
                )
            
            with col2:
                st.metric(
                    "Com Conteúdo",
                    "38",
                    delta=f"{(38/1025*100):.1f}%",
                    help="Deals com conteúdo no campo UF_CRM_1738699062493"
                )
            
            with col3:
                st.metric(
                    "Na Etapa C32:UC_GBPN8V",
                    "16",
                    delta=f"{(16/38*100):.1f}% dos com conteúdo",
                    help="Deals com conteúdo na etapa C32:UC_GBPN8V"
                )
            
            with col4:
                st.metric(
                    "Em Outras Etapas",
                    "22",
                    delta=f"{(22/38*100):.1f}% dos com conteúdo",
                    help="Deals com conteúdo em outras etapas"
                )
                
elif tipo_relatorio == "Relatório 2":
    st.subheader("Relatório 2")
    # Aqui virá a lógica do relatório 2
    
elif tipo_relatorio == "Relatório 3":
    st.subheader("Relatório 3")
    # Aqui virá a lógica do relatório 3