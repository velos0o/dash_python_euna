import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Relatório de Famílias",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Título
st.title("👨‍👩‍👧‍👦 Relatório de Famílias")

# Carregar dados
df = pd.read_csv('relatorio_familias.csv')

# Remover linha de total para visualizações
df_viz = df[df['ID_Familia'] != 'TOTAL'].copy()

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Famílias",
        f"{len(df_viz):,}".replace(",", ".")
    )

with col2:
    st.metric(
        "Total de Membros",
        f"{df_viz['Total_Membros'].sum():,}".replace(",", ".")
    )

with col3:
    st.metric(
        "Total Continua",
        f"{df_viz['Continua'].sum():,}".replace(",", "."),
        f"{df_viz['Continua'].sum() / df_viz['Total_Membros'].sum():.1%}"
    )

with col4:
    st.metric(
        "Total Cancelou",
        f"{df_viz['Cancelou'].sum():,}".replace(",", "."),
        f"{df_viz['Cancelou'].sum() / df_viz['Total_Membros'].sum():.1%}"
    )

# Gráficos
col1, col2 = st.columns(2)

with col1:
    # Gráfico de Pizza - Status
    valores_status = [df_viz['Continua'].sum(), df_viz['Cancelou'].sum()]
    labels_status = ['Continua', 'Cancelou']
    
    fig_pie = px.pie(
        values=valores_status,
        names=labels_status,
        title='Distribuição de Status',
        color_discrete_sequence=['#00CC96', '#EF553B']
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Gráfico de Barras - Top 5 famílias
    df_top5 = df_viz.sort_values('Total_Membros', ascending=False).head(5)
    
    fig_bar = px.bar(
        df_top5,
        x='Nome_Familia',
        y=['Continua', 'Cancelou'],
        title='Top 5 Famílias por Total de Membros',
        barmode='stack',
        color_discrete_sequence=['#00CC96', '#EF553B']
    )
    
    fig_bar.update_layout(
        xaxis_title="Família",
        yaxis_title="Quantidade",
        showlegend=True
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Tabela detalhada
st.subheader("Detalhes por Família")
st.dataframe(
    df_viz.sort_values('Total_Membros', ascending=False),
    column_config={
        'ID_Familia': 'ID da Família',
        'Nome_Familia': 'Nome da Família',
        'Continua': 'Continua',
        'Cancelou': 'Cancelou',
        'Total_Membros': 'Total de Membros'
    },
    hide_index=True
)