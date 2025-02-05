@@ -84,11 +84,11 @@ def consultar_bitrix(table, filtros=None):
    deals_uf = consultar_bitrix("crm_deal_uf")

    if deals_data and deals_uf:
        # Converter dados do Bitrix24 para DataFrame
        # Preparar dados do Bitrix24
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])

        # Juntar dados do Bitrix24
        # Juntar dados
        df_bitrix = pd.merge(
            deals_df[["ID", "TITLE"]],
            deals_uf_df[["DEAL_ID", "UF_CRM_1722605592778"]],
@@ -97,8 +97,8 @@ def consultar_bitrix(table, filtros=None):
            how="left"
        )

        # Juntar com dados do MySQL
        df_final = pd.merge(
        # Relatório final
        df_report = pd.merge(
            df_mysql,
            df_bitrix[["UF_CRM_1722605592778", "TITLE"]],
            left_on="idfamilia",
@@ -107,48 +107,32 @@ def consultar_bitrix(table, filtros=None):
        )

        # Usar idfamilia quando não tiver TITLE
        df_final["nome_familia"] = df_final["TITLE"].fillna(df_final["idfamilia"])

        # Selecionar colunas para exibição
        df_exibir = df_final[[
            "nome_familia",
            "continua",
            "cancelou",
            "total_membros"
        ]].copy()

        # Renomear colunas
        df_exibir.columns = [
            "Família",
            "Ativos",
            "Cancelados",
            "Total"
        ]
        df_report["TITLE"] = df_report["TITLE"].fillna(df_report["idfamilia"])

        # Métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total de Famílias",
                str(len(df_exibir))
                str(len(df_report))
            )

        with col2:
            st.metric(
                "Famílias Ativas",
                str(df_exibir["Ativos"].sum())
                str(df_report["continua"].sum())
            )

        with col3:
            st.metric(
                "Famílias Canceladas",
                str(df_exibir["Cancelados"].sum())
                str(df_report["cancelou"].sum())
            )

        # Tabela de Detalhamento por Família
        # Tabela
        st.markdown("### Detalhamento por Família")
        st.dataframe(df_exibir)
        st.dataframe(df_report)

        # Separador visual
        st.markdown("---")
