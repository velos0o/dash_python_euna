import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

def get_mysql_data():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            database=st.secrets["mysql"]["database"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"]
        )
        
        # Query principal para status das famílias
        query_status = """
        SELECT 
            ID_Familia, 
            Nome_Familia, 
            A, B, C, D, E
        FROM (
            -- Linhas por família
            SELECT 
                e.idfamilia AS ID_Familia,
                COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
                SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E
            FROM whatsapp_euna_data.euna_familias e
            LEFT JOIN whatsapp_euna_data.familias f 
                ON TRIM(e.idfamilia) = TRIM(f.unique_id)
            WHERE e.is_menor = 0
              AND e.isSpecial = 0
              AND e.hasTechnicalProblems = 0
            GROUP BY e.idfamilia, f.nome_familia
            
            UNION ALL
            
            -- Linha total geral
            SELECT 
                'TOTAL' AS ID_Familia,
                'Total' AS Nome_Familia,
                SUM(CASE WHEN paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
                SUM(CASE WHEN paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
                SUM(CASE WHEN paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
                SUM(CASE WHEN paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
                SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) AS E
            FROM whatsapp_euna_data.euna_familias
            WHERE is_menor = 0
              AND isSpecial = 0
              AND hasTechnicalProblems = 0
        ) AS resultado
        ORDER BY 
            CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END,
            ID_Familia;
        """
        
        # Query para requerentes sem opção
        query_sem_opcao = """
        SELECT 
            e.idfamilia,
            COALESCE(f.nome_familia, 'Sem Nome') as nome_familia,
            e.nome_completo,
            e.telefone,
            e.`e-mail` as email,
            CASE WHEN e.is_menor = 1 THEN 'Menor' ELSE 'Maior' END as status_idade
        FROM whatsapp_euna_data.euna_familias e
        LEFT JOIN whatsapp_euna_data.familias f 
            ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE (e.paymentOption IS NULL OR e.paymentOption = '')
          AND e.is_menor = 0
          AND e.isSpecial = 0
          AND e.hasTechnicalProblems = 0
        ORDER BY e.idfamilia, e.nome_completo
        """
        
        # Query para comparação de formulários
        query_comparacao = """
        WITH total_familias AS (
            SELECT COUNT(DISTINCT familia) as total_geral
            FROM whatsapp_euna_data.familiares
        ),
        preenchidos AS (
            SELECT COUNT(DISTINCT idfamilia) as total_preenchidos
            FROM whatsapp_euna_data.euna_familias
            WHERE is_menor = 0
              AND isSpecial = 0
              AND hasTechnicalProblems = 0
        )
        SELECT 'Total de Famílias' as Tipo,
               (SELECT total_geral FROM total_familias) as Total
        
        UNION ALL
        
        SELECT 'Preencheram Formulário' as Tipo,
               (SELECT total_preenchidos FROM preenchidos) as Total
        
        UNION ALL
        
        SELECT 'Não Preencheram' as Tipo,
               ((SELECT total_geral FROM total_familias) - 
                (SELECT total_preenchidos FROM preenchidos)) as Total
        """
        
        # Executar queries
        df_status = pd.read_sql(query_status, conn)
        df_sem_opcao = pd.read_sql(query_sem_opcao, conn)
        df_comparacao = pd.read_sql(query_comparacao, conn)
        
        return df_status, df_sem_opcao, df_comparacao
        
    except Exception as e:
        st.error(f'Erro ao conectar ao MySQL: {e}')
        return None, None, None
    finally:
        if 'conn' in locals():
            conn.close()

def mostrar_metricas(df_status, df_sem_opcao, df_comparacao):
    # Pegar linha de totais
    totais = df_status[df_status['Nome_Familia'] == 'Total'].iloc[0]
    
    # Calcular métricas
    total_familias = len(df_status) - 1  # -1 para excluir linha de total
    total_planos = {
        'A': totais['A'],
        'B': totais['B'],
        'C': totais['C'],
        'D': totais['D'],
        'E': totais['E']
    }
    total_sem_opcao = len(df_sem_opcao['idfamilia'].unique())
    
    # Criar colunas para métricas em cards estilizados
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Total de Famílias</div>
                <div class='metric-value'>{total_familias}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Cadastradas no Sistema
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Famílias Ativas</div>
                <div class='metric-value'>{total_planos['A'] + total_planos['B'] + total_planos['C'] + total_planos['D']}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Planos A, B, C e D
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Famílias Canceladas</div>
                <div class='metric-value'>{total_planos['E']}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Plano E
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Espaçamento
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # Segunda linha de métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Planos A e B</div>
                <div class='metric-value'>{total_planos['A'] + total_planos['B']}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Pagamento à Vista
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Planos C e D</div>
                <div class='metric-value'>{total_planos['C'] + total_planos['D']}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Pagamento Parcelado
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>Sem Opção</div>
                <div class='metric-value'>{total_sem_opcao}</div>
                <div style='color: var(--texto); opacity: 0.7; font-size: 0.875rem;'>
                    Aguardando Escolha
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Espaçamento
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # Gráfico de distribuição de planos
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de barras horizontal
        df_planos = pd.DataFrame({
            'Plano': ['A', 'B', 'C', 'D', 'E'],
            'Total': [total_planos['A'], total_planos['B'], total_planos['C'], total_planos['D'], total_planos['E']]
        })
        
        fig = px.bar(
            df_planos,
            x='Total',
            y='Plano',
            orientation='h',
            title='Distribuição por Plano',
            color='Plano',
            color_discrete_map={
                'A': '#008C45',  # Verde
                'B': '#4CAF50',  # Verde claro
                'C': '#003399',  # Azul
                'D': '#4267b2',  # Azul claro
                'E': '#CD212A'   # Vermelho
            }
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            title_x=0.5,
            title_font_size=20
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Status de Preenchimento
        st.markdown("""
            <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='text-align: center; color: #1E3A8A; margin-bottom: 20px;'>Status de Preenchimento</h3>
        """, unsafe_allow_html=True)
        
        for _, row in df_comparacao.iterrows():
            st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <div style='color: #666; font-size: 0.9em;'>{row['Tipo']}</div>
                    <div style='font-size: 1.5em; font-weight: bold; color: #003399;'>{row['Total']}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_tabela_familias(df_status):
    st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 30px;'>
            <h3 style='color: #1E3A8A; margin-bottom: 20px;'>Detalhamento por Família</h3>
    """, unsafe_allow_html=True)
    
    # Preparar dados
    df_exibir = df_status[df_status['Nome_Familia'] != 'Total'].copy()
    
    # Calcular continuam (A,B,C,D) e cancelados (E)
    df_exibir['Continuam'] = df_exibir['A'] + df_exibir['B'] + df_exibir['C'] + df_exibir['D']
    df_exibir['Cancelados'] = df_exibir['E']
    
    # Selecionar colunas para exibição
    df_exibir = df_exibir[['Nome_Familia', 'Continuam', 'Cancelados']]
    
    # Estilizar e exibir tabela
    st.dataframe(
        df_exibir.style.set_properties(**{
            'background-color': 'white',
            'color': '#000000',
            'font-size': '14px',
            'font-weight': '400',
            'min-width': '100px'
        }).format({
            'Continuam': '{:,.0f}',
            'Cancelados': '{:,.0f}'
        }),
        use_container_width=True,
        height=400
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_requerentes_sem_opcao(df_sem_opcao):
    if len(df_sem_opcao) > 0:
        st.markdown("""
            <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 30px;'>
                <h3 style='color: #1E3A8A; margin-bottom: 20px;'>Requerentes sem Opção de Pagamento</h3>
        """, unsafe_allow_html=True)
        
        # Agrupar por família
        for familia in df_sem_opcao['nome_familia'].unique():
            pessoas = df_sem_opcao[df_sem_opcao['nome_familia'] == familia]
            with st.expander(f"Família: {familia} ({len(pessoas)} pessoas)"):
                st.dataframe(
                    pessoas[['nome_completo', 'telefone', 'email', 'status_idade']]
                    .style.set_properties(**{
                        'background-color': 'white',
                        'color': '#000000',
                        'font-size': '14px',
                        'font-weight': '400',
                        'min-width': '100px'
                    }),
                    use_container_width=True
                )
        
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.title("Status das Famílias")
    
    # Carregar dados
    df_status, df_sem_opcao, df_comparacao = get_mysql_data()
    
    if df_status is not None:
        # Mostrar métricas e gráficos
        mostrar_metricas(df_status, df_sem_opcao, df_comparacao)
        
        # Mostrar tabela de famílias
        mostrar_tabela_familias(df_status)
        
        # Mostrar requerentes sem opção
        mostrar_requerentes_sem_opcao(df_sem_opcao)

if __name__ == "__main__":
    main()