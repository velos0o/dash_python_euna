import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
            
            # Filtrar registros com conteúdo
            deals_com_conteudo = deals_uf_df[
                deals_uf_df['UF_CRM_1738699062493'].notna() & 
                (deals_uf_df['UF_CRM_1738699062493'].astype(str) != '')
            ]
            total_com_conteudo = len(deals_com_conteudo)
            
            # Filtrar por etapa
            deals_na_etapa = deals_df[deals_df['STAGE_ID'] == 'C32:UC_GBPN8V']
            total_na_etapa = len(deals_na_etapa)
            
            # Métricas em cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total em NEGOCIAÇÃO TAXA",
                    f"{total_categoria_32:,}".replace(",", "."),
                    help="Total de deals na categoria 32",
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    "Com Conteúdo",
                    f"{total_com_conteudo:,}".replace(",", "."),
                    f"{(total_com_conteudo/total_categoria_32*100):.1f}%",
                    help="Deals com conteúdo preenchido",
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "Em NEGOCIAÇÃO TAXA",
                    f"{total_na_etapa:,}".replace(",", "."),
                    f"{(total_na_etapa/total_com_conteudo*100):.1f}%",
                    help="Deals na etapa C32:UC_GBPN8V",
                    delta_color="normal"
                )
            
            # Gráfico de funil melhorado
            fig_funil = go.Figure()
            
            # Adicionar etapas do funil
            fig_funil.add_trace(go.Funnel(
                name='Funil de Conversão',
                y=[
                    'Total em NEGOCIAÇÃO TAXA',
                    'Com Conteúdo',
                    'Em NEGOCIAÇÃO TAXA'
                ],
                x=[
                    total_categoria_32,
                    total_com_conteudo,
                    total_na_etapa
                ],
                textposition="inside",
                textinfo="value+percent previous",
                opacity=0.85,
                marker={
                    "color": [COLORS['azul'], COLORS['verde'], COLORS['vermelho']],
                    "line": {"width": [2, 2, 2], "color": [COLORS['branco']]}
                },
                connector={
                    "line": {
                        "color": "black",
                        "width": 1
                    }
                }
            ))
            
            # Atualizar layout
            fig_funil.update_layout(
                title={
                    'text': 'Funil de Conversão - NEGOCIAÇÃO TAXA',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 20, 'color': COLORS['azul']}
                },
                font={'size': 14},
                showlegend=False,
                margin=dict(t=120, l=50, r=50),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_funil, use_container_width=True)
            
            # Deals com conteúdo fora da etapa
            st.subheader("Deals com Conteúdo Fora da Etapa NEGOCIAÇÃO TAXA")
            
            # Identificar deals com conteúdo que não estão na etapa
            deals_fora_etapa = pd.merge(
                deals_df[deals_df['STAGE_ID'] != 'C32:UC_GBPN8V'][['ID', 'TITLE', 'STAGE_ID', 'STAGE_NAME']],
                deals_com_conteudo[['DEAL_ID']],
                left_on='ID',
                right_on='DEAL_ID',
                how='inner'
            )
            
            if not deals_fora_etapa.empty:
                df_display = deals_fora_etapa[[
                    'ID', 'TITLE', 'STAGE_NAME'
                ]].copy()
                
                df_display.columns = [
                    'ID do Deal',
                    'Título',
                    'Etapa Atual'
                ]
                
                # Adicionar botão de download
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 Download Lista",
                    csv,
                    "deals_fora_etapa.csv",
                    "text/csv",
                    key='download-deals'
                )
                
                st.dataframe(
                    df_display,
                    use_container_width=True
                )

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
            
            # Métricas detalhadas
            st.markdown(f"""
                <h2 style='color: {COLORS["azul"]}; margin-bottom: 1rem;'>
                    📊 Métricas Detalhadas por Opção de Pagamento
                </h2>
            """, unsafe_allow_html=True)
            
            # Primeira linha - Totais Gerais
            col1, col2 = st.columns(2)
            
            total_geral = int(df_report['total_atual'].sum())
            total_familias = len(df_report[df_report['idfamilia'] != 'TOTAL'])
            
            with col1:
                st.metric(
                    "Total de Requerentes",
                    f"{total_geral:,}".replace(",", "."),
                    f"Em {total_familias:,}".replace(",", ".") + " famílias",
                    help="Número total de requerentes em todas as opções"
                )
            
            with col2:
                total_sem_opcao = len(df_report[df_report['pessoas_sem_opcao'].notna()])
                st.metric(
                    "Aguardando Definição",
                    f"{total_sem_opcao:,}".replace(",", "."),
                    f"{(total_sem_opcao / total_familias * 100):.1f}% das famílias",
                    help="Famílias que ainda não escolheram uma opção de pagamento"
                )
            
            # Divisor
            st.markdown("---")
            
            # Segunda linha - Opções de Pagamento
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Distribuição por Opção</h3>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_a = int(df_report['A'].sum())
                st.metric(
                    "Opção A",
                    f"{total_a:,}".replace(",", "."),
                    f"{(total_a / total_geral * 100):.1f}% do total",
                    help="Requerentes que escolheram a Opção A de pagamento"
                )
                st.markdown(f"""
                    <small>
                        Famílias: {len(df_report[df_report['A'] > 0]):,}<br>
                        Média por família: {total_a/len(df_report[df_report['A'] > 0]):.1f} requerentes
                    </small>
                """.replace(",", "."), unsafe_allow_html=True)
            
            with col2:
                total_b = int(df_report['B'].sum())
                st.metric(
                    "Opção B",
                    f"{total_b:,}".replace(",", "."),
                    f"{(total_b / total_geral * 100):.1f}% do total",
                    help="Requerentes que escolheram a Opção B de pagamento"
                )
                st.markdown(f"""
                    <small>
                        Famílias: {len(df_report[df_report['B'] > 0]):,}<br>
                        Média por família: {total_b/len(df_report[df_report['B'] > 0]):.1f} requerentes
                    </small>
                """.replace(",", ".") if len(df_report[df_report['B'] > 0]) > 0 else "<small>Sem famílias nesta opção</small>",
                unsafe_allow_html=True)
            
            with col3:
                total_c = int(df_report['C'].sum())
                st.metric(
                    "Opção C",
                    f"{total_c:,}".replace(",", "."),
                    f"{(total_c / total_geral * 100):.1f}% do total",
                    help="Requerentes que escolheram a Opção C de pagamento"
                )
                st.markdown(f"""
                    <small>
                        Famílias: {len(df_report[df_report['C'] > 0]):,}<br>
                        Média por família: {total_c/len(df_report[df_report['C'] > 0]):.1f} requerentes
                    </small>
                """.replace(",", ".") if len(df_report[df_report['C'] > 0]) > 0 else "<small>Sem famílias nesta opção</small>",
                unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_d = int(df_report['D'].sum())
                st.metric(
                    "Opção D",
                    f"{total_d:,}".replace(",", "."),
                    f"{(total_d / total_geral * 100):.1f}% do total",
                    help="Requerentes que escolheram a Opção D de pagamento"
                )
                st.markdown(f"""
                    <small>
                        Famílias: {len(df_report[df_report['D'] > 0]):,}<br>
                        Média por família: {total_d/len(df_report[df_report['D'] > 0]):.1f} requerentes
                    </small>
                """.replace(",", ".") if len(df_report[df_report['D'] > 0]) > 0 else "<small>Sem famílias nesta opção</small>",
                unsafe_allow_html=True)
            
            with col2:
                total_e = int(df_report['E'].sum())
                st.metric(
                    "Cancelados (E)",
                    f"{total_e:,}".replace(",", "."),
                    f"{(total_e / total_geral * 100):.1f}% do total",
                    help="Requerentes que cancelaram o processo"
                )
                st.markdown(f"""
                    <small>
                        Famílias: {len(df_report[df_report['E'] > 0]):,}<br>
                        Média por família: {total_e/len(df_report[df_report['E'] > 0]):.1f} requerentes
                    </small>
                """.replace(",", ".") if len(df_report[df_report['E'] > 0]) > 0 else "<small>Sem famílias nesta opção</small>",
                unsafe_allow_html=True)
            
            # Divisor
            st.markdown("---")
            
            # Terceira linha - Resumo
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Resumo Geral</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_ativos = total_a + total_b + total_c + total_d
                familias_ativas = len(df_report[(df_report['A'] > 0) | (df_report['B'] > 0) | 
                                              (df_report['C'] > 0) | (df_report['D'] > 0)])
                st.metric(
                    "Total Ativos (A+B+C+D)",
                    f"{total_ativos:,}".replace(",", "."),
                    f"{(total_ativos / total_geral * 100):.1f}% do total",
                    help="Total de requerentes ativos em todas as opções"
                )
                st.markdown(f"""
                    <small>
                        Famílias Ativas: {familias_ativas:,}<br>
                        Média por família: {total_ativos/familias_ativas:.1f} requerentes<br>
                        {(familias_ativas/total_familias*100):.1f}% das famílias
                    </small>
                """.replace(",", "."), unsafe_allow_html=True)
            
            with col2:
                familias_canceladas = len(df_report[df_report['E'] > 0])
                st.metric(
                    "Total Cancelados (E)",
                    f"{total_e:,}".replace(",", "."),
                    f"{(total_e / total_geral * 100):.1f}% do total",
                    help="Total de requerentes que cancelaram"
                )
                st.markdown(f"""
                    <small>
                        Famílias Canceladas: {familias_canceladas:,}<br>
                        Média por família: {total_e/familias_canceladas:.1f} requerentes<br>
                        {(familias_canceladas/total_familias*100):.1f}% das famílias
                    </small>
                """.replace(",", ".") if familias_canceladas > 0 else "<small>Sem famílias canceladas</small>",
                unsafe_allow_html=True)
            
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
            
            # Tabela de Famílias
            st.subheader("Detalhes das Famílias")
            # Preparar dados para exibição
            df_detalhes = pd.DataFrame({
                'Família': df_report['nome_familia'],
                'A': df_report['A'],
                'B': df_report['B'],
                'C': df_report['C'],
                'D': df_report['D'],
                'E': df_report['E'],
                'Total Atual': df_report['total_atual'],
                'Total Esperado': df_report['total_esperado'],
                'Diferença': df_report['total_esperado'] - df_report['total_atual']
            })
            
            # Formatar números como inteiros
            colunas_numericas = ['A', 'B', 'C', 'D', 'E', 'Total Atual', 'Total Esperado', 'Diferença']
            for col in colunas_numericas:
                df_detalhes[col] = df_detalhes[col].fillna(0).astype(int)
            
            # Adicionar botão de download
            csv = df_detalhes.to_csv(index=False)
            st.download_button(
                "📥 Download Relatório",
                csv,
                "relatorio_familias.csv",
                "text/csv",
                key='download-csv'
            )
            
            # Ordenar por diferença
            df_detalhes = df_detalhes.sort_values('Diferença', ascending=False)
            
            # Formatar números como inteiros
            for col in ['Continuam', 'Cancelaram', 'Total Atual', 'Total Esperado', 'Diferença']:
                df_detalhes[col] = df_detalhes[col].astype(int)
            
            st.dataframe(
                df_detalhes,
                use_container_width=True
            )
            
            # Tabela de Opções de Pagamento
            st.subheader("Detalhes por Opção de Pagamento")
            if df_options is not None:
                df_options['Descrição'] = df_options['paymentOption'].map({
                    'A': 'Opção A',
                    'B': 'Opção B',
                    'C': 'Opção C',
                    'D': 'Opção D',
                    'E': 'Cancelado'
                })
                
                df_options_display = df_options[[
                    'Descrição', 'total', 'pessoas'
                ]].copy()
                
                df_options_display.columns = [
                    'Opção', 'Total', 'Pessoas'
                ]
                
                st.dataframe(
                    df_options_display,
                    use_container_width=True
                )
            
            # Pessoas sem opção de pagamento
            st.subheader("Pessoas sem Opção de Pagamento")
            df_sem_opcao = df_report[df_report['pessoas_sem_opcao'].notna()]
            
            if not df_sem_opcao.empty:
                for _, row in df_sem_opcao.iterrows():
                    with st.expander(f"Família: {row['TITLE']}"):
                        st.text(row['pessoas_sem_opcao'])