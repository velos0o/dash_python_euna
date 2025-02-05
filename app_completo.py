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
            total_pessoas_euna = int(totais['Total_euna'])
            total_sem_opcao = int(totais['Sem_Opcao'])
            total_esperado = int(totais['total_requerentes_esperado'])
            
            with col1:
                st.metric(
                    "Total de Famílias",
                    f"{total_familias:,}".replace(",", "."),
                    help="Total de famílias cadastradas"
                )
            
            with col2:
                st.metric(
                    "Pessoas em euna_familias",
                    f"{total_pessoas_euna:,}".replace(",", "."),
                    f"{total_sem_opcao:,} sem opção".replace(",", "."),
                    help="Total de pessoas na tabela euna_familias"
                )
            
            with col3:
                st.metric(
                    "Requerentes Esperados",
                    f"{total_esperado:,}".replace(",", "."),
                    f"Diferença: {total_esperado - total_pessoas_euna:,}".replace(",", "."),
                    help="Total de requerentes na tabela familiares"
                )
            
            # Análise dos dados
            st.markdown("---")
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Análise dos Dados</h3>", unsafe_allow_html=True)
            
            # Calcular métricas para análise
            familias_incompletas = len(df_sem_total[df_sem_total['diferenca_requerentes'] > 0])
            familias_com_pendentes = len(df_sem_total[df_sem_total['Sem_Opcao'] > 0])
            
            # Mostrar insights
            st.markdown(f"""
                #### Pontos de Atenção:
                
                1. **Pessoas sem Opção de Pagamento**:
                   - {total_sem_opcao:,} pessoas ainda não escolheram uma opção
                   - Isso representa {(total_sem_opcao/total_pessoas_euna*100):.1f}% do total em euna_familias
                   - Afeta {familias_com_pendentes:,} famílias ({(familias_com_pendentes/total_familias*100):.1f}% do total)
                
                2. **Diferença entre Bases**:
                   - Esperados: {total_esperado:,} requerentes (tabela familiares)
                   - Atual: {total_pessoas_euna:,} pessoas (tabela euna_familias)
                   - Diferença: {total_esperado - total_pessoas_euna:,} pessoas
                   - {familias_incompletas:,} famílias ({(familias_incompletas/total_familias*100):.1f}%) têm menos pessoas que o esperado
                
                #### Distribuição por Opção:
                - Opção A: {int(totais['A']):,} pessoas ({(totais['A']/total_pessoas_euna*100):.1f}%)
                - Opção B: {int(totais['B']):,} pessoas ({(totais['B']/total_pessoas_euna*100):.1f}%)
                - Opção C: {int(totais['C']):,} pessoas ({(totais['C']/total_pessoas_euna*100):.1f}%)
                - Opção D: {int(totais['D']):,} pessoas ({(totais['D']/total_pessoas_euna*100):.1f}%)
                - Opção E: {int(totais['E']):,} pessoas ({(totais['E']/total_pessoas_euna*100):.1f}%)
                - Sem Opção: {int(totais['Sem_Opcao']):,} pessoas ({(totais['Sem_Opcao']/total_pessoas_euna*100):.1f}%)
            """.replace(",", "."), unsafe_allow_html=True)
            
            # Questionamentos
            st.markdown(f"""
                #### Questionamentos:
                
                1. **Pessoas sem Opção**:
                   - Por que {total_sem_opcao:,} pessoas ainda não escolheram uma opção?
                   - Existe algum padrão nas famílias com pessoas pendentes?
                
                2. **Diferença entre Bases**:
                   - Por que existem {abs(total_esperado - total_pessoas_euna):,} pessoas de diferença?
                   - As famílias sabem que têm membros faltando?
                
                3. **Distribuição**:
                   - Por que a opção {['A','B','C','D'][totais[['A','B','C','D']].argmax()]} é a mais escolhida?
                   - O que leva as pessoas a escolherem cada opção?
            """.replace(",", "."), unsafe_allow_html=True)
            
            # Tabela detalhada
            st.markdown("---")
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
                    'Nome_Exibicao', 'A', 'B', 'C', 'D', 'E', 'Sem_Opcao',
                    'Total_euna', 'total_requerentes_esperado', 'diferenca_requerentes'
                ]].copy()
                
                df_display.columns = [
                    'Família', 'A', 'B', 'C', 'D', 'E', 'Sem Opção',
                    'Total Atual', 'Total Esperado', 'Diferença'
                ]
                
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
                
                # Mostrar detalhes das pessoas sem opção
                if st.checkbox("Ver detalhes das pessoas sem opção de pagamento"):
                    st.markdown(f"<h4 style='color: {COLORS['azul']}'>Pessoas sem Opção de Pagamento</h4>", unsafe_allow_html=True)
                    for _, row in df_detalhes[df_detalhes['pessoas_sem_opcao'].notna()].iterrows():
                        with st.expander(f"Família: {row['Nome_Exibicao']}"):
                            st.text(row['pessoas_sem_opcao'])