import pandas as pd
import streamlit as st

def consultar_bitrix(table, filtros=None):
    """
    Função simulada para consulta ao Bitrix24.
    Para uma implementação real, substitua esse retorno
    pela chamada à API do Bitrix24.
    """
    if table == "crm_deal":
        # Retorno simulado: cabeçalho + dados
        return [
            ["ID", "TITLE"],
            [1, "Família Silva"],
            [2, "Família Santos"]
        ]
    elif table == "crm_deal_uf":
        return [
            ["DEAL_ID", "UF_CRM_1722605592778"],
            [1, 1],
            [2, 2]
        ]
    else:
        return None

# Simulação de dados vindos do MySQL
df_mysql = pd.DataFrame({
    "idfamilia": [1, 2, 3],
    "continua": [5, 10, 7],
    "cancelou": [2, 3, 1],
    "total_membros": [7, 13, 8]
})

# Consultar dados do Bitrix24
deals_data = consultar_bitrix("crm_deal")
deals_uf = consultar_bitrix("crm_deal_uf")

if deals_data and deals_uf:
    # Converter dados do Bitrix24 para DataFrame
    deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
    deals_uf_df = pd.DataFrame(deals_uf[1:], columns=deals_uf[0])
    
    # Juntar dados do Bitrix24
    df_bitrix = pd.merge(
        deals_df[["ID", "TITLE"]],
        deals_uf_df[["DEAL_ID", "UF_CRM_1722605592778"]],
        left_on="ID",
        right_on="DEAL_ID",
        how="left"
    )
    
    # Juntar com dados do MySQL (resultado armazenado em df_report)
    df_report = pd.merge(
        df_mysql,
        df_bitrix[["UF_CRM_1722605592778", "TITLE"]],
        left_on="idfamilia",
        right_on="UF_CRM_1722605592778",
        how="left"
    )
    
    # Usar idfamilia quando não houver TITLE
    df_report["TITLE"] = df_report["TITLE"].fillna(df_report["idfamilia"])
    
    # Preparar relatório final para exibição
    # Cria uma coluna 'nome_familia' que utiliza o TITLE (ou o idfamilia quando TITLE estiver vazio)
    df_report["nome_familia"] = df_report["TITLE"]
    
    # Selecionar colunas para exibição em uma tabela simplificada
    df_exibir = df_report[[
        "nome_familia",
        "continua",
        "cancelou",
        "total_membros"
    ]].copy()
    
    # Renomear colunas para uma melhor exibição
    df_exibir.columns = [
        "Família",
        "Ativos",
        "Cancelados",
        "Total"
    ]
    
    # Exibir Métricas comparando dados dos dois DataFrames
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_exibir = len(df_exibir)
        total_report = len(df_report)
        st.metric("Total de Famílias", f"{total_exibir} / {total_report}")
    
    with col2:
        ativos_exibir = df_exibir["Ativos"].sum()
        ativos_report = df_report["continua"].sum()
        st.metric("Famílias Ativas", f"{ativos_exibir} / {ativos_report}")
    
    with col3:
        cancelados_exibir = df_exibir["Cancelados"].sum()
        cancelados_report = df_report["cancelou"].sum()
        st.metric("Famílias Canceladas", f"{cancelados_exibir} / {cancelados_report}")
    
    # Exibir tabelas detalhadas
    st.markdown("### Detalhamento por Família")
    st.dataframe(df_exibir)
    st.dataframe(df_report)
    
    # Separador visual
    st.markdown("---")
else:
    st.write("Não foi possível obter dados do Bitrix24.")
