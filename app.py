import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import requests
import json
import time
import io
from datetime import datetime, timedelta

# Cores do tema (Itália e União Europeia)
COLORS = {
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
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def consultar_bitrix(table, filtros=None, max_retries=3, timeout=30):
    """Função para consultar Bitrix24 com retry e timeout"""
    for attempt in range(max_retries):
        try:
            url = f"{BITRIX_BASE_URL}?token={BITRIX_TOKEN}&table={table}"
            
            if filtros:
                response = requests.post(url, json=filtros, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)
            
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
            ]],
            "select": [
                "ID", "TITLE", "DATE_CREATE", "ASSIGNED_BY_NAME", 
                "STAGE_ID", "STAGE_NAME", "CATEGORY_NAME"
            ]
        }
        
        deals_data = consultar_bitrix("crm_deal", filtros_deal)
        
        if not deals_data:
            st.error("Não foi possível obter os dados de negócios")
            return None
        
        # Converter para DataFrame
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        
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
        
        deals_uf_data = consultar_bitrix("crm_deal_uf", filtros_uf)
        
        if not deals_uf_data:
            st.error("Não foi possível obter os dados complementares")
            return None
            
        deals_uf_df = pd.DataFrame(deals_uf_data[1:], columns=deals_uf_data[0])
        
        # 3. Mesclar os dataframes
        df_completo = pd.merge(
            deals_df,
            deals_uf_df[["DEAL_ID", "UF_CRM_1738699062493"]],
            left_on="ID",
            right_on="DEAL_ID",
            how="left"
        )
        
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
        
        df_detalhamento = pd.DataFrame(detalhamento)
        
        # Ordenar por ID
        df_detalhamento = df_detalhamento.sort_values(by="ID", ascending=False)
        
        return metricas, df_detalhamento, df_completo
        
    except Exception as e:
        st.error(f"Erro ao analisar dados: {str(e)}")
        return None

# Sidebar personalizada
st.sidebar.markdown("""
    <div class="sidebar-title">
        Navegação
    </div>
""", unsafe_allow_html=True)

tipo_relatorio = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise Funil Bitrix24"]
)

# Lógica principal
if tipo_relatorio == "Análise Funil Bitrix24":
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Análise Funil Bitrix24")
    with col2:
        if st.button("Atualizar"):
            st.rerun()
    
    # Container de status
    status_container = st.empty()
    
    try:
        # Iniciar análise com feedback detalhado
        status_container.info("Iniciando análise dos dados...")
        time.sleep(0.5)
        
        # Consulta ao Bitrix24
        status_container.info("Consultando negócios no Bitrix24...")
        resultado = analisar_deals()
        
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
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_detalhamento.to_excel(writer, sheet_name='Negócios', index=False)
                worksheet = writer.sheets['Negócios']
                for idx, col in enumerate(df_detalhamento.columns):
                    worksheet.set_column(idx, idx, max(len(col) + 2, df_detalhamento[col].astype(str).str.len().max() + 2))
            
            st.download_button(
                label="Baixar Excel",
                data=buffer.getvalue(),
                file_name="negocios_bitrix24.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
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