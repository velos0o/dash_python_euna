"""Componente principal do dashboard"""
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time
import io
from ...services.familia_service import familia_service
from ...utils.constants import PAYMENT_OPTIONS, PAYMENT_OPTIONS_COLORS

class Dashboard:
    """Classe para gerenciar a interface do dashboard"""

    @staticmethod
    def show_cache_metrics():
        """Exibe métricas de cache"""
        pass  # Removido pois as métricas agora estão apenas no sidebar

    @staticmethod
    def show_main_metrics(df: pd.DataFrame):
        """Exibe métricas principais"""
        total_row = df[df['Nome_Familia'] == 'Total'].iloc[0]
        total_preenchimentos = familia_service.get_total_preenchimentos()
        
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

    @staticmethod
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

    @staticmethod
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
                    ),
                    ticktext=[f"{h:02d}:00" for h in range(24)],
                    tickvals=list(range(24))
                )
            )
            
            fig_hora.update_traces(
                marker_color='#1a73e8',
                hovertemplate="<br>".join([
                    "Hora: %{x}:00",
                    "Total: %{y}",
                    "<extra></extra>"
                ])
            )
            
            st.plotly_chart(fig_hora, use_container_width=True)
        
        with tab2:
            df_grouped = df.groupby(['data_formatada', 'hora_formatada'])['total_ids'].sum().reset_index()
            df_grouped['datetime'] = pd.to_datetime(df_grouped['data_formatada'] + ' ' + df_grouped['hora_formatada'])
            
            fig_timeline = px.bar(
                df_grouped,
                x='datetime',
                y='total_ids',
                title='Linha do Tempo de Preenchimentos',
                labels={
                    'datetime': 'Data/Hora',
                    'total_ids': 'Quantidade'
                }
            )
            
            fig_timeline.update_layout(
                showlegend=False,
                plot_bgcolor='white',
                yaxis=dict(
                    gridcolor='#eee',
                    title=dict(
                        text='Quantidade',
                        font=dict(size=14)
                    )
                ),
                xaxis=dict(
                    title=dict(
                        text='Data/Hora',
                        font=dict(size=14)
                    ),
                    dtick='H2'  # Mostrar tick a cada 2 horas
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14
                )
            )
            
            fig_timeline.update_traces(
                marker_color='#1a73e8',
                hovertemplate="<br>".join([
                    "Data: %{x|%d/%m/%Y}",
                    "Hora: %{x|%H:00}",
                    "Preenchimentos: %{y}",
                    "<extra></extra>"
                ])
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)

    @staticmethod
    @st.cache_data(ttl=300)
    def filter_familias(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """Filtra famílias com cache"""
        if not search_term:
            return df
        
        # Converter para minúsculas para busca case-insensitive
        search_term = search_term.lower()
        mask = df['Nome_Familia'].str.lower().str.contains(search_term, na=False)
        return df[mask]

    @staticmethod
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
            df_display = Dashboard.filter_familias(df_display, search)
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

    @staticmethod
    def show_option_details(option: str):
        """Exibe detalhes de uma opção de pagamento"""
        df = familia_service.get_option_details(option)
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

    @staticmethod
    def render():
        """Renderiza o dashboard completo"""
        # Título e botão de atualização
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title("Status das Famílias")
        with col2:
            if st.button("🔄 Atualizar"):
                familia_service.clear_cache()
                st.rerun()
        
        # Iniciar análise
        start_time = time.time()
        
        try:
            # Carregar dados
            with st.spinner("Carregando dados..."):
                df_status = familia_service.get_familias_status()
                df_timeline = familia_service.get_dados_grafico()
            
            if df_status is not None:
                # Mostrar componentes
                Dashboard.show_cache_metrics()
                st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_main_metrics(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_payment_options(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                if df_timeline is not None:
                    Dashboard.show_timeline_chart(df_timeline)
                    st.markdown("<hr>", unsafe_allow_html=True)
                
                Dashboard.show_detailed_table(df_status)
                st.markdown("<hr>", unsafe_allow_html=True)
                
                # Detalhes por opção
                st.markdown("### 🔍 Explorar Opção")
                option = st.selectbox(
                    "Selecione uma opção para ver detalhes",
                    options=list(PAYMENT_OPTIONS.keys()),
                    format_func=lambda x: f"{x} - {PAYMENT_OPTIONS[x]}"
                )
                if option:
                    Dashboard.show_option_details(option)
            else:
                st.error("Erro ao carregar dados. Tente novamente mais tarde.")
            
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
        finally:
            # Mostrar tempo de carregamento
            end_time = time.time()
            st.sidebar.metric(
                "Tempo de Carregamento",
                f"{(end_time - start_time):.2f}s",
                help="Tempo total de carregamento da página"
            )