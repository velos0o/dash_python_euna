import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from mysql.connector import Error
import requests
import json
import time
import io
from datetime import datetime, timedelta

# Configurações básicas do Streamlit
st.set_page_config(
    page_title="Eu na Europa - Sistema de Relatórios",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)
"""
Eu na Europa - Sistema de Relatórios
Versão consolidada para Streamlit Cloud
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from mysql.connector import Error
import requests
import json
import time
import io
import base64
from datetime import datetime, timedelta
from PIL import Image
from sqlalchemy import create_engine
from typing import Optional, Dict, Any, Union, Tuple

# Carregar e converter o logo para usar como ícone
def get_logo_base64():
    try:
        with open('assets/logo.svg', 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

# Configurações da página
logo_base64 = get_logo_base64()
st.set_page_config(
    page_title='Eu na Europa - Sistema de Relatórios',
    page_icon=f"data:image/svg+xml;base64,{logo_base64}" if logo_base64 else '🌍',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Constantes
PAYMENT_OPTIONS = {
    'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
    'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
    'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
    'D': 'Parcelamento em até 24 vezes fixas',
    'E': 'Cancelar',
    'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
    'Z': 'Análise especial'
}

PAYMENT_OPTIONS_COLORS = {
    'A': '#4CAF50',  # Verde
    'B': '#2196F3',  # Azul
    'C': '#9C27B0',  # Roxo
    'D': '#FF9800',  # Laranja
    'E': '#F44336',  # Vermelho
    'F': '#795548',  # Marrom
    'Z': '#607D8B'   # Cinza azulado
}

DATABASE_CONFIG = {
    'host': 'database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com',
    'port': 3306,
    'database': 'whatsapp_euna_data',
    'user': 'lucas',
    'password': 'a9!o98Q80$MM'
}

update-logo-and-app
# Configurar logo no sidebar
if logo_base64:  # Usando o mesmo logo_base64 carregado anteriormente
    st.sidebar.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem; padding: 1rem;'>
            <img src="data:image/svg+xml;base64,{logo_base64}" width="180" height="180" style="margin-bottom: 0.5rem;">
        </div>
    """, unsafe_allow_html=True)

# CSS personalizado
=======
feature/update-interface-streamlit
# Carregar o logo para usar como ícone
def get_base64_logo():
    try:
        with open('assets/logo.svg', 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa",
    page_icon="🇪🇺",  # Usando emoji da UE como ícone
    layout="wide",
    initial_sidebar_state="expanded")

# Carregar e exibir o logo
logo_base64 = get_base64_logo()
if logo_base64:
    # Logo no título
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <img src="data:image/svg+xml;base64,{logo_base64}" width="200" style="margin-bottom: 1rem;">
        </div>
    """, unsafe_allow_html=True)
    
    # Logo no sidebar com fundo branco
    st.sidebar.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <img src="data:image/svg+xml;base64,{logo_base64}" width="120" height="120" style="margin-bottom: 0.5rem;">
        </div>
    """, unsafe_allow_html=True)
)



# Injetar CSS personalizado

st.markdown("""
    <style>
        /* Estilo geral */
        .main {
            background-color: #ffffff;
            font-family: 'Montserrat', sans-serif;
            color: #333333;
        }
        
        /* Cores da Eu na Europa */
        :root {
            --primary-color: #003399;  /* Azul principal */
            --secondary-color: #FFD700;  /* Dourado */
            --text-color: #333333;
            --background-color: #ffffff;
            --accent-color: #1a73e8;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #ffffff;
            border-right: 1px solid #e9ecef;
        }
        
        .sidebar-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a73e8;
            margin: 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        /* Cards de métricas */
        .metric-card {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .metric-card.highlight {
            background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
            color: white;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        
        .metric-card.highlight .metric-label {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
        }
        
        .metric-card.highlight .metric-value {
            color: white;
            font-size: 3rem;
        }
        
        .metric-card.highlight .metric-description {
            color: rgba(255, 255, 255, 0.8);
        }
        
        /* Textos */
        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #1a73e8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a1f36;
            line-height: 1.2;
        }
        
        .metric-description {
            font-size: 0.813rem;
            color: #697386;
            margin-top: 0.5rem;
            line-height: 1.4;
        }
        
        /* Tabelas */
        .stDataFrame {
            border: 1px solid #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            background: white;
        }
        
        .stDataFrame th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #1a1f36;
            padding: 1rem;
            font-size: 0.875rem;
        }
        
        .stDataFrame td {
            padding: 0.875rem 1rem;
            color: #697386;
            font-size: 0.875rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        /* Botões */
        .stButton>button {
            background-color: #1a73e8;
            border: none;
            padding: 0.5rem 1rem;
            color: white;
            font-weight: 500;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            background-color: #1557b0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 0;
            color: #697386;
            font-weight: 500;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #1a73e8;
            border-bottom-color: #1a73e8;
        }
        
        /* Headers */
        h1 {
            color: #1a1f36;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 0;
        }
        
        h2 {
            color: #1a1f36;
            font-weight: 600;
            font-size: 1.5rem;
            margin: 2rem 0 1rem;
        }
        
        h3 {
            color: #1a1f36;
            font-weight: 600;
            font-size: 1.25rem;
            margin: 1.5rem 0 1rem;
        }
        
        /* Métricas no Sidebar */
        .sidebar .stMetric {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            margin-bottom: 0.5rem;
        }
        
        .sidebar .stMetric label {
            color: #1a73e8;
            font-size: 0.813rem;
            font-weight: 600;
        }
        
        .sidebar .stMetric .css-1wivap2 {
            color: #1a1f36;
            font-size: 1.25rem;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Classe Database
class Database:
    """Classe para gerenciar conexões com o banco de dados"""
    _instance = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    @property
    def engine(self):
        """Obtém ou cria a engine SQLAlchemy"""
        if self._engine is None:
            conn_str = (
                f"mysql+mysqlconnector://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            )
            self._engine = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
        return self._engine

    def get_connection(self) -> Optional[mysql.connector.MySQLConnection]:
        """Cria uma nova conexão com o banco de dados"""
        try:
            return mysql.connector.connect(**DATABASE_CONFIG)
        except Error as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
        """Executa uma query e retorna um DataFrame"""
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(query, conn, params=params)
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return None

    def execute_raw_query(self, query: str, params: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        """Executa uma query raw usando mysql.connector"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return None
        finally:
            if conn.is_connected():
                conn.close()

# Instância global do banco de dados
db = Database()

# Funções de serviço
@st.cache_data(ttl=300)
def get_total_preenchimentos() -> Optional[int]:
    """Obtém o total de formulários preenchidos"""
    query = """
    SELECT COUNT(DISTINCT id) as total
    FROM whatsapp_euna_data.euna_familias
    WHERE is_menor = 0
    AND isSpecial = 0
    AND hasTechnicalProblems = 0
    """
    df = db.execute_query(query)
    if df is not None and not df.empty:
        return int(df['total'].iloc[0])
    return None

@st.cache_data(ttl=300)
def get_familias_status() -> Optional[pd.DataFrame]:
    """Obtém o status das famílias com cache"""
    query = """
    WITH FamiliaDetalhes AS (
        SELECT
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
            SUM(CASE WHEN e.paymentOption = 'Z' THEN 1 ELSE 0 END) AS Z,
            SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Z') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
            SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
            COUNT(DISTINCT e.id) AS Requerentes_Preencheram,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia
             AND f2.is_conjuge = 0
             AND f2.is_italiano = 0
             AND f2.is_menor = 0) AS Requerentes_Maiores,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia
             AND f2.is_menor = 1) AS Requerentes_Menores,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia) AS Total_Banco,
            MIN(e.createdAt) as Primeiro_Preenchimento,
            MAX(e.createdAt) as Ultimo_Preenchimento
        FROM whatsapp_euna_data.euna_familias e
        LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0 AND e.isSpecial = 0 AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia
    ),
    TotalGeral AS (
        SELECT
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(A) AS A,
            SUM(B) AS B,
            SUM(C) AS C,
            SUM(D) AS D,
            SUM(E) AS E,
            SUM(F) AS F,
            SUM(Z) AS Z,
            SUM(Requerentes_Continuar) AS Requerentes_Continuar,
            SUM(Requerentes_Cancelar) AS Requerentes_Cancelar,
            SUM(Sem_Opcao) AS Sem_Opcao,
            SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
            SUM(Requerentes_Maiores) AS Requerentes_Maiores,
            SUM(Requerentes_Menores) AS Requerentes_Menores,
            SUM(Total_Banco) AS Total_Banco,
            MIN(Primeiro_Preenchimento) as Primeiro_Preenchimento,
            MAX(Ultimo_Preenchimento) as Ultimo_Preenchimento
        FROM FamiliaDetalhes
    )
    SELECT * FROM FamiliaDetalhes
    UNION ALL
    SELECT * FROM TotalGeral
    ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, Nome_Familia;
    """
    return db.execute_query(query)

@st.cache_data(ttl=300)
def get_option_details(option: str) -> Optional[pd.DataFrame]:
    """Obtém detalhes de uma opção de pagamento"""
    query = """
    SELECT
        e.idfamilia,
        e.nome_completo,
        e.telefone,
        e.`e-mail` as email,
        e.birthdate,
        e.paymentOption,
        e.createdAt,
        e.is_menor,
        e.isSpecial,
        e.hasTechnicalProblems,
        f.nome_familia,
        TIMESTAMPDIFF(YEAR, e.birthdate, CURDATE()) as idade
    FROM whatsapp_euna_data.euna_familias e
    LEFT JOIN whatsapp_euna_data.familias f
        ON TRIM(e.idfamilia) = TRIM(f.unique_id)
    WHERE e.paymentOption = %s
    AND e.is_menor = 0
    AND e.isSpecial = 0
    AND e.hasTechnicalProblems = 0
    ORDER BY e.createdAt DESC
    """
    df = db.execute_raw_query(query, (option,))
    if df is not None:
        # Formatar datas
        df['createdAt'] = pd.to_datetime(df['createdAt']).dt.strftime('%d/%m/%Y %H:%M')
        df['birthdate'] = pd.to_datetime(df['birthdate']).dt.strftime('%d/%m/%Y')

        # Formatar status
        df['Status'] = df.apply(lambda x: [
            'Menor de idade' if x['is_menor'] else None,
            'Especial' if x['isSpecial'] else None,
            'Problemas Técnicos' if x['hasTechnicalProblems'] else None
        ], axis=1).apply(lambda x: ', '.join([s for s in x if s]))
    return df

@st.cache_data(ttl=300)
def get_dados_grafico() -> Optional[pd.DataFrame]:
    """Obtém dados para o gráfico de evolução temporal"""
    query = """
    SELECT
        DATE(createdAt) as data,
        HOUR(createdAt) as hora,
        COUNT(DISTINCT id) as total_ids
    FROM whatsapp_euna_data.euna_familias
    WHERE is_menor = 0 AND isSpecial = 0 AND hasTechnicalProblems = 0
    GROUP BY DATE(createdAt), HOUR(createdAt)
    ORDER BY data, hora
    """
    return db.execute_query(query)

@st.cache_data(ttl=300)
def filter_familias(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """Filtra famílias com cache"""
    if not search_term:
        return df

    # Converter para minúsculas para busca case-insensitive
    search_term = search_term.lower()
    mask = df['Nome_Familia'].str.lower().str.contains(search_term, na=False)
    return df[mask]

def clear_cache():
    """Limpa todo o cache"""
    get_familias_status.clear()
    get_option_details.clear()
    get_dados_grafico.clear()
    filter_familias.clear()
    get_total_preenchimentos.clear()

# Inicializar variáveis de sessão
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

if 'cache_status' not in st.session_state:
    st.session_state.cache_status = {
        'last_update': datetime.now(),
        'cache_hits': 0,
        'requests': 0
    }

# Atualizar métricas
st.session_state.cache_status['requests'] += 1
execution_time = time.time() - st.session_state.start_time

# Converter para fuso horário de São Paulo
import pytz
sp_tz = pytz.timezone('America/Sao_Paulo')
last_update = datetime.now(sp_tz)
st.session_state.cache_status['last_update'] = last_update

# Formatar tempo de execução
execution_time_ms = execution_time * 1000  # Converter para milissegundos

# Sidebar de navegação
st.sidebar.markdown("""
    <div class="sidebar-title">
        Navegação
    </div>
""", unsafe_allow_html=True)

tipo_relatorio = st.sidebar.selectbox(
    "Selecione o Relatório",
    ["Selecione uma opção", "Status das Famílias", "Análise Funil Bitrix24"]
)

# Métricas de performance no sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div class="sidebar-title">
        Performance
    </div>
""", unsafe_allow_html=True)

st.sidebar.metric("Cache Hits", st.session_state.cache_status['cache_hits'])
st.sidebar.metric("Tempo de Execução", f"{execution_time_ms:.0f}ms")
st.sidebar.metric("Última Atualização", st.session_state.cache_status['last_update'].strftime("%H:%M:%S"))
st.sidebar.metric("Tempo de Cache", "5 minutos")

def show_main_metrics(df: pd.DataFrame):
    """Exibe métricas principais"""
    total_row = df[df['Nome_Familia'] == 'Total'].iloc[0]
    total_preenchimentos = get_total_preenchimentos()

    # Primeiro, mostrar total de preenchimentos em destaque
    st.markdown(f"""
        <div class='metric-card highlight'>
            <div class='metric-label'>Total de Preenchimentos</div>
            <div class='metric-value'>{total_preenchimentos or 0}</div>
            <div class='metric-description'>
                Formulários preenchidos até o momento
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Demais métricas em linha
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Total de Famílias</div>
                <div class='metric-value'>{len(df[df['Nome_Familia'] != 'Total'])}</div>
                <div class='metric-description'>
                    Famílias cadastradas
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Requerentes Continuar</div>
                <div class='metric-value'>{int(total_row['Requerentes_Continuar'])}</div>
                <div class='metric-description'>
                    Opções A, B, C, D, F e Z
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Requerentes Cancelar</div>
                <div class='metric-value'>{int(total_row['Requerentes_Cancelar'])}</div>
                <div class='metric-description'>
                    Apenas opção E
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Sem Opção</div>
                <div class='metric-value'>{int(total_row['Sem_Opcao'])}</div>
                <div class='metric-description'>
                    Aguardando escolha
                </div>
            </div>
        """, unsafe_allow_html=True)

def show_payment_options(df: pd.DataFrame):
    """Exibe distribuição das opções de pagamento"""
    st.subheader("Distribuição por Opção de Pagamento")

    total_row = df[df['Nome_Familia'] == 'Total'].iloc[0]
    total_preenchidos = total_row[['A', 'B', 'C', 'D', 'E', 'F', 'Z']].sum()

    cols = st.columns(7)
    for option, col in zip(['A', 'B', 'C', 'D', 'E', 'F', 'Z'], cols):
        valor = total_row[option]
        percentual = (valor / total_preenchidos * 100) if total_preenchidos > 0 else 0

        with col:
            st.markdown(f"""
                <div class='metric-card' style='border-left: 4px solid {PAYMENT_OPTIONS_COLORS[option]};'>
                    <div class='metric-label'>Opção {option}</div>
                    <div class='metric-value'>{int(valor)}</div>
                    <div class='metric-description' title="{PAYMENT_OPTIONS[option]}">
                        {PAYMENT_OPTIONS[option][:30]}...
                    </div>
                    <div class='metric-percentage'>
                        {percentual:.1f}% do total
                    </div>
                </div>
            """, unsafe_allow_html=True)

def show_timeline_chart(df: pd.DataFrame):
    """Exibe gráfico de evolução temporal"""
    st.subheader("Evolução do Preenchimento")

    # Preparar dados
    df['datetime'] = pd.to_datetime(df['data']) + pd.to_timedelta(df['hora'], unit='h')
    df['hora_formatada'] = df['datetime'].dt.strftime('%H:00')
    df['data_formatada'] = df['datetime'].dt.strftime('%d/%m/%Y')
    df['dia_semana'] = df['datetime'].dt.strftime('%A')  # Nome do dia da semana

    # Tradução dos dias da semana
    dias_semana = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    df['dia_semana'] = df['dia_semana'].map(dias_semana)

    # Agrupar por diferentes períodos
    df_dia = df.groupby('data_formatada')['total_ids'].sum().reset_index()
    df_hora = df.groupby('hora')['total_ids'].sum().reset_index()
    df_dia_semana = df.groupby('dia_semana')['total_ids'].sum().reset_index()

    # Encontrar períodos mais ativos
    hora_mais_ativa = df_hora.loc[df_hora['total_ids'].idxmax()]
    dia_mais_ativo = df_dia.loc[df_dia['total_ids'].idxmax()]
    dia_semana_mais_ativo = df_dia_semana.loc[df_dia_semana['total_ids'].idxmax()]

    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Horário Mais Ativo",
            f"{int(hora_mais_ativa['hora']):02d}:00",
            f"{int(hora_mais_ativa['total_ids'])} preenchimentos"
        )
    with col2:
        st.metric(
            "Dia Mais Ativo",
            dia_mais_ativo['data_formatada'],
            f"{int(dia_mais_ativo['total_ids'])} preenchimentos"
        )
    with col3:
        st.metric(
            "Dia da Semana Mais Ativo",
            dia_semana_mais_ativo['dia_semana'],
            f"{int(dia_semana_mais_ativo['total_ids'])} preenchimentos"
        )

    # Criar visualizações
    tab1, tab2, tab3 = st.tabs(["Por Hora", "Por Dia", "Por Dia da Semana"])

    with tab1:
        # Gráfico por hora
        fig_hora = px.bar(
            df_hora,
            x='hora',
            y='total_ids',
            title='Distribuição por Hora do Dia',
            labels={
                'hora': 'Hora',
                'total_ids': 'Total de Preenchimentos'
            }
        )

        # Formatar eixo X para mostrar horas corretamente
        fig_hora.update_xaxes(
            ticktext=[f"{h:02d}:00" for h in range(24)],
            tickvals=list(range(24))
        )

        # Atualizar layout
        fig_hora.update_layout(
            showlegend=False,
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='#eee',
                title=dict(
                    text='Total de Preenchimentos',
                    font=dict(size=14)
                )
            ),
            xaxis=dict(
                title=dict(
                    text='Hora do Dia',
                    font=dict(size=14)
                )
            )
        )

        st.plotly_chart(fig_hora, use_container_width=True)

    with tab2:
        # Gráfico por dia
        fig_dia = px.bar(
            df_dia,
            x='data_formatada',
            y='total_ids',
            title='Distribuição por Dia',
            labels={
                'data_formatada': 'Data',
                'total_ids': 'Total de Preenchimentos'
            }
        )

        fig_dia.update_xaxes(tickangle=45)
        st.plotly_chart(fig_dia, use_container_width=True)

    with tab3:
        # Gráfico por dia da semana
        fig_semana = px.bar(
            df_dia_semana,
            x='dia_semana',
            y='total_ids',
            title='Distribuição por Dia da Semana',
            labels={
                'dia_semana': 'Dia da Semana',
                'total_ids': 'Total de Preenchimentos'
            }
        )

        # Ordenar dias da semana corretamente
        ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        fig_semana.update_xaxes(categoryorder='array', categoryarray=ordem_dias)

        st.plotly_chart(fig_semana, use_container_width=True)

def show_detailed_table(df: pd.DataFrame):
    """Exibe tabela detalhada"""
    st.subheader("Detalhamento por Família")

    # Campo de busca
    search = st.text_input(
        "🔍 Buscar família",
        help="Digite o nome da família para filtrar",
        placeholder="Ex: Silva, Santos..."
    )

    # Remover linha de total e aplicar filtro
    df_display = df[df['Nome_Familia'] != 'Total'].copy()
    if search:
        df_display = filter_familias(df_display, search)
        if df_display.empty:
            st.warning("Nenhuma família encontrada com o termo de busca.")
            return
        st.success(f"Encontradas {len(df_display)} famílias.")

    # Dividir em duas tabelas
    tab1, tab2 = st.tabs(["Opções de Pagamento", "Resumo"])

    with tab1:
        # Tabela de opções
        columns_options = {
            'Nome_Familia': 'Família',
            'A': 'A',
            'B': 'B',
            'C': 'C',
            'D': 'D',
            'E': 'E',
            'F': 'F',
            'Z': 'Z'
        }

        df_options = df_display[columns_options.keys()].rename(columns=columns_options)

        # Estilo mais sutil
        styled_options = df_options.style\
            .format({col: '{:,.0f}' for col in df_options.columns if col != 'Família'})\
            .set_properties(**{
                'background-color': 'white',
                'color': '#666',
                'font-size': '13px',
                'border': '1px solid #eee'
            })\
            .apply(lambda x: ['font-weight: bold' if v > 0 else '' for v in x],
                   subset=[col for col in df_options.columns if col != 'Família'])

        st.dataframe(
            styled_options,
            use_container_width=True,
            height=300
        )

    with tab2:
        # Tabela de resumo
        columns_summary = {
            'Nome_Familia': 'Família',
            'Requerentes_Continuar': 'Continuar',
            'Requerentes_Cancelar': 'Cancelar',
            'Total_Banco': 'Total'
        }

        df_summary = df_display[columns_summary.keys()].rename(columns=columns_summary)

        styled_summary = df_summary.style\
            .format({col: '{:,.0f}' for col in df_summary.columns if col != 'Família'})\
            .set_properties(**{
                'background-color': 'white',
                'color': '#333',
                'font-size': '13px',
                'border': '1px solid #eee'
            })\
            .apply(lambda x: ['font-weight: bold' if v > 0 else '' for v in x],
                   subset=[col for col in df_summary.columns if col != 'Família'])

        st.dataframe(
            styled_summary,
            use_container_width=True,
            height=300
        )

def show_option_details(option: str):
    """Exibe detalhes de uma opção de pagamento"""
    df = get_option_details(option)
    if df is not None and not df.empty:
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["Visão Geral", "Por Família", "Download"])

        with tab1:
            st.markdown(f"""
                ### Detalhes da Opção {option}
                <div style='font-size: 0.9rem; color: {PAYMENT_OPTIONS_COLORS[option]}; margin-bottom: 1rem;'>
                    {PAYMENT_OPTIONS[option]}
                </div>
            """, unsafe_allow_html=True)

            # Métricas da opção
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Pessoas", len(df))
            with col2:
                st.metric("Famílias Diferentes", df['idfamilia'].nunique())
            with col3:
                st.metric("Média por Família", f"{len(df)/df['idfamilia'].nunique():.1f}")

            # Tabela principal
            df_display = df.rename(columns={
                'nome_completo': 'Nome',
                'telefone': 'Telefone',
                'nome_familia': 'Família',
                'createdAt': 'Data'
            })

            st.dataframe(
                df_display[['Nome', 'Telefone', 'Família', 'Data']],
                use_container_width=True
            )

        with tab2:
            st.markdown("### Análise por Família")

            # Campo de busca
            search = st.text_input(
                "🔍 Buscar família",
                help="Digite o nome da família para filtrar",
                placeholder="Ex: Silva, Santos...",
                key=f"search_familia_{option}"  # Key única por opção
            )

            # Agrupar por família com mais detalhes
            df_familia = df.groupby('nome_familia').agg({
                'nome_completo': 'count',
                'idade': ['mean', 'min', 'max'],
                'createdAt': ['min', 'max'],
                'email': 'nunique',
                'telefone': 'nunique'
            }).reset_index()

            # Renomear colunas
            df_familia.columns = [
                'Família',
                'Total Membros',
                'Idade Média',
                'Idade Mínima',
                'Idade Máxima',
                'Primeiro Preenchimento',
                'Último Preenchimento',
                'Emails Únicos',
                'Telefones Únicos'
            ]

            # Formatar dados
            df_familia['Idade Média'] = df_familia['Idade Média'].round(1)
            df_familia['Primeiro Preenchimento'] = pd.to_datetime(df_familia['Primeiro Preenchimento']).dt.strftime('%d/%m/%Y %H:%M')
            df_familia['Último Preenchimento'] = pd.to_datetime(df_familia['Último Preenchimento']).dt.strftime('%d/%m/%Y %H:%M')

            # Aplicar filtro de busca
            if search:
                df_familia = df_familia[df_familia['Família'].str.contains(search, case=False, na=False)]
                if df_familia.empty:
                    st.warning("Nenhuma família encontrada com o termo de busca.")
                    return
                st.success(f"Encontradas {len(df_familia)} famílias.")

            # Criar visualizações
            col1, col2 = st.columns([2, 1])

            with col1:
                # Gráfico de barras por família
                fig = px.bar(
                    df_familia,
                    x='Família',
                    y='Total Membros',
                    title=f'Distribuição da Opção {option} por Família',
                    color='Idade Média',
                    color_continuous_scale='RdYlBu',
                    hover_data=['Idade Mínima', 'Idade Máxima', 'Emails Únicos']
                )

                fig.update_layout(
                    showlegend=True,
                    plot_bgcolor='white',
                    yaxis=dict(
                        title='Total de Membros',
                        gridcolor='#eee'
                    ),
                    xaxis=dict(
                        title='Família',
                        tickangle=45
                    ),
                    coloraxis_colorbar=dict(
                        title='Idade Média'
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Métricas resumidas
                st.metric(
                    "Média de Membros por Família",
                    f"{df_familia['Total Membros'].mean():.1f}",
                    help="Média de membros por família"
                )
                st.metric(
                    "Idade Média Geral",
                    f"{df_familia['Idade Média'].mean():.1f} anos",
                    help="Média de idade considerando todas as famílias"
                )
                st.metric(
                    "Total de Emails Únicos",
                    df_familia['Emails Únicos'].sum(),
                    help="Total de emails únicos registrados"
                )

            # Tabela detalhada por família
            st.markdown("#### Detalhamento por Família")
            st.dataframe(
                df_familia.style.format({
                    'Idade Média': '{:.1f}',
                    'Idade Mínima': '{:.0f}',
                    'Idade Máxima': '{:.0f}'
                }),
                use_container_width=True
            )

            # Detalhes dos membros
            if len(df_familia) == 1:
                familia_selecionada = df_familia['Família'].iloc[0]
                st.markdown(f"#### Membros da Família {familia_selecionada}")

                membros = df[df['nome_familia'] == familia_selecionada].copy()
                membros = membros[[
                    'nome_completo', 'idade', 'email', 'telefone',
                    'birthdate', 'createdAt'
                ]].rename(columns={
                    'nome_completo': 'Nome',
                    'idade': 'Idade',
                    'email': 'Email',
                    'telefone': 'Telefone',
                    'birthdate': 'Data de Nascimento',
                    'createdAt': 'Data de Preenchimento'
                })

                st.dataframe(membros, use_container_width=True)

        with tab3:
            st.markdown("### Download dos Dados")

            # Preparar dados para download
            df_download = df.rename(columns={
                'nome_completo': 'Nome',
                'telefone': 'Telefone',
                'nome_familia': 'Família',
                'createdAt': 'Data',
                'idfamilia': 'ID Família'
            })

            # Botões de download
            col1, col2 = st.columns(2)
            with col1:
                csv = df_download.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"opcao_{option}.csv",
                    mime="text/csv"
                )

            with col2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_download.to_excel(writer, sheet_name='Dados', index=False)
                    df_familia.to_excel(writer, sheet_name='Por Família', index=False)

                st.download_button(
                    label="📊 Baixar Excel",
                    data=buffer.getvalue(),
                    file_name=f"opcao_{option}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info(f"Nenhum detalhe encontrado para a opção {option}")

def render_dashboard():
    """Renderiza o dashboard completo"""
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Status das Famílias")
    with col2:
        if st.button("🔄 Atualizar"):
            clear_cache()
            st.rerun()

    # Iniciar análise
    start_time = time.time()

    try:
        # Carregar dados
        with st.spinner("Carregando dados..."):
            df_status = get_familias_status()
            df_timeline = get_dados_grafico()

        if df_status is not None:
            # Mostrar componentes
            st.markdown("<hr>", unsafe_allow_html=True)

            show_main_metrics(df_status)
            st.markdown("<hr>", unsafe_allow_html=True)

            show_payment_options(df_status)
            st.markdown("<hr>", unsafe_allow_html=True)

            if df_timeline is not None:
                show_timeline_chart(df_timeline)
                st.markdown("<hr>", unsafe_allow_html=True)

            show_detailed_table(df_status)
            st.markdown("<hr>", unsafe_allow_html=True)

            # Detalhes por opção
            st.markdown("### 🔍 Explorar Opção")
            option = st.selectbox(
                "Selecione uma opção para ver detalhes",
                options=list(PAYMENT_OPTIONS.keys()),
                format_func=lambda x: f"{x} - {PAYMENT_OPTIONS[x]}"
            )
            if option:
                show_option_details(option)
        else:
            st.error("Erro ao carregar dados. Tente novamente mais tarde.")

    except Exception as e:
update-logo-and-app
        st.error(f"Erro inesperado: {str(e)}")
    finally:
        # Mostrar tempo de carregamento
        end_time = time.time()
        st.sidebar.metric(
            "Tempo de Carregamento",
            f"{(end_time - start_time):.2f}s",
            help="Tempo total de carregamento da página"
        )

# Função principal
def main():
    try:
        if tipo_relatorio == "Status das Famílias":
            render_dashboard()
        elif tipo_relatorio == "Análise Funil Bitrix24":
            st.info("Módulo em desenvolvimento")
        elif tipo_relatorio == "Selecione uma opção":
            st.info("👈 Selecione um relatório no menu lateral para começar")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")

if __name__ == "__main__":
    main()
=======
        status_container.error(f"Erro ao processar dados: {str(e)}")
        st.stop()
# Carregar o logo para usar como ícone
def get_base64_logo():
    try:
        with open('assets/logo.svg', 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
        return None

# Configuração da página
st.set_page_config(
    page_title="Eu na Europa",
    page_icon="🇪🇺",  # Usando emoji da UE como ícone
    layout="wide",
    initial_sidebar_state="expanded")

# Carregar e exibir o logo
logo_base64 = get_base64_logo()
if logo_base64:
    # Logo no título
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <img src="data:image/svg+xml;base64,{logo_base64}" width="200" style="margin-bottom: 1rem;">
        </div>
    """, unsafe_allow_html=True)
    
    # Logo no sidebar com fundo branco
    st.sidebar.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <img src="data:image/svg+xml;base64,{logo_base64}" width="120" height="120" style="margin-bottom: 0.5rem;">
        </div>
    """, unsafe_allow_html=True)
main
