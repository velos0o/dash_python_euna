import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import requests
import json
import time
import io
from datetime import datetime, timedelta

# Cores
# Cores do tema (Itália e União Europeia)
COLORS = {
    "verde": "#008C45",
    "branco": "#FFFFFF",
    "vermelho": "#CD212A",
    "azul": "#003399"
    "verde": "#008C45",      # Verde Itália
    "branco": "#FFFFFF",     # Branco
    "vermelho": "#CD212A",   # Vermelho Itália
    "azul": "#003399",       # Azul UE
    "azul_claro": "#4267b2", # Azul secundário
    "cinza": "#F5F7FA",      # Fundo
    "texto": "#1E3A8A"       # Texto principal
}

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon="📊",
    layout="wide"
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Sistema de Relatórios")
# CSS personalizado
st.markdown("""
    <style>
        /* Configurações globais */
        :root {
            --verde: #008C45;
            --branco: #FFFFFF;
            --vermelho: #CD212A;
            --azul: #003399;
            --azul-claro: #4267b2;
            --cinza: #F5F7FA;
            --texto: #1E3A8A;
        }
        
        /* Configurações gerais */
        .stApp {
            background-color: var(--cinza);
        }
        
        /* Cards e containers */
        .metric-card {
            background: var(--branco);
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-top: 4px solid var(--azul);
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--azul);
            margin: 0.5rem 0;
        }
        
        .metric-label {
            font-size: 1rem;
            color: var(--texto);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Tabelas */
        .dataframe {
            background: var(--branco) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        }
        
        .dataframe th {
            background-color: var(--azul) !important;
            color: var(--branco) !important;
            font-weight: 600 !important;
            padding: 1rem !important;
            text-align: left !important;
        }
        
        .dataframe td {
            padding: 1rem !important;
            border-bottom: 1px solid var(--cinza) !important;
            color: #000000 !important;
            background-color: var(--branco) !important;
        }
        
        /* Hover na tabela */
        .dataframe tr:hover td {
            background-color: #f8f9fa !important;
        }
        
        /* Botões */
        .stButton>button {
            background-color: var(--azul) !important;
            color: var(--branco) !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        .stButton>button:hover {
            background-color: var(--azul-claro) !important;
            transform: translateY(-2px);
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--branco);
            border-right: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        [data-testid="stSidebar"] .css-1d391kg {
            padding-top: 2rem;
        }
        
        .sidebar-title {
            color: var(--azul);
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding: 0 1rem;
            border-left: 4px solid var(--verde);
        }
    </style>
""", unsafe_allow_html=True)

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
def consultar_bitrix(table, filtros=None, max_retries=3, timeout=30):
    """Função para consultar Bitrix24 com retry e timeout"""
    for attempt in range(max_retries):
        try:
            url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"

            all_results = None
            progress_bar = st.progress(0)
            if filtros:
                response = requests.post(url, json=filtros, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)

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
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                st.error(f"Timeout ao consultar {table} (tentativa {attempt + 1}/{max_retries})")
                return None
            st.warning(f"Timeout, tentando novamente... ({attempt + 1}/{max_retries})")
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                st.error(f"Erro ao consultar {table}: {str(e)}")
                return None
            st.warning(f"Erro, tentando novamente... ({attempt + 1}/{max_retries})")
            time.sleep(1)
    
    return None

def analisar_deals():
    """Função para analisar deals do Bitrix24"""
    with st.spinner("Analisando dados do Bitrix24..."):
        # 1. Consultar crm_deal (apenas categoria 32)
    try:
        # 1. Consultar crm_deal (categoria 32 - Negociação de Taxa)
        filtros_deal = {
            "dimensionsFilters": [[
                {
                    "fieldName": "CATEGORY_ID",
                    "values": [32],
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }
            ]]
            ]],
            "select": [
                "ID", "TITLE", "DATE_CREATE", "ASSIGNED_BY_NAME", 
                "STAGE_ID", "STAGE_NAME", "CATEGORY_NAME"
            ]
        }

        deals_df = consultar_bitrix("crm_deal", filtros_deal)
        deals_data = consultar_bitrix("crm_deal", filtros_deal)

        if deals_df is None:
            st.error("❌ Não foi possível obter os dados de deals")
        if not deals_data:
            st.error("Não foi possível obter os dados de negócios")
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
        # Converter para DataFrame
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])

        if isinstance(deals_uf_df, list):
            deals_uf_df = pd.DataFrame(deals_uf_df[1:], columns=deals_uf_df[0])
        if deals_df.empty:
            st.warning("Nenhum negócio encontrado na categoria 32")
            return None
        
        # 2. Consultar crm_deal_uf apenas para os IDs encontrados
        deal_ids = deals_df["ID"].tolist()
        
        filtros_uf = {
            "dimensionsFilters": [[
                {
                    "fieldName": "DEAL_ID",
                    "values": deal_ids,
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }
            ]],
            "select": ["DEAL_ID", "UF_CRM_1738699062493"]
        }

        # 4. Renomear coluna DEAL_ID para ID no DataFrame de UF
        deals_uf_df = deals_uf_df.rename(columns={"DEAL_ID": "ID"})
        deals_uf_data = consultar_bitrix("crm_deal_uf", filtros_uf)

        # 5. Mesclar os dataframes
        if not deals_uf_data:
            st.error("Não foi possível obter os dados complementares")
            return None
            
        deals_uf_df = pd.DataFrame(deals_uf_data[1:], columns=deals_uf_data[0])
        
        # 3. Mesclar os dataframes
        df_completo = pd.merge(
            deals_df,
            deals_uf_df[["ID", "UF_CRM_1738699062493"]],
            on="ID",
            deals_uf_df[["DEAL_ID", "UF_CRM_1738699062493"]],
            left_on="ID",
            right_on="DEAL_ID",
            how="left"
        )

        # 6. Separar deals com e sem conteúdo no campo UF_CRM_1738699062493
        deals_com_conteudo = df_completo[
            df_completo["UF_CRM_1738699062493"].notna() & 
            (df_completo["UF_CRM_1738699062493"].astype(str) != "")
        ]
        # 4. Calcular métricas
        metricas = {
            "total_negocios": len(df_completo),
            "categoria_name": df_completo["CATEGORY_NAME"].iloc[0] if not df_completo.empty else "N/A",
            "com_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""]),
            "sem_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() == ""]),
            "stage_negociacao": df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]["STAGE_NAME"].iloc[0] if not df_completo.empty else "N/A",
            "total_stage_negociacao": len(df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]),
            "com_conteudo_em_negociacao": len(df_completo[
                (df_completo["STAGE_ID"] == "C32:UC_GBPN8V") & 
                (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
            ]),
            "com_conteudo_fora_negociacao": len(df_completo[
                (df_completo["STAGE_ID"] != "C32:UC_GBPN8V") & 
                (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
            ])
        }
        
        # 5. Preparar dados detalhados para tabela (apenas com conteúdo)
        detalhamento = []
        for _, row in df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""].iterrows():
            detalhamento.append({
                "ID": row["ID"],
                "Título": row["TITLE"],
                "Data Criação": pd.to_datetime(row["DATE_CREATE"]).strftime("%d/%m/%Y"),
                "Responsável": row["ASSIGNED_BY_NAME"],
                "Etapa": row["STAGE_NAME"],
                "Status": "GEROU O LINK"
            })

        deals_sem_conteudo = df_completo[
            df_completo["UF_CRM_1738699062493"].isna() | 
            (df_completo["UF_CRM_1738699062493"].astype(str) == "")
        ]
        df_detalhamento = pd.DataFrame(detalhamento)

        # 7. Dos que têm conteúdo, separar por stage_id
        deals_com_link = deals_com_conteudo[deals_com_conteudo["STAGE_ID"] == "C32:UC_GBPN8V"]
        deals_sem_link = deals_com_conteudo[deals_com_conteudo["STAGE_ID"] != "C32:UC_GBPN8V"]
        # Ordenar por ID
        df_detalhamento = df_detalhamento.sort_values(by="ID", ascending=False)

        st.success("✅ Análise concluída com sucesso!")
        return metricas, df_detalhamento, df_completo

        return deals_com_link, deals_sem_link
    except Exception as e:
        st.error(f"Erro ao analisar dados: {str(e)}")
        return None
# Sidebar personalizada
st.sidebar.markdown("""
    <div class="sidebar-title">
        Navegação
    </div>
""", unsafe_allow_html=True)

# Sidebar para seleção de relatórios
tipo_relatorio = st.sidebar.selectbox(
    "Selecione o tipo de relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise de Deals", "Relatório 3"]
    "Selecione o Relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise Funil Bitrix24"]
)

# Lógica principal
if tipo_relatorio == "Status das Famílias":
    st.title("📊 Status das Famílias")
if tipo_relatorio == "Análise Funil Bitrix24":
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Análise Funil Bitrix24")
    with col2:
        if st.button("Atualizar"):
            st.rerun()

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
    # Container de status
    status_container = st.empty()
    
    try:
        # Iniciar análise com feedback detalhado
        status_container.info("Iniciando análise dos dados...")
        time.sleep(0.5)

        deals_data = consultar_bitrix("crm_deal", filtros_deal)
        deals_uf = consultar_bitrix("crm_deal_uf")
        # Consulta ao Bitrix24
        status_container.info("Consultando negócios no Bitrix24...")
        resultado = analisar_deals()

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
        if not resultado:
            status_container.error("Erro ao analisar os dados. Por favor, tente novamente.")
            st.stop()
        
        metricas, df_detalhamento, df_completo = resultado
        status_container.success("Dados carregados com sucesso!")
        
        # Métricas principais em cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Total de Negócios</div>
                    <div class='metric-value'>{metricas['total_negocios']}</div>
                    <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                        {metricas['categoria_name']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Gerou o Link</div>
                    <div class='metric-value'>{metricas['com_conteudo']}</div>
                    <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                        {((metricas['com_conteudo'] / metricas['total_negocios']) * 100):.1f}% do total
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>{metricas['stage_negociacao']}</div>
                    <div class='metric-value'>{metricas['total_stage_negociacao']}</div>
                    <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                        {((metricas['total_stage_negociacao'] / metricas['total_negocios']) * 100):.1f}% do total
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Tabela detalhada
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        st.subheader("Detalhamento dos Negócios")
        
        # Botões de download
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            csv = df_detalhamento.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name="negocios_bitrix24.csv",
                mime="text/csv"
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
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_detalhamento.to_excel(writer, sheet_name='Negócios', index=False)
                worksheet = writer.sheets['Negócios']
                for idx, col in enumerate(df_detalhamento.columns):
                    worksheet.set_column(idx, idx, max(len(col) + 2, df_detalhamento[col].astype(str).str.len().max() + 2))

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
            st.download_button(
                label="Baixar Excel",
                data=buffer.getvalue(),
                file_name="negocios_bitrix24.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
        
        # Tabela com dados
        st.markdown("""
            <style>
                /* Aumentar altura da tabela */
                .element-container iframe {
                    height: 600px !important;
                }
                
                /* Aumentar tamanho da fonte */
                .dataframe {
                    font-size: 14px !important;
                }
                
                /* Ajustar altura das linhas */
                .dataframe td {
                    padding: 12px !important;
                    line-height: 1.4 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Remover índice antes de criar o estilo
        df_detalhamento = df_detalhamento.reset_index(drop=True)
        
        st.dataframe(
            df_detalhamento.style.set_properties(**{
                'background-color': 'white',
                'color': '#000000',  # Preto
                'font-size': '14px',
                'font-weight': '400',
                'min-width': '100px'  # Largura mínima das colunas
            }).format({
                'ID': lambda x: f'{x:,.0f}'
            }),
            use_container_width=True,
            height=600  # Altura fixa da tabela
        )
    
    except Exception as e:
        status_container.error(f"Erro ao processar dados: {str(e)}")
        st.stop()
