            # Status das Famílias
            st.markdown(f"""
                <h2 style='color: {COLORS["azul"]}; margin-bottom: 1rem;'>
                    Status das Famílias
                </h2>
            """, unsafe_allow_html=True)
            
            # Pegar linha de totais e dados sem total
            totais = df_report[df_report['ID_Familia'] == 'TOTAL'].iloc[0]
            df_sem_total = df_report[df_report['ID_Familia'] != 'TOTAL']
            
            # Primeira linha - Totais
            col1, col2, col3 = st.columns(3)
            
            # Total de Famílias
            total_familias = len(df_sem_total)
            familias_continuam = len(df_sem_total[df_sem_total['status_familia'] == 'Continua'])
            familias_cancelaram = len(df_sem_total[df_sem_total['status_familia'] == 'Cancelou'])
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    f"{total_familias:,}".replace(",", "."),
                    help="Total de famílias cadastradas"
                )
            
            with col2:
                st.metric(
                    "Famílias que Continuam",
                    f"{familias_continuam:,}".replace(",", "."),
                    f"{(familias_continuam/total_familias*100):.1f}% do total",
                    help="Famílias com opções A, B, C ou D"
                )
            
            with col3:
                st.metric(
                    "Famílias que Cancelaram",
                    f"{familias_cancelaram:,}".replace(",", "."),
                    f"{(familias_cancelaram/total_familias*100):.1f}% do total",
                    help="Famílias com opção E"
                )
            
            # Divisor
            st.markdown("---")
            
            # Segunda linha - Comparativo de Requerentes
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Comparativo de Requerentes</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Total de requerentes em euna_familias
            total_euna = df_sem_total['A'].sum() + df_sem_total['B'].sum() + \
                        df_sem_total['C'].sum() + df_sem_total['D'].sum() + \
                        df_sem_total['E'].sum()
            
            # Total de requerentes em familiares
            total_familiares = df_sem_total['total_requerentes_esperado'].sum()
            
            with col1:
                st.metric(
                    "Requerentes em euna_familias",
                    f"{int(total_euna):,}".replace(",", "."),
                    help="Total de requerentes na tabela euna_familias"
                )
            
            with col2:
                st.metric(
                    "Requerentes em familiares",
                    f"{int(total_familiares):,}".replace(",", "."),
                    help="Total de requerentes na tabela familiares"
                )
            
            # Divisor
            st.markdown("---")
            
            # Tabela detalhada
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Detalhamento por Família</h3>", unsafe_allow_html=True)
            
            # Buscar nomes do Bitrix24
            deals_df, deals_uf_df = get_bitrix_data()
            if deals_df is not None and deals_uf_df is not None:
                # Juntar com dados do Bitrix24
                df_bitrix = pd.merge(
                    deals_df[['ID', 'TITLE']],
                    deals_uf_df[['DEAL_ID', 'UF_CRM_1722605592778']],
                    left_on='ID',
                    right_on='DEAL_ID',
                    how='left'
                )
                
                # Preparar dados para exibição
                df_detalhes = pd.merge(
                    df_sem_total,
                    df_bitrix[['UF_CRM_1722605592778', 'TITLE']],
                    left_on='ID_Familia',
                    right_on='UF_CRM_1722605592778',
                    how='left'
                )
                
                # Usar TITLE do Bitrix24 se disponível, senão usar Nome_Familia
                df_detalhes['Nome_Exibicao'] = df_detalhes['TITLE'].fillna(df_detalhes['Nome_Familia'])
                
                # Selecionar e renomear colunas
                df_display = df_detalhes[[
                    'Nome_Exibicao', 'A', 'B', 'C', 'D', 'E',
                    'status_familia', 'total_requerentes_esperado'
                ]].copy()
                
                df_display.columns = [
                    'Família', 'A', 'B', 'C', 'D', 'E',
                    'Status', 'Total Esperado'
                ]
                
                # Adicionar totais
                df_display['Total Atual'] = df_display[['A', 'B', 'C', 'D', 'E']].sum(axis=1)
                df_display['Diferença'] = df_display['Total Esperado'] - df_display['Total Atual']
                
                # Ordenar por status e nome
                df_display = df_display.sort_values(['Status', 'Família'])
                
                # Adicionar botão de download
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 Download Relatório",
                    csv,
                    "status_familias.csv",
                    "text/csv",
                    key='download-csv'
                )
                
                # Mostrar tabela
                st.dataframe(df_display, use_container_width=True)