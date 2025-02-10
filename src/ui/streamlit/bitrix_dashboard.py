"""Componente de dashboard para análise do Bitrix24"""
import streamlit as st
import pandas as pd
import io
import time
from ...services.bitrix_service import bitrix_service

class BitrixDashboard:
    """Classe para gerenciar o dashboard do Bitrix24"""

    @staticmethod
    def show_metrics(metricas: dict):
        """Exibe métricas principais"""
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

    @staticmethod
    def show_detailed_table(df_detalhamento: pd.DataFrame):
        """Exibe tabela detalhada"""
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
                'color': '#000000',
                'font-size': '14px',
                'font-weight': '400',
                'min-width': '100px'
            }).format({
                'ID': lambda x: f'{x:,.0f}'
            }),
            use_container_width=True,
            height=600
        )

    @staticmethod
    def render():
        """Renderiza o dashboard do Bitrix24"""
        # Título e botão de atualização
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title("Análise Funil Bitrix24")
        with col2:
            if st.button("🔄 Atualizar"):
                st.rerun()
        
        # Container de status
        status_container = st.empty()
        
        try:
            # Iniciar análise com feedback
            status_container.info("Iniciando análise dos dados...")
            time.sleep(0.5)
            
            # Consulta ao Bitrix24
            status_container.info("Consultando negócios no Bitrix24...")
            resultado = bitrix_service.analisar_deals()
            
            if not resultado:
                status_container.error("Erro ao analisar os dados. Por favor, tente novamente.")
                st.stop()
            
            metricas, df_detalhamento, _ = resultado
            status_container.success("Dados carregados com sucesso!")
            
            # Exibir componentes
            BitrixDashboard.show_metrics(metricas)
            BitrixDashboard.show_detailed_table(df_detalhamento)
            
        except Exception as e:
            status_container.error(f"Erro ao processar dados: {str(e)}")
            st.stop()