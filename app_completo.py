            # Métricas detalhadas
            st.markdown(f"""
                <h2 style='color: {COLORS["azul"]}; margin-bottom: 1rem;'>
                    📊 Métricas por Opção de Pagamento
                </h2>
            """, unsafe_allow_html=True)
            
            # Pegar linha de totais
            totais = df_report[df_report['ID_Familia'] == 'TOTAL'].iloc[0]
            df_sem_total = df_report[df_report['ID_Familia'] != 'TOTAL']
            
            # Primeira linha - Totais
            col1, col2, col3 = st.columns(3)
            
            total_requerentes = totais['A'] + totais['B'] + totais['C'] + totais['D'] + totais['E']
            total_familias = len(df_sem_total)
            
            with col1:
                st.metric(
                    "Total de Requerentes",
                    f"{int(total_requerentes):,}".replace(",", "."),
                    help="Total de requerentes em todas as opções"
                )
            
            with col2:
                st.metric(
                    "Total de Famílias",
                    f"{total_familias:,}".replace(",", "."),
                    f"Média: {total_requerentes/total_familias:.1f}/família",
                    help="Total de famílias"
                )
            
            with col3:
                familias_sem_opcao = len(df_sem_total[
                    (df_sem_total['A'] == 0) & 
                    (df_sem_total['B'] == 0) & 
                    (df_sem_total['C'] == 0) & 
                    (df_sem_total['D'] == 0) & 
                    (df_sem_total['E'] == 0)
                ])
                st.metric(
                    "Aguardando Definição",
                    f"{familias_sem_opcao:,}".replace(",", "."),
                    f"{(familias_sem_opcao/total_familias*100):.1f}% das famílias",
                    help="Famílias sem opção definida"
                )
            
            # Divisor
            st.markdown("---")
            
            # Segunda linha - Opções A, B e C
            col1, col2, col3 = st.columns(3)
            
            with col1:
                familias_a = len(df_sem_total[df_sem_total['A'] > 0])
                st.metric(
                    "Opção A",
                    f"{int(totais['A']):,}".replace(",", "."),
                    f"{(totais['A']/total_requerentes*100):.1f}% dos requerentes",
                    help="Requerentes na opção A"
                )
                if familias_a > 0:
                    st.markdown(f"<small>{familias_a:,} famílias • {totais['A']/familias_a:.1f}/família</small>".replace(",", "."), unsafe_allow_html=True)
            
            with col2:
                familias_b = len(df_sem_total[df_sem_total['B'] > 0])
                st.metric(
                    "Opção B",
                    f"{int(totais['B']):,}".replace(",", "."),
                    f"{(totais['B']/total_requerentes*100):.1f}% dos requerentes",
                    help="Requerentes na opção B"
                )
                if familias_b > 0:
                    st.markdown(f"<small>{familias_b:,} famílias • {totais['B']/familias_b:.1f}/família</small>".replace(",", "."), unsafe_allow_html=True)
            
            with col3:
                familias_c = len(df_sem_total[df_sem_total['C'] > 0])
                st.metric(
                    "Opção C",
                    f"{int(totais['C']):,}".replace(",", "."),
                    f"{(totais['C']/total_requerentes*100):.1f}% dos requerentes",
                    help="Requerentes na opção C"
                )
                if familias_c > 0:
                    st.markdown(f"<small>{familias_c:,} famílias • {totais['C']/familias_c:.1f}/família</small>".replace(",", "."), unsafe_allow_html=True)
            
            # Terceira linha - Opções D e E
            col1, col2 = st.columns(2)
            
            with col1:
                familias_d = len(df_sem_total[df_sem_total['D'] > 0])
                st.metric(
                    "Opção D",
                    f"{int(totais['D']):,}".replace(",", "."),
                    f"{(totais['D']/total_requerentes*100):.1f}% dos requerentes",
                    help="Requerentes na opção D"
                )
                if familias_d > 0:
                    st.markdown(f"<small>{familias_d:,} famílias • {totais['D']/familias_d:.1f}/família</small>".replace(",", "."), unsafe_allow_html=True)
            
            with col2:
                familias_e = len(df_sem_total[df_sem_total['E'] > 0])
                st.metric(
                    "Cancelados (E)",
                    f"{int(totais['E']):,}".replace(",", "."),
                    f"{(totais['E']/total_requerentes*100):.1f}% dos requerentes",
                    help="Requerentes que cancelaram"
                )
                if familias_e > 0:
                    st.markdown(f"<small>{familias_e:,} famílias • {totais['E']/familias_e:.1f}/família</small>".replace(",", "."), unsafe_allow_html=True)
            
            # Divisor
            st.markdown("---")
            
            # Resumo final
            st.markdown(f"<h3 style='color: {COLORS['azul']}'>Resumo Final</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_ativos = totais['A'] + totais['B'] + totais['C'] + totais['D']
                familias_ativas = len(df_sem_total[
                    (df_sem_total['A'] > 0) | 
                    (df_sem_total['B'] > 0) | 
                    (df_sem_total['C'] > 0) | 
                    (df_sem_total['D'] > 0)
                ])
                st.metric(
                    "Total Ativos (A+B+C+D)",
                    f"{int(total_ativos):,}".replace(",", "."),
                    f"{(total_ativos/total_requerentes*100):.1f}% dos requerentes",
                    help="Total de requerentes ativos"
                )
                if familias_ativas > 0:
                    st.markdown(f"""
                        <small>
                            {familias_ativas:,} famílias ativas<br>
                            {total_ativos/familias_ativas:.1f} requerentes/família<br>
                            {(familias_ativas/total_familias*100):.1f}% das famílias
                        </small>
                    """.replace(",", "."), unsafe_allow_html=True)
            
            with col2:
                st.metric(
                    "Total Cancelados (E)",
                    f"{int(totais['E']):,}".replace(",", "."),
                    f"{(totais['E']/total_requerentes*100):.1f}% dos requerentes",
                    help="Total de requerentes que cancelaram"
                )
                if familias_e > 0:
                    st.markdown(f"""
                        <small>
                            {familias_e:,} famílias canceladas<br>
                            {totais['E']/familias_e:.1f} requerentes/família<br>
                            {(familias_e/total_familias*100):.1f}% das famílias
                        </small>
                    """.replace(",", "."), unsafe_allow_html=True)