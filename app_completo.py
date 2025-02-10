"""
Módulo principal do aplicativo
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from mysql.connector import Error
import requests
import json
import time
import io
import base64
from datetime import datetime, timedelta

# Constantes
PAYMENT_OPTIONS = {
    'A': 'Pagamento no momento do protocolo junto ao tribunal competente',
    'B': 'Incorporação da taxa ao parcelamento do contrato vigente',
    'C': 'Pagamento flexível com entrada reduzida e saldo postergado',
    'D': 'Parcelamento em até 24 vezes fixas',
    'E': 'Cancelar',
    'F': 'Pagamento no momento do deferimento junto ao tribunal competente',
    'Z': 'Análise especial'
}

PAYMENT_OPTIONS_COLORS = {
    'A': '#4CAF50',  # Verde
    'B': '#2196F3',  # Azul
    'C': '#9C27B0',  # Roxo
    'D': '#FF9800',  # Laranja
    'E': '#F44336',  # Vermelho
    'F': '#795548',  # Marrom
    'Z': '#607D8B'   # Cinza azulado
}

# Funções de banco de dados
def get_database_connection():
    try:
        from sqlalchemy import create_engine
        engine = create_engine(
            'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'.format(
                user='lucas',
                password='a9!o98Q80$MM',
                host='database-1.cdqa6ywqs8pz.us-west-2.rds.amazonaws.com',
                port=3306,
                database='whatsapp_euna_data'
            )
        )
        return engine
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

@st.cache_data(ttl=300)
def get_familias_status():
    """Obtém o status das famílias com cache"""
    connection = get_database_connection()
    if connection is None:
        return None

    query = """
    WITH FamiliaDetalhes AS (
        SELECT
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            SUM(CASE WHEN e.paymentOption = 'F' THEN 1 ELSE 0 END) AS F,
            SUM(CASE WHEN e.paymentOption = 'Z' THEN 1 ELSE 0 END) AS Z,
            SUM(CASE WHEN e.paymentOption IN ('A','B','C','D','F','Z') THEN 1 ELSE 0 END) AS Requerentes_Continuar,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS Requerentes_Cancelar,
            COUNT(DISTINCT e.id) AS Requerentes_Preencheram,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia
             AND f2.is_conjuge = 0
             AND f2.is_italiano = 0
             AND f2.is_menor = 0) AS Requerentes_Maiores,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia
             AND f2.is_menor = 1) AS Requerentes_Menores,
            (SELECT COUNT(DISTINCT unique_id)
             FROM whatsapp_euna_data.familiares f2
             WHERE f2.familia = e.idfamilia) AS Total_Banco
        FROM whatsapp_euna_data.euna_familias e
        LEFT JOIN whatsapp_euna_data.familias f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0 AND e.isSpecial = 0 AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia
    ),
    TotalGeral AS (
        SELECT
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(A) AS A,
            SUM(B) AS B,
            SUM(C) AS C,
            SUM(D) AS D,
            SUM(E) AS E,
            SUM(F) AS F,
            SUM(Z) AS Z,
            SUM(Requerentes_Continuar) AS Requerentes_Continuar,
            SUM(Requerentes_Cancelar) AS Requerentes_Cancelar,
            SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
            SUM(Requerentes_Maiores) AS Requerentes_Maiores,
            SUM(Requerentes_Menores) AS Requerentes_Menores,
            SUM(Total_Banco) AS Total_Banco
        FROM FamiliaDetalhes
    )
    SELECT * FROM FamiliaDetalhes
    UNION ALL
    SELECT * FROM TotalGeral
    ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, Nome_Familia;
    """

    try:
        df = pd.read_sql(query, connection)
        return df
    except Error as e:
        st.error(f"Erro ao executar query: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

@st.cache_data(ttl=300)
def get_option_details(option: str):
    """Obtém detalhes de uma opção de pagamento"""
    connection = get_database_connection()
    if connection is None:
        return None

    query = """
    SELECT
        e.idfamilia,
        e.nome_completo,
        e.telefone,
        e.`e-mail` as email,
        e.birthdate,
        e.paymentOption,
        e.createdAt,
        e.is_menor,
        e.isSpecial,
        e.hasTechnicalProblems,
        f.nome_familia,
        TIMESTAMPDIFF(YEAR, e.birthdate, CURDATE()) as idade
    FROM whatsapp_euna_data.euna_familias e
    LEFT JOIN whatsapp_euna_data.familias f
        ON TRIM(e.idfamilia) = TRIM(f.unique_id)
    WHERE e.paymentOption = %s
    AND e.is_menor = 0
    AND e.isSpecial = 0
    AND e.hasTechnicalProblems = 0
    ORDER BY e.createdAt DESC
    """

    try:
        df = pd.read_sql(query, connection, params=[option])
        df['createdAt'] = pd.to_datetime(df['createdAt']).dt.strftime('%d/%m/%Y %H:%M')
        df['birthdate'] = pd.to_datetime(df['birthdate']).dt.strftime('%d/%m/%Y')
        return df
    except Error as e:
        st.error(f"Erro ao buscar detalhes: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def show_status_familias():
    """Exibe dashboard de status das famílias"""
    # Título e botão de atualização
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("Status das Famílias")
    with col2:
        if st.button("🔄 Atualizar"):
            st.cache_data.clear()
            st.rerun()

    try:
        # Carregar dados
        with st.spinner("Carregando dados..."):
            df_status = get_familias_status()

        if df_status is not None:
            # Métricas gerais
            total_row = df_status[df_status['Nome_Familia'] == 'Total'].iloc[0]

            # Cards de métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{len(df_status[df_status['Nome_Familia'] != 'Total'])}</div>
                        <div class='metric-label'>Total de Famílias</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{int(total_row['Requerentes_Continuar'])}</div>
                        <div class='metric-label'>Requerentes Continuar</div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{int(total_row['Requerentes_Cancelar'])}</div>
                        <div class='metric-label'>Requerentes Cancelar</div>
                    </div>
                """, unsafe_allow_html=True)

            # Distribuição por opção
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Distribuição por Opção de Pagamento")

            cols = st.columns(7)
            for option, col in zip(['A', 'B', 'C', 'D', 'E', 'F', 'Z'], cols):
                valor = total_row[option]
                with col:
                    st.markdown(f"""
                        <div class='metric-card' style='border-left: 4px solid {PAYMENT_OPTIONS_COLORS[option]};'>
                            <div class='metric-value'>{int(valor)}</div>
                            <div class='metric-label'>Opção {option}</div>
                            <div style='font-size: 0.8rem; margin-top: 0.5rem;'>
                                {PAYMENT_OPTIONS[option][:30]}...
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            # Tabela detalhada
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Detalhamento por Família")

            # Preparar dados para a tabela
            df_display = df_status.copy()
            df_display = df_display[df_display['Nome_Familia'] != 'Total']

            # Campo de busca
            search = st.text_input(
                "🔍 Buscar família",
                help="Digite o nome da família para filtrar",
                placeholder="Ex: Silva, Santos..."
            )

            if search:
                df_display = df_display[df_display['Nome_Familia'].str.contains(search, case=False, na=False)]
                if df_display.empty:
                    st.warning("Nenhuma família encontrada.")
                    return

            # Exibir tabela
            st.dataframe(
                df_display.style.format({
                    'A': '{:,.0f}',
                    'B': '{:,.0f}',
                    'C': '{:,.0f}',
                    'D': '{:,.0f}',
                    'E': '{:,.0f}',
                    'F': '{:,.0f}',
                    'Z': '{:,.0f}',
                    'Requerentes_Continuar': '{:,.0f}',
                    'Requerentes_Cancelar': '{:,.0f}',
                    'Total_Banco': '{:,.0f}'
                }),
                use_container_width=True,
                height=400
            )

        else:
            st.error("Erro ao carregar dados. Tente novamente mais tarde.")

    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")

def main():
    """Função principal do aplicativo"""
    if 'tipo_relatorio' in globals():
        if tipo_relatorio == "Status das Famílias":
            show_status_familias()
        elif tipo_relatorio == "Análise Funil Bitrix24":
            st.info("Módulo em desenvolvimento")
        elif tipo_relatorio == "Selecione uma opção":
            st.info("👈 Selecione um relatório no menu lateral para começar")
    else:
        show_status_familias()

if __name__ == "__main__":
    main()
