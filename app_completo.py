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
            
            # Calcular totais
            total_familias = len(df_sem_total)
            familias_continuam = len(df_sem_total[
                (df_sem_total['A'] > 0) | 
                (df_sem_total['B'] > 0) | 
                (df_sem_total['C'] > 0) | 
                (df_sem_total['D'] > 0)
            ])
            familias_canceladas = len(df_sem_total[df_sem_total['E'] > 0])
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    f"{total_familias:,}".replace(",", "."),
                    help="Total de famílias cadastradas"
                )
            
            with col2:
                st.metric(
                    "Famílias Continuam",
                    f"{familias_continuam:,}".replace(",", "."),
                    f"{(familias_continuam/total_familias*100):.1f}% do total",
                    help="Famílias com opções A, B, C ou D"
                )
            
            with col3:
                st.metric(
                    "Famílias Canceladas",
                    f"{familias_canceladas:,}".replace(",", "."),
                    f"{(familias_canceladas/total_familias*100):.1f}% do total",
                    help="Famílias com opção E"
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
                    'Nome_Exibicao', 'A', 'B', 'C', 'D', 'E'
                ]].copy()
                
                df_display.columns = [
                    'Família', 'A', 'B', 'C', 'D', 'E'
                ]
                
                # Calcular totais
                df_display['Total'] = df_display[['A', 'B', 'C', 'D', 'E']].sum(axis=1)
                
                # Adicionar status
                df_display['Status'] = 'Pendente'
                df_display.loc[
                    (df_display['A'] > 0) | 
                    (df_display['B'] > 0) | 
                    (df_display['C'] > 0) | 
                    (df_display['D'] > 0), 
                    'Status'
                ] = 'Continua'
                df_display.loc[df_display['E'] > 0, 'Status'] = 'Cancelou'
                
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
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    column_config={
                        'Família': st.column_config.TextColumn(
                            'Família',
                            width='large'
                        ),
                        'A': st.column_config.NumberColumn(
                            'A',
                            help='Opção A'
                        ),
                        'B': st.column_config.NumberColumn(
                            'B',
                            help='Opção B'
                        ),
                        'C': st.column_config.NumberColumn(
                            'C',
                            help='Opção C'
                        ),
                        'D': st.column_config.NumberColumn(
                            'D',
                            help='Opção D'
                        ),
                        'E': st.column_config.NumberColumn(
                            'E',
                            help='Opção E (Cancelados)'
                        ),
                        'Total': st.column_config.NumberColumn(
                            'Total',
                            help='Total de pessoas'
                        ),
                        'Status': st.column_config.TextColumn(
                            'Status',
                            help='Status da família'
                        )
                    }
                )
                
                # Mostrar gráfico de pizza com distribuição
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de pizza - Status das famílias
                    status_counts = df_display['Status'].value_counts()
                    fig_status = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title='Distribuição por Status',
                        color_discrete_sequence=[COLORS['verde'], COLORS['vermelho'], COLORS['azul']]
                    )
                    fig_status.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_status, use_container_width=True)
                
                with col2:
                    # Gráfico de pizza - Distribuição por opção
                    opcoes = {
                        'A': int(totais['A']),
                        'B': int(totais['B']),
                        'C': int(totais['C']),
                        'D': int(totais['D']),
                        'E': int(totais['E'])
                    }
                    fig_opcoes = px.pie(
                        values=list(opcoes.values()),
                        names=list(opcoes.keys()),
                        title='Distribuição por Opção',
                        color_discrete_sequence=[
                            COLORS['verde'], '#2ECC71', '#3498DB', 
                            '#9B59B6', COLORS['vermelho']
                        ]
                    )
                    fig_opcoes.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_opcoes, use_container_width=True)