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

# Constantes de descrição das opções
PAYMENT_OPTIONS_DESCRIPTIONS = {
    'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
    'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
    'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
    'D': 'Parcelamento em até 24 vezes fixas',
    'E': 'Cancelar',
    'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
    'Z': 'Análise especial'
}

# Cores para cada opção
PAYMENT_OPTIONS_COLORS = {
    'A': '#4CAF50',  # Verde
    'B': '#2196F3',  # Azul
    'C': '#9C27B0',  # Roxo
    'D': '#FF9800',  # Laranja
    'E': '#F44336',  # Vermelho
    'F': '#795548',  # Marrom
    'Z': '#607D8B'   # Cinza azulado
}

@st.cache_data(ttl=300)
def get_option_details(option: str) -> pd.DataFrame:
    """Busca detalhes de uma opção de pagamento"""
    connection = get_database_connection()
    if connection is None:
        return pd.DataFrame()

    query = """
    SELECT 
        e.idfamilia,
        e.nome_completo,
        e.telefone,
        f.nome_familia,
        e.paymentOption,
        e.createdAt
    FROM whatsapp_euna_data.euna_familias e
    LEFT JOIN whatsapp_euna_data.familias f 
        ON TRIM(e.idfamilia) = TRIM(f.unique_id)
    WHERE e.paymentOption = %s
    AND e.is_menor = 0 
    AND e.isSpecial = 0 
    AND e.hasTechnicalProblems = 0
    ORDER BY e.createdAt DESC
    """
    
    try:
        df = pd.read_sql(query, connection, params=[option])
        df['createdAt'] = pd.to_datetime(df['createdAt']).dt.strftime('%d/%m/%Y %H:%M')
        return df
    except Exception as e:
        st.error(f"Erro ao buscar detalhes: {e}")
        return pd.DataFrame()
    finally:
        if connection.is_connected():
            connection.close()

def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host='database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com',
            port=3306,
            database='whatsapp_euna_data',
            user='lucas',
            password='a9!o98Q80$MM'
        )
        return connection
    except Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_dados_grafico():
    """Obtém dados do gráfico com cache"""
    connection = get_database_connection()
    if connection is None:
        return None

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

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query do gráfico: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_familias_status():
    """Obtém status das famílias com cache"""
    connection = get_database_connection()
    if connection is None:
        return None

    # Query principal
    query = """
    WITH FamiliaDetalhes AS (
        -- Primeiro, obtemos os dados por família
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
            SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
            SUM(CASE WHEN e.paymentOption IN ('E','Z') THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
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
             WHERE f2.familia = e.idfamilia) AS Total_Banco
        FROM whatsapp_euna_data.euna_familias e
        LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0 AND e.isSpecial = 0 AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia
    ),
    TotalGeral AS (
        -- Depois, calculamos o total geral
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
            SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
            SUM(Requerentes_Maiores) AS Requerentes_Maiores,
            SUM(Requerentes_Menores) AS Requerentes_Menores,
            SUM(Total_Banco) AS Total_Banco
        FROM FamiliaDetalhes
    )
    -- União dos resultados
    SELECT * FROM FamiliaDetalhes
    UNION ALL
    SELECT * FROM TotalGeral
    ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, ID_Familia;
    """

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def show_status_familias():
    """Exibe dashboard de status das famílias"""
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Status das Famílias")
    with col2:
        if st.button("Atualizar", help="Atualiza os dados do dashboard"):
            st.cache_data.clear()
            st.rerun()
    
    # Mostrar status do cache
    if 'cache_status' not in st.session_state:
        st.session_state.cache_status = {
            'last_update': datetime.now(),
            'cache_hits': 0
        }
    
    # Atualizar contagem de cache hits
    if st.session_state.cache_status['last_update'] < datetime.now() - timedelta(minutes=5):
        st.session_state.cache_status['last_update'] = datetime.now()
    else:
        st.session_state.cache_status['cache_hits'] += 1
    
    # Container de status
    status_container = st.empty()
    
    # Métricas de performance
    start_time = time.time()
    
    try:
        # Iniciar análise com feedback
        status_container.info("Iniciando análise dos dados...")
        
        # Mostrar métricas de cache
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Cache Hits",
                st.session_state.cache_status['cache_hits'],
                help="Número de vezes que os dados foram servidos do cache"
            )
        with col2:
            last_update = st.session_state.cache_status['last_update']
            st.metric(
                "Última Atualização",
                last_update.strftime("%H:%M:%S"),
                help="Horário da última atualização dos dados"
            )
        with col3:
            st.metric(
                "Tempo de Carregamento",
                "Calculando...",
                help="Tempo total de carregamento da página"
            )
        
        # Obtém os dados
        status_container.info("Consultando banco de dados...")
        df_status = get_familias_status()

        if df_status is not None:
            status_container.success("Dados carregados com sucesso!")
            
            # Métricas gerais em cards
            total_row = df_status[df_status['Nome_Familia'] == 'Total'].iloc[0]
            
            # Primeira linha de métricas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Total de Famílias</div>
                        <div class='metric-value'>{len(df_status[df_status['Nome_Familia'] != 'Total'])}</div>
                        <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                            Contagem de ID_Familia
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Requerentes Continuar</div>
                        <div class='metric-value'>{int(total_row['Requerentes_Continuar'])}</div>
                        <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                            Escolheram opções A, B, C ou D
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Requerentes Cancelar</div>
                        <div class='metric-value'>{int(total_row['Requerentes_Cancelar'])}</div>
                        <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                            Escolheram opção E
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Distribuição por opção de pagamento
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.subheader("Distribuição por Opção de Pagamento")
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            opcoes = ['A', 'B', 'C', 'D', 'E', 'F', 'Z']
            colunas = [col1, col2, col3, col4, col5, col6, col7]
            
            # Descrições das opções
            descricoes = {
                'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
                'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
                'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
                'D': 'Parcelamento em até 24 vezes fixas',
                'E': 'Cancelar',
                'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
                'Z': 'Análise especial'
            }
            
            total_requerentes = total_row['Total_Banco']
            
            for opcao, col in zip(opcoes, colunas):
                with col:
                    valor = total_row[opcao]
                    percentual = (valor / total_requerentes * 100) if total_requerentes > 0 else 0
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>Opção {opcao}</div>
                            <div class='metric-value'>{int(valor)}</div>
                            <div class='metric-description' title="{descricoes[opcao]}">
                                {descricoes[opcao][:30]}...
                            </div>
                            <div class='metric-percentage'>
                                {percentual:.1f}% do total
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            # Tabela detalhada
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.subheader("Detalhamento por Família")
            
            # Preparar dados para a tabela
            df_display = df_status.copy()
            
            # Criar matriz de dados
            matriz_data = []
            total_row = df_display[df_display['Nome_Familia'] == 'Total'].iloc[0]
            
            for _, row in df_display[df_display['Nome_Familia'] != 'Total'].iterrows():
                linha = {
                    'Família': row['Nome_Familia'],
                    'A': int(row['A']),
                    'B': int(row['B']),
                    'C': int(row['C']),
                    'D': int(row['D']),
                    'E': int(row['E']),
                    'F': int(row['F']),
                    'Z': int(row['Z']),
                    'Requerentes Continuar': int(row['Requerentes_Continuar']),
                    'Requerentes Cancelar': int(row['Requerentes_Cancelar']),
                    'Requerentes Maiores': int(row['Requerentes_Maiores']),
                    'Requerentes Menores': int(row['Requerentes_Menores']),
                    'Total de Requerentes': int(row['Total_Banco'])
                }
                matriz_data.append(linha)
            
            # Adicionar linha de totais
            matriz_data.append({
                'Família': 'Total',
                'A': int(total_row['A']),
                'B': int(total_row['B']),
                'C': int(total_row['C']),
                'D': int(total_row['D']),
                'E': int(total_row['E']),
                'F': int(total_row['F']),
                'Z': int(total_row['Z']),
                'Requerentes Continuar': int(total_row['Requerentes_Continuar']),
                'Requerentes Cancelar': int(total_row['Requerentes_Cancelar']),
                'Requerentes Maiores': int(total_row['Requerentes_Maiores']),
                'Requerentes Menores': int(total_row['Requerentes_Menores']),
                'Total de Requerentes': int(total_row['Total_Banco'])
            })
            
            # Converter para DataFrame
            df_display = pd.DataFrame(matriz_data)
            
            # Exibir tabela
            st.dataframe(
                df_display.style.set_properties(**{
                    'background-color': 'white',
                    'color': '#000000',
                    'font-size': '14px',
                    'font-weight': '400',
                    'min-width': '100px'
                }).format({
                    'A': '{:,.0f}',
                    'B': '{:,.0f}',
                    'C': '{:,.0f}',
                    'D': '{:,.0f}',
                    'E': '{:,.0f}',
                    'F': '{:,.0f}',
                    'Z': '{:,.0f}',
                    'Requerentes Continuar': '{:,.0f}',
                    'Requerentes Cancelar': '{:,.0f}',
                    'Requerentes Maiores': '{:,.0f}',
                    'Requerentes Menores': '{:,.0f}',
                    'Total de Requerentes': '{:,.0f}'
                }),
                use_container_width=True,
                height=400
            )

            # Campo de busca
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.markdown("### 🔍 Buscar Família")
            familia_busca = st.text_input(
                "Digite o nome da família",
                help="Pesquise pelo nome da família"
            )
            
            if familia_busca:
                filtered_df = df_status[
                    df_status['Nome_Familia'].str.contains(familia_busca, case=False, na=False)
                ]
                
                if not filtered_df.empty:
                    for _, row in filtered_df.iterrows():
                        with st.expander(f"📋 {row['Nome_Familia']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                total = row['Requerentes_Maiores'] + row['Requerentes_Menores']
                                st.metric("Total de Requerentes", int(total))
                                st.metric("Requerentes Maiores", int(row['Requerentes_Maiores']))
                                st.metric("Requerentes Menores", int(row['Requerentes_Menores']))
                            
                            with col2:
                                for opt in ['A', 'B', 'C', 'D', 'E', 'F', 'Z']:
                                    if row[opt] > 0:
                                        st.metric(
                                            f"Opção {opt}",
                                            int(row[opt]),
                                            help=PAYMENT_OPTIONS_DESCRIPTIONS[opt]
                                        )
                else:
                    st.info("Nenhuma família encontrada")
            
            # Gráfico de evolução
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.subheader("Evolução de Requerentes")
            
            df_grafico = get_dados_grafico()
            if df_grafico is not None:
                # Criar coluna de data/hora formatada
                df_grafico['data_hora'] = df_grafico.apply(
                    lambda x: f"{x['data'].strftime('%d/%m/%Y')} {x['hora']:02d}h", 
                    axis=1
                )

                fig = px.line(df_grafico, 
                            x='data_hora', 
                            y='total_ids',
                            title='Evolução do Número de Requerentes por Hora',
                            labels={'data_hora': 'Data e Hora', 'total_ids': 'Total de Requerentes'})
                
                # Adicionar pontos
                fig.add_trace(px.scatter(df_grafico, x='data_hora', y='total_ids').data[0])
                
                # Adicionar os números acima dos pontos
                for i, row in df_grafico.iterrows():
                    if row['total_ids'] > 0:  # Só mostra números > 0
                        fig.add_annotation(
                            x=row['data_hora'],
                            y=row['total_ids'],
                            text=str(int(row['total_ids'])),
                            yshift=10,
                            showarrow=False,
                            font=dict(size=12)
                        )
                
                # Melhorar o layout
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=14),
                    height=400,
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=12),
                        gridcolor='lightgray'
                    ),
                    yaxis=dict(
                        gridcolor='lightgray',
                        zeroline=True,
                        zerolinecolor='lightgray'
                    ),
                    showlegend=False
                )
                
                # Atualizar linhas e pontos
                fig.update_traces(
                    line=dict(width=2),
                    marker=dict(size=8)
                )
                
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=14),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Atualizar tempo de carregamento
            load_time = time.time() - start_time
            col3.metric(
                "Tempo de Carregamento",
                f"{load_time:.2f}s",
                help="Tempo total de carregamento da página"
            )

            # Botões de download no final da página
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                csv = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar CSV",
                    data=csv,
                    file_name="status_familias.csv",
                    mime="text/csv"
                )
            
            with col2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_display.to_excel(writer, sheet_name='Status Famílias', index=False)
                    worksheet = writer.sheets['Status Famílias']
                    for idx, col in enumerate(df_display.columns):
                        worksheet.set_column(idx, idx, max(len(col) + 2, df_display[col].astype(str).str.len().max() + 2))
                
                st.download_button(
                    label="Baixar Excel",
                    data=buffer.getvalue(),
                    file_name="status_familias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Configuração da tabela
            st.markdown("""
                <style>
                    /* Variáveis de tema */
                    :root {
                        --primary: #003399;
                        --success: #008C45;
                        --warning: #CD212A;
                        --neutral: #F5F7FA;
                        --text: #1E3A8A;
                    }
                    
                    /* Cards de métricas */
                    .metric-card {
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                        transition: transform 0.2s ease;
                        border-left: 4px solid var(--primary);
                        margin-bottom: 1rem;
                    }
                    
                    .metric-card:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }
                    
                    .metric-label {
                        font-size: 1rem;
                        font-weight: 600;
                        color: var(--text);
                        margin-bottom: 0.5rem;
                    }
                    
                    .metric-value {
                        font-size: 2rem;
                        font-weight: 700;
                        color: var(--primary);
                        margin-bottom: 0.5rem;
                    }
                    
                    .metric-description {
                        font-size: 0.875rem;
                        color: var(--text);
                        opacity: 0.7;
                        margin-bottom: 0.5rem;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    
                    .metric-percentage {
                        font-size: 0.875rem;
                        color: var(--primary);
                        font-weight: 600;
                    }
                    
                    /* Tabela de dados */
                    .element-container iframe {
                        height: 800px !important;
                    }
                    
                    .dataframe {
                        font-size: 16px !important;
                        background-color: white !important;
                        border-radius: 10px !important;
                        overflow: hidden !important;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
                    }
                    
                    /* Responsividade */
                    @media (max-width: 768px) {
                        .metric-card {
                            padding: 1rem;
                        }
                        
                        .metric-value {
                            font-size: 1.5rem;
                        }
                        
                        .metric-description {
                            font-size: 0.75rem;
                        }
                    }
                    .dataframe th {
                        position: sticky !important;
                        top: 0 !important;
                        background-color: var(--azul) !important;
                        color: white !important;
                        font-weight: bold !important;
                        text-align: left !important;
                        padding: 20px !important;
                        font-size: 18px !important;
                        white-space: nowrap !important;
                        z-index: 1 !important;
                    }
                    .dataframe td {
                        padding: 16px 20px !important;
                        line-height: 1.6 !important;
                        border-bottom: 1px solid #f0f0f0 !important;
                        white-space: nowrap !important;
                    }
                    .dataframe tr:hover td {
                        background-color: #f8f9fa !important;
                    }
                    .dataframe tr:last-child {
                        position: sticky !important;
                        bottom: 0 !important;
                        background-color: white !important;
                        border-top: 2px solid var(--azul) !important;
                        font-weight: bold !important;
                        z-index: 1 !important;
                    }
                    .dataframe tr:last-child td {
                        background-color: white !important;
                        border-bottom: none !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Exibe a tabela com estilo
            df_display = df_display.reset_index(drop=True)
            st.dataframe(
                df_display.style.set_properties(**{
                    'background-color': 'white',
                    'color': '#000000',
                    'font-size': '14px',
                    'font-weight': '400',
                    'min-width': '100px'
                }).format({
                    'A': '{}',
                    'B': '{}',
                    'C': '{}',
                    'D': '{}',
                    'E': '{}',
                    'Requerentes Continuar': '{:,.0f}',
                    'Requerentes Cancelar': '{:,.0f}',
                    'Requerentes Maiores': '{:,.0f}',
                    'Requerentes Menores': '{:,.0f}',
                    'Total de Requerentes': '{:,.0f}'
                }),
                use_container_width=True,
                height=600
            )
            
    except Exception as e:
        status_container.error(f"Erro ao processar dados: {str(e)}")
        st.stop()

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

# Injetar CSS personalizado
st.markdown("""
    <style>
    /* Variáveis de tema */
    :root {
        --primary: #003399;
        --success: #008C45;
        --warning: #CD212A;
        --neutral: #F5F7FA;
        --text: #1E3A8A;
    }
    
    /* Cards expansíveis */
    .expandable-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary);
        transition: all 0.2s ease;
    }
    
    .expandable-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Campo de busca */
    .search-input {
        margin: 1rem 0;
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid var(--neutral);
    }
    
    /* Gráficos responsivos */
    .plot-container {
        margin: 1rem 0;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
        border-left: 4px solid var(--primary);
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-label {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 0.5rem;
    }
    
    .metric-description {
        font-size: 0.875rem;
        color: var(--text);
        opacity: 0.7;
        margin-bottom: 0.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .metric-percentage {
        font-size: 0.875rem;
        color: var(--primary);
        font-weight: 600;
    }
    
    /* Tabela de dados */
    .dataframe {
        font-size: 16px !important;
        background-color: white !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    .dataframe th {
        background-color: var(--primary) !important;
        color: white !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 1rem !important;
    }
    
    .dataframe td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--neutral) !important;
    }
    
    .dataframe tr:hover td {
        background-color: var(--neutral) !important;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .metric-card {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .metric-description {
            font-size: 0.75rem;
        }
        
        .dataframe {
            font-size: 14px !important;
        }
        
        .plot-container {
            padding: 0.5rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

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
if tipo_relatorio == "Status das Famílias":
    show_status_familias()
elif tipo_relatorio == "Análise Funil Bitrix24":
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
