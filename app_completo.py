import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import requests
import json
import time
from datetime import datetime, timedelta

# Cores
COLORS = {
    "verde": "#008C45",
    "branco": "#FFFFFF",
    "vermelho": "#CD212A",
    "azul": "#003399"
}

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Sistema de Relatórios")

# Configurações do Bitrix24
BITRIX_BASE_URL = "https://eunaeuropacidadania.bitrix24.com.br/bitrix/tools/biconnector/pbi.php"
BITRIX_TOKEN = "0z1rgUWgNbR0e53G7T88D9A1gkDWGly7br"

def get_mysql_data():
    """Função para buscar dados do MySQL"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql_host"],
            port=st.secrets["mysql_port"],
            database=st.secrets["mysql_database"],
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"]
        )
        
        query = """
        WITH dados_familia AS (
            SELECT 
                idfamilia,
                SUM(CASE WHEN paymentOption IN ("A", "B", "C", "D") THEN 1 ELSE 0 END) as continua,
                SUM(CASE WHEN paymentOption = "E" THEN 1 ELSE 0 END) as cancelou,
                COUNT(*) as total_membros,
                GROUP_CONCAT(
                    CASE 
                        WHEN paymentOption IS NULL OR paymentOption = "" 
                        THEN CONCAT_WS(" | ",
                            nome_completo,
                            telefone,
                            `e-mail`,
                            CASE WHEN is_menor = 1 THEN "Menor" ELSE "Maior" END
                        )
                    END
                    SEPARATOR "\n"
                ) as requerentes_sem_opcao
            FROM euna_familias
            WHERE is_menor = 0
              AND isSpecial = 0
              AND hasTechnicalProblems = 0
            GROUP BY idfamilia
        )
        SELECT 
            idfamilia,
            continua,
            cancelou,
            total_membros,
            requerentes_sem_opcao,
            (
                SELECT COUNT(*)
                FROM euna_familias e2
                WHERE e2.idfamilia = dados_familia.idfamilia
                AND (e2.paymentOption IS NULL OR e2.paymentOption = "")
            ) as total_sem_opcao
        FROM dados_familia
        """
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return None
    finally:
        if "conn" in locals():
            conn.close()

def consultar_bitrix(table, filtros=None, max_retries=3):
    """Função para consultar Bitrix24"""
    try:
        url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"
        
        # Se for crm_deal_uf, vamos filtrar apenas os IDs que precisamos
        if table == "crm_deal_uf" and filtros and "deal_ids" in filtros:
            deal_ids = filtros["deal_ids"]
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
    except Exception as e:
        st.error(f"Erro ao consultar Bitrix24: {e}")
        return None

def analisar_deals():
    """Função para analisar deals do Bitrix24"""
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
            id_index = deals_df[0].index("ID")
            
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
        deals_uf_df = deals_uf_df.rename(columns={"DEAL_ID": "ID"})
        
        # 5. Mesclar os dataframes
        df_completo = pd.merge(
            deals_df,
            deals_uf_df[["ID", "UF_CRM_1738699062493"]],
            on="ID",
            how="left"
        )
        
        # 6. Separar deals com e sem conteúdo no campo UF_CRM_1738699062493
        deals_com_conteudo = df_completo[
            df_completo["UF_CRM_1738699062493"].notna() & 
            (df_completo["UF_CRM_1738699062493"].astype(str) != "")
        ]
        
        deals_sem_conteudo = df_completo[
            df_completo["UF_CRM_1738699062493"].isna() | 
            (df_completo["UF_CRM_1738699062493"].astype(str) == "")
        ]
        
        # 7. Dos que têm conteúdo, separar por stage_id
        deals_com_link = deals_com_conteudo[deals_com_conteudo["STAGE_ID"] == "C32:UC_GBPN8V"]
        deals_sem_link = deals_com_conteudo[deals_com_conteudo["STAGE_ID"] != "C32:UC_GBPN8V"]
        
        st.success("✅ Análise concluída com sucesso!")
        
        return deals_com_link, deals_sem_link

# Sidebar para seleção de relatórios
tipo_relatorio = st.sidebar.selectbox(
    "Selecione o tipo de relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise de Deals", "Relatório 3"]
)

# Lógica principal
if tipo_relatorio == "Status das Famílias":
    st.title("📊 Status das Famílias")
    
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
            # Converter dados do Bitrix24 para DataFrame
            deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
            deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
            
            # Juntar dados do Bitrix24
            df_bitrix = pd.merge(
                deals_df[["ID", "TITLE"]],
                deals_uf_df[["DEAL_ID", "UF_CRM_1722605592778"]],
                left_on="ID",
                right_on="DEAL_ID",
                how="left"
            )
            
            # Juntar com dados do MySQL
            df_final = pd.merge(
                df_mysql,
                df_bitrix[["UF_CRM_1722605592778", "TITLE"]],
                left_on="idfamilia",
                right_on="UF_CRM_1722605592778",
                how="left"
            )
            
            # Usar idfamilia quando não tiver TITLE
            df_final["nome_familia"] = df_final["TITLE"].fillna(df_final["idfamilia"])
            
            # Selecionar colunas para exibição
            df_exibir = df_final[[
                "nome_familia",
                "continua",
                "cancelou",
                "total_membros",
                "total_sem_opcao"
            ]].copy()
            
            # Renomear colunas
            df_exibir.columns = [
                "Família",
                "Ativos",
                "Cancelados",
                "Total",
                "Sem Opção"
            ]
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    str(len(df_exibir))
                )
            
            with col2:
                st.metric(
                    "Famílias Ativas",
                    str(df_exibir["Ativos"].sum())
                )
            
            with col3:
                st.metric(
                    "Famílias Canceladas",
                    str(df_exibir["Cancelados"].sum())
                )
            
            # Gráfico de Pizza
            valores_status = [df_exibir["Ativos"].sum(), df_exibir["Cancelados"].sum()]
            labels_status = ["Ativos", "Cancelados"]
            
            fig_pie = px.pie(
                values=valores_status,
                names=labels_status,
                title="Distribuição de Status"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Tabela principal
            st.markdown("### Detalhamento por Família")
            st.dataframe(df_exibir)

elif tipo_relatorio == "Análise de Deals":
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
                "Etapa": ["Total Categoria 32", "Com Conteúdo", "Na Etapa C32:UC_GBPN8V"],
                "Quantidade": [1025, 38, 16]
            }
            fig_funil = px.funnel(
                dados_funil, 
                x="Quantidade", 
                y="Etapa",
                title="Funil de Deals"
            )
            fig_funil.update_traces(
                textinfo="value+percent initial",
                hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{percentInitial:.1%}"
            )
            st.plotly_chart(fig_funil, use_container_width=True)
            
            # 2. Gráficos de Distribuição
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - Conteúdo vs Sem Conteúdo
                fig_pie1 = px.pie(
                    values=[38, 987],
                    names=["Com Conteúdo", "Sem Conteúdo"],
                    title="Distribuição por Conteúdo",
                    color_discrete_sequence=["#00CC96", "#EF553B"]
                )
                fig_pie1.update_traces(
                    textposition="inside",
                    textinfo="percent+value",
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                )
                st.plotly_chart(fig_pie1, use_container_width=True)
            
            with col2:
                # Gráfico de pizza - Com Link vs Sem Link
                fig_pie2 = px.pie(
                    values=[16, 22],
                    names=["Com Link", "Sem Link"],
                    title="Distribuição dos Deals com Conteúdo",
                    color_discrete_sequence=["#00CC96", "#EF553B"]
                )
                fig_pie2.update_traces(
                    textposition="inside",
                    textinfo="percent+value",
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}"
                )
                st.plotly_chart(fig_pie2, use_container_width=True)
