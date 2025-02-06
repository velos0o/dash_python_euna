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

from config import DB_CONFIG, OPENAI_API_KEY

def get_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_metricas_macro():
    connection = get_database_connection()
    if connection is None:
        return None

    query = """
    WITH FamiliasBase AS (
        -- Apenas famílias que solicitaram procuração
        SELECT 
            f.unique_id,
            COUNT(DISTINCT e.idfamilia) as preencheu
        FROM whatsapp_euna_data.familias f
        LEFT JOIN whatsapp_euna_data.euna_familias e ON f.unique_id = e.idfamilia
        WHERE f.solicitado_procuracao = 1
        GROUP BY f.unique_id
    ),
    RequerentesContinuidade AS (
        -- Análise de continuidade por requerente
        SELECT 
            COUNT(DISTINCT id) as total_requerentes,
            COUNT(DISTINCT CASE WHEN paymentOption IN ('A','B','C','D') THEN id END) as requerentes_continuar,
            COUNT(DISTINCT CASE WHEN paymentOption = 'E' THEN id END) as requerentes_cancelar
        FROM whatsapp_euna_data.euna_familias
        WHERE is_menor = 0 AND isSpecial = 0 AND hasTechnicalProblems = 0
    ),
    Metricas AS (
        SELECT 
            -- Métricas de Famílias
            COUNT(DISTINCT unique_id) as total_familias_procuracao,
            SUM(preencheu) as total_familias_preencheram,
            -- Pegar métricas de requerentes
            (SELECT total_requerentes FROM RequerentesContinuidade) as total_requerentes,
            (SELECT requerentes_continuar FROM RequerentesContinuidade) as requerentes_continuar,
            (SELECT requerentes_cancelar FROM RequerentesContinuidade) as requerentes_cancelar
        FROM FamiliasBase
    )
    SELECT 
        total_familias_procuracao,
        total_familias_preencheram,
        total_requerentes,
        requerentes_continuar,
        requerentes_cancelar,
        -- Percentuais de famílias
        ROUND((total_familias_preencheram / NULLIF(total_familias_procuracao, 0)) * 100, 1) as percentual_familias_preencheram,
        ROUND(((total_familias_procuracao - total_familias_preencheram) / NULLIF(total_familias_procuracao, 0)) * 100, 1) as percentual_familias_nao_preencheram,
        -- Percentuais de requerentes
        ROUND((requerentes_continuar / NULLIF(total_requerentes, 0)) * 100, 1) as percentual_requerentes_continuar,
        ROUND((requerentes_cancelar / NULLIF(total_requerentes, 0)) * 100, 1) as percentual_requerentes_cancelar
    FROM Metricas;
    """

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query das métricas macro: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def get_progresso_familias():
    connection = get_database_connection()
    if connection is None:
        return None

    query = """
    WITH FamiliaRequerentes AS (
        -- Para cada família, calcular total de requerentes e preenchidos
        SELECT 
            f.nome_familia,
            f.unique_id,
            COUNT(DISTINCT fa.unique_id) as total_requerentes_esperados,
            COUNT(DISTINCT e.id) as total_preencheram
        FROM whatsapp_euna_data.familias f
        LEFT JOIN whatsapp_euna_data.familiares fa ON f.unique_id = fa.familia 
            AND fa.is_menor = 0 
            AND fa.is_conjuge = 0 
            AND fa.is_italiano = 0
        LEFT JOIN whatsapp_euna_data.euna_familias e ON f.unique_id = e.idfamilia
            AND e.is_menor = 0 
            AND e.isSpecial = 0 
            AND e.hasTechnicalProblems = 0
        WHERE f.solicitado_procuracao = 1
        GROUP BY f.nome_familia, f.unique_id
    )
    SELECT 
        nome_familia,
        total_requerentes_esperados,
        total_preencheram,
        CASE 
            WHEN total_preencheram = 0 THEN '0-20%'
            WHEN (total_preencheram * 100.0 / NULLIF(total_requerentes_esperados, 0)) <= 20 THEN '0-20%'
            WHEN (total_preencheram * 100.0 / NULLIF(total_requerentes_esperados, 0)) <= 40 THEN '21-40%'
            WHEN (total_preencheram * 100.0 / NULLIF(total_requerentes_esperados, 0)) <= 60 THEN '41-60%'
            WHEN (total_preencheram * 100.0 / NULLIF(total_requerentes_esperados, 0)) <= 80 THEN '61-80%'
            ELSE '81-100%'
        END as faixa_progresso,
        ROUND(total_preencheram * 100.0 / NULLIF(total_requerentes_esperados, 0), 1) as percentual_progresso
    FROM FamiliaRequerentes
    ORDER BY percentual_progresso DESC;
    """

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query de progresso: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def get_analise_conversas():
    connection = get_database_connection()
    if connection is None:
        return None

    query = """
    SELECT 
        o.userName,
        s.conversation_text,
        s.customer_name,
        s.avaliacao_geral_atendimento,
        s.satisfacao_cliente,
        s.sentimento_cliente_final,
        s.problema_resolvido
    FROM whatsapp_euna_data.operators o
    JOIN whatsapp_euna_data.scores_ranking_adm s ON o.instanceId = s.instanceId
    WHERE o.position = 'ADM'
    ORDER BY s.evaluation_datetime DESC;
    """

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query de análise de conversas: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def analisar_conversa_openai(conversation_text):
    from openai import OpenAI
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Você é um analista especializado em avaliar comunicações com clientes.
                Analise a conversa fornecida e forneça insights sobre:
                1. Tom da comunicação
                2. Clareza das informações
                3. Eficiência no atendimento
                4. Pontos positivos
                5. Pontos de melhoria
                Seja conciso e direto."""},
                {"role": "user", "content": f"Analise esta conversa:\n\n{conversation_text}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na análise: {str(e)}"

def gerar_nuvem_palavras(textos):
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import io
    
    # Juntar todos os textos
    texto_completo = ' '.join(textos)
    
    # Criar WordCloud
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='white',
        colormap='viridis',
        max_words=100
    ).generate(texto_completo)
    
    # Criar figura
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    plt.close()
    
    return buf

def get_dados_grafico():
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

def get_familias_status():
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
            SUM(CASE WHEN e.paymentOption IN ('A','B','C','D') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
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
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Status das Famílias")
    with col2:
        if st.button("Atualizar"):
            st.rerun()
    
    # Container de status
    status_container = st.empty()
    
    try:
        # Iniciar análise com feedback
        status_container.info("Iniciando análise dos dados...")
        time.sleep(0.5)
        
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
            
            col1, col2, col3, col4, col5 = st.columns(5)
            opcoes = ['A', 'B', 'C', 'D', 'E']
            colunas = [col1, col2, col3, col4, col5]
            
            total_requerentes = total_row['Total_Banco']
            
            for opcao, col in zip(opcoes, colunas):
                with col:
                    valor = total_row[opcao]
                    percentual = (valor / total_requerentes * 100) if total_requerentes > 0 else 0
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>Opção {opcao}</div>
                            <div class='metric-value'>{int(valor)}</div>
                            <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                                {int(percentual)}% do total de requerentes
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
                    'Requerentes Continuar': '{:,.0f}',
                    'Requerentes Cancelar': '{:,.0f}',
                    'Requerentes Maiores': '{:,.0f}',
                    'Requerentes Menores': '{:,.0f}',
                    'Total de Requerentes': '{:,.0f}'
                }),
                use_container_width=True,
                height=400
            )

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

def show_tela_inicial():
    st.title("Dashboard Eu na Europa")
    
    # Container de status
    status_container = st.empty()
    
    try:
        status_container.info("Carregando métricas...")
        df_metricas = get_metricas_macro()
        
        if df_metricas is not None:
            metricas = df_metricas.iloc[0]
            status_container.success("Dados carregados com sucesso!")
            
            # Métricas principais em cards
            st.subheader("Visão Geral")
            col1, col2 = st.columns(2)
            
            with col1:
                # Card de Status de Preenchimento
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Status de Preenchimento (Famílias)</div>
                        <div class='metric-value'>{int(metricas['total_familias_preencheram'])}/{int(metricas['total_familias_procuracao'])}</div>
                        <div style='color: var(--texto); opacity: 0.7; font-size: 1.2rem;'>
                            {metricas['percentual_familias_preencheram']}% das famílias com procuração preencheram
                        </div>
                        <div style='color: #CD212A; opacity: 0.9; font-size: 1.2rem;'>
                            {metricas['percentual_familias_nao_preencheram']}% ainda não preencheram
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Card de Status de Continuidade
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Status de Continuidade (Requerentes)</div>
                        <div class='metric-value'>{int(metricas['requerentes_continuar'])}/{int(metricas['total_requerentes'])}</div>
                        <div style='color: #008C45; opacity: 0.9; font-size: 1.2rem;'>
                            {metricas['percentual_requerentes_continuar']}% dos requerentes continuam
                        </div>
                        <div style='color: #CD212A; opacity: 0.9; font-size: 1.2rem;'>
                            {metricas['percentual_requerentes_cancelar']}% dos requerentes cancelam
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Progresso das Famílias
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.subheader("Progresso das Famílias")
            
            df_progresso = get_progresso_familias()
            if df_progresso is not None:
                # Calcular totais por faixa
                df_faixas = df_progresso['faixa_progresso'].value_counts().reset_index()
                df_faixas.columns = ['Faixa', 'Total']
                df_faixas['Percentual'] = (df_faixas['Total'] / len(df_progresso) * 100).round(1)
                
                # Ordenar as faixas
                ordem_faixas = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
                df_faixas['Faixa'] = pd.Categorical(df_faixas['Faixa'], categories=ordem_faixas, ordered=True)
                df_faixas = df_faixas.sort_values('Faixa')
                
                # Criar visualização de progresso
                total_familias = df_faixas['Total'].sum()
                
                # Estilo para os cards de progresso
                st.markdown("""
                    <style>
                        .progress-card {
                            background-color: white;
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            margin-bottom: 10px;
                        }
                        .progress-title {
                            font-size: 1.2rem;
                            font-weight: bold;
                            margin-bottom: 10px;
                        }
                        .progress-bar {
                            width: 100%;
                            height: 20px;
                            background-color: #f0f0f0;
                            border-radius: 10px;
                            overflow: hidden;
                            margin-bottom: 5px;
                        }
                        .progress-fill {
                            height: 100%;
                            border-radius: 10px;
                            transition: width 0.5s ease-in-out;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                # Mostrar cards de progresso
                for faixa in ordem_faixas:
                    total = df_faixas[df_faixas['Faixa'] == faixa]['Total'].iloc[0] if len(df_faixas[df_faixas['Faixa'] == faixa]) > 0 else 0
                    percentual = (total / total_familias * 100) if total_familias > 0 else 0
                    
                    # Definir cor baseada na faixa
                    if faixa == '0-20%':
                        cor = '#CD212A'  # Vermelho
                    elif faixa == '21-40%':
                        cor = '#FF6B6B'  # Vermelho claro
                    elif faixa == '41-60%':
                        cor = '#FFD93D'  # Amarelo
                    elif faixa == '61-80%':
                        cor = '#6BCB77'  # Verde claro
                    else:
                        cor = '#008C45'  # Verde
                    
                    st.markdown(f"""
                        <div class='progress-card'>
                            <div class='progress-title'>{faixa}</div>
                            <div class='progress-bar'>
                                <div class='progress-fill' style='width: {percentual}%; background-color: {cor};'></div>
                            </div>
                            <div style='display: flex; justify-content: space-between;'>
                                <span>{total} famílias</span>
                                <span>{percentual:.1f}%</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar detalhamento expandível por faixa
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                st.markdown("### Detalhamento por Faixa")
                
                for faixa in ordem_faixas:
                    familias_faixa = df_progresso[df_progresso['faixa_progresso'] == faixa]
                    total = len(familias_faixa)
                    if total > 0:
                        with st.expander(f"{faixa}: {total} famílias"):
                            # Criar tabela detalhada
                            df_detalhe = familias_faixa[['nome_familia', 'total_requerentes_esperados', 'total_preencheram', 'percentual_progresso']]
                            df_detalhe.columns = ['Família', 'Total Esperado', 'Preencheram', 'Progresso (%)']
                            
                            # Formatar números
                            df_detalhe['Progresso (%)'] = df_detalhe['Progresso (%)'].apply(lambda x: f"{x:.1f}%")
                            
                            # Exibir tabela com estilo
                            st.dataframe(
                                df_detalhe.style.set_properties(**{
                                    'background-color': 'white',
                                    'color': 'black',
                                    'font-size': '14px'
                                }),
                                use_container_width=True
                            )
                
                # Análise de Comunicação
                st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                st.subheader("Análise de Comunicação")
                
                # Carregar dados de conversas
                df_conversas = get_analise_conversas()
                if df_conversas is not None:
                    # Dropdown para selecionar operador
                    operadores = ['Todos'] + list(df_conversas['userName'].unique())
                    operador_selecionado = st.selectbox('Selecione o Operador:', operadores)
                    
                    if operador_selecionado != 'Todos':
                        df_conversas = df_conversas[df_conversas['userName'] == operador_selecionado]
                    
                    # Mostrar métricas gerais
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        media_satisfacao = df_conversas['satisfacao_cliente'].mean()
                        st.metric("Média de Satisfação", f"{media_satisfacao:.1f}/5")
                    
                    with col2:
                        problemas_resolvidos = (df_conversas['problema_resolvido'] == 1).mean() * 100
                        st.metric("Problemas Resolvidos", f"{problemas_resolvidos:.1f}%")
                    
                    with col3:
                        media_avaliacao = df_conversas['avaliacao_geral_atendimento'].mean()
                        st.metric("Avaliação Geral", f"{media_avaliacao:.1f}/5")
                    
                    # Estilo para cards e métricas
                    st.markdown("""
                        <style>
                            .metric-row {
                                display: flex;
                                justify-content: space-between;
                                margin-bottom: 20px;
                            }
                            .operator-card {
                                background: white;
                                padding: 20px;
                                border-radius: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                margin: 10px 0;
                            }
                            .operator-name {
                                font-size: 1.1rem;
                                font-weight: bold;
                                color: #1f1f1f;
                                margin-bottom: 10px;
                            }
                            .operator-stats {
                                display: flex;
                                justify-content: space-between;
                            }
                            .stat-item {
                                text-align: center;
                            }
                            .stat-value {
                                font-size: 1.2rem;
                                font-weight: bold;
                                color: #2c3e50;
                            }
                            .stat-label {
                                font-size: 0.8rem;
                                color: #7f8c8d;
                            }
                            .search-box {
                                background: white;
                                padding: 15px;
                                border-radius: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                margin-bottom: 20px;
                            }
                            .sentiment-cloud {
                                background: white;
                                padding: 20px;
                                border-radius: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                margin-top: 20px;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Layout principal
                    st.markdown("### Performance dos Operadores")
                    
                    # Preparar dados dos operadores
                    df_ranking = df_conversas.groupby('userName').agg({
                        'avaliacao_geral_atendimento': 'mean',
                        'satisfacao_cliente': 'mean',
                        'problema_resolvido': 'mean',
                        'id': 'count'  # Total de atendimentos
                    }).round(2)
                    
                    # Ordenar por avaliação geral
                    df_ranking = df_ranking.sort_values('avaliacao_geral_atendimento', ascending=False)
                    
                    # Cards dos operadores
                    for operador, metricas in df_ranking.iterrows():
                        st.markdown(f"""
                            <div class='operator-card'>
                                <div class='operator-name'>👤 {operador}</div>
                                <div class='operator-stats'>
                                    <div class='stat-item'>
                                        <div class='stat-value'>{metricas['avaliacao_geral_atendimento']:.1f}</div>
                                        <div class='stat-label'>Avaliação Geral</div>
                                    </div>
                                    <div class='stat-item'>
                                        <div class='stat-value'>{metricas['satisfacao_cliente']:.1f}</div>
                                        <div class='stat-label'>Satisfação</div>
                                    </div>
                                    <div class='stat-item'>
                                        <div class='stat-value'>{metricas['problema_resolvido']*100:.0f}%</div>
                                        <div class='stat-label'>Taxa Resolução</div>
                                    </div>
                                    <div class='stat-item'>
                                        <div class='stat-value'>{int(metricas['id'])}</div>
                                        <div class='stat-label'>Atendimentos</div>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Layout em duas colunas para busca e nuvem
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("### Análise de Conversas")
                        with st.container():
                            st.markdown("<div class='search-box'>", unsafe_allow_html=True)
                            familia_busca = st.text_input("🔍 Buscar família pelo nome")
                            if familia_busca:
                                familias_encontradas = df_conversas[
                                    df_conversas['customer_name'].str.contains(familia_busca, case=False, na=False)
                                ]
                                if not familias_encontradas.empty:
                                    for idx, conversa in familias_encontradas.iterrows():
                                        with st.expander(f"💬 {conversa['customer_name']}", expanded=True):
                                            cols = st.columns([1, 1])
                                            with cols[0]:
                                                st.markdown(f"**Operador:** {conversa['userName']}")
                                            with cols[1]:
                                                st.markdown(f"**Sentimento:** {conversa['sentimento_cliente_final']}")
                                            if st.button("📊 Analisar Conversa", key=f"btn_busca_{idx}"):
                                                with st.spinner('Analisando...'):
                                                    analise = analisar_conversa_openai(conversa['conversation_text'])
                                                    st.info(analise)
                                else:
                                    st.warning("Nenhuma família encontrada")
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### Sentimentos dos Clientes")
                        sentimentos = df_conversas['sentimento_cliente_final'].dropna().tolist()
                        if sentimentos:
                            st.markdown("<div class='sentiment-cloud'>", unsafe_allow_html=True)
                            wordcloud_buffer = gerar_nuvem_palavras(sentimentos)
                            st.image(wordcloud_buffer)
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Chat flutuante
                    st.markdown("""
                        <style>
                            .chat-container {
                                position: fixed;
                                bottom: 20px;
                                right: 20px;
                                width: 350px;
                                background: white;
                                border-radius: 10px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                z-index: 1000;
                                padding: 15px;
                            }
                            .chat-header {
                                font-weight: bold;
                                margin-bottom: 10px;
                                padding-bottom: 10px;
                                border-bottom: 1px solid #eee;
                            }
                            .chat-messages {
                                max-height: 300px;
                                overflow-y: auto;
                                margin-bottom: 10px;
                            }
                            .chat-input {
                                border-top: 1px solid #eee;
                                padding-top: 10px;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Chat para análise personalizada
                    with st.container():
                        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
                        st.markdown("<div class='chat-header'>💬 Assistente de Análise</div>", unsafe_allow_html=True)
                        
                        if "mensagens" not in st.session_state:
                            st.session_state.mensagens = []
                        
                        # Área de mensagens
                        with st.container():
                            for msg in st.session_state.mensagens[-5:]:  # Mostrar últimas 5 mensagens
                                with st.chat_message(msg["role"]):
                                    st.markdown(msg["content"])
                        
                        # Campo de entrada
                        prompt = st.chat_input("Pergunte algo sobre as conversas...")
                        if prompt:
                            st.session_state.mensagens.append({"role": "user", "content": prompt})
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            
                            with st.chat_message("assistant"):
                                with st.spinner("Analisando..."):
                                    resposta = analisar_conversa_openai(
                                        f"Analise as conversas e responda: {prompt}"
                                    )
                                    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
                                    st.markdown(resposta)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            
            # Gráficos de pizza
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            st.subheader("Distribuição")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza do status de preenchimento
                fig1 = px.pie(
                    values=[metricas['total_familias_preencheram'], 
                           metricas['total_familias_procuracao'] - metricas['total_familias_preencheram']],
                    names=['Famílias que Preencheram', 'Famílias que Não Preencheram'],
                    title='Status de Preenchimento (Famílias com Procuração)',
                    color_discrete_sequence=['#003399', '#CD212A']
                )
                fig1.update_traces(textinfo='percent+value')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Gráfico de pizza do status de continuidade
                fig2 = px.pie(
                    values=[metricas['requerentes_continuar'], metricas['requerentes_cancelar']],
                    names=['Requerentes que Continuam', 'Requerentes que Cancelam'],
                    title='Status de Continuidade (Requerentes)',
                    color_discrete_sequence=['#008C45', '#CD212A']
                )
                fig2.update_traces(textinfo='percent+value')
                st.plotly_chart(fig2, use_container_width=True)
                
    except Exception as e:
        status_container.error(f"Erro ao processar dados: {str(e)}")
        st.stop()

# Lógica principal
if tipo_relatorio == "Selecione uma opção":
    show_tela_inicial()
elif tipo_relatorio == "Status das Famílias":
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
