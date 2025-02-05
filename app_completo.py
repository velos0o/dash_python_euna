            # Status das Famílias
            st.markdown(f"""
                <h2 style='color: {COLORS["azul"]}; margin-bottom: 1rem;'>
                    Status das Famílias
                </h2>
            """, unsafe_allow_html=True)
            
            # Carregar dados do MySQL
            df_mysql = get_mysql_data()
            
            if df_mysql is not None:
                # Buscar nomes das famílias no Bitrix24
                filtros_deal = {
                    "dimensionsFilters": [[
                        {
                            "fieldName": "CATEGORY_ID",
                            "values": [32],
                            "type": "INCLUDE",
                            "operator": "EQUALS"
                        }
                    ]]
                }
                
                deals_data = consultar_bitrix("crm_deal", filtros_deal)
                deals_uf = consultar_bitrix("crm_deal_uf")
                
                if deals_data and deals_uf:
                    # Converter para DataFrames
                    deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
                    deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
                    
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
                    
                    # Métricas principais
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Total de Famílias",
                            f"{len(df_report):,}".replace(",", "."),
                            delta_color="normal"
                        )
                    
                    with col2:
                        st.metric(
                            "Famílias Ativas",
                            f"{df_report['continua'].sum():,}".replace(",", "."),
                            f"{(df_report['continua'].sum() / len(df_report) * 100):.0f}%",
                            delta_color="normal"
                        )
                    
                    with col3:
                        st.metric(
                            "Famílias Canceladas",
                            f"{df_report['cancelou'].sum():,}".replace(",", "."),
                            f"{(df_report['cancelou'].sum() / len(df_report) * 100):.0f}%",
                            delta_color="normal"
                        )
                    
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
                    
                    # Tabela detalhada
                    st.markdown("---")
                    st.markdown(f"<h3 style='color: {COLORS['azul']}'>Detalhamento por Família</h3>", unsafe_allow_html=True)
                    
                    # Mostrar tabela original
                    st.dataframe(
                        df_report,
                        use_container_width=True
                    )