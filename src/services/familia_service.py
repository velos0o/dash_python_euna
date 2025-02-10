"""Serviço para gerenciar dados das famílias"""
import pandas as pd
from typing import Optional, Dict, Any, Tuple
import streamlit as st
from ..data.database import db
from ..services.bitrix_service import bitrix_service
from datetime import datetime

class FamiliaService:
    """Classe para gerenciar dados das famílias"""

    @staticmethod
    @st.cache_data(ttl=300)
    def get_total_preenchimentos() -> Optional[int]:
        """Obtém o total de formulários preenchidos"""
        query = """
        SELECT COUNT(DISTINCT id) as total
        FROM whatsapp_euna_data.euna_familias
        WHERE is_menor = 0 
        AND isSpecial = 0 
        AND hasTechnicalProblems = 0
        """
        df = db.execute_query(query)
        if df is not None and not df.empty:
            return int(df['total'].iloc[0])
        return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_familias_status() -> Optional[pd.DataFrame]:
        """
        Obtém o status das famílias com cache
        
        Returns:
            DataFrame com o status das famílias ou None em caso de erro
        """
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
                SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
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
                 WHERE f2.familia = e.idfamilia) AS Total_Banco,
                MIN(e.createdAt) as Primeiro_Preenchimento,
                MAX(e.createdAt) as Ultimo_Preenchimento
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
                SUM(Sem_Opcao) AS Sem_Opcao,
                SUM(Requerentes_Preencheram) AS Requerentes_Preencheram,
                SUM(Requerentes_Maiores) AS Requerentes_Maiores,
                SUM(Requerentes_Menores) AS Requerentes_Menores,
                SUM(Total_Banco) AS Total_Banco,
                MIN(Primeiro_Preenchimento) as Primeiro_Preenchimento,
                MAX(Ultimo_Preenchimento) as Ultimo_Preenchimento
            FROM FamiliaDetalhes
        )
        SELECT * FROM FamiliaDetalhes
        UNION ALL
        SELECT * FROM TotalGeral
        ORDER BY CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END, Nome_Familia;
        """
        return db.execute_query(query)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_option_details(option: str) -> Optional[pd.DataFrame]:
        """
        Obtém detalhes de uma opção de pagamento
        
        Args:
            option: Código da opção de pagamento (A, B, C, D, E, F, Z)
            
        Returns:
            DataFrame com os detalhes da opção ou None em caso de erro
        """
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
        df = db.execute_raw_query(query, (option,))
        if df is not None:
            # Formatar datas
            df['createdAt'] = pd.to_datetime(df['createdAt']).dt.strftime('%d/%m/%Y %H:%M')
            df['birthdate'] = pd.to_datetime(df['birthdate']).dt.strftime('%d/%m/%Y')
            
            # Formatar status
            df['Status'] = df.apply(lambda x: [
                'Menor de idade' if x['is_menor'] else None,
                'Especial' if x['isSpecial'] else None,
                'Problemas Técnicos' if x['hasTechnicalProblems'] else None
            ], axis=1).apply(lambda x: ', '.join([s for s in x if s]))
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_dados_grafico() -> Optional[pd.DataFrame]:
        """
        Obtém dados para o gráfico de evolução temporal
        
        Returns:
            DataFrame com os dados do gráfico ou None em caso de erro
        """
        query = """
        SELECT 
            DATE(createdAt) as data,
            HOUR(createdAt) as hora,
            COUNT(DISTINCT id) as total_ids
        FROM whatsapp_euna_data.euna_familias
        WHERE is_menor = 0 AND isSpecial = 0 AND hasTechnicalProblems = 0
        GROUP BY DATE(createdAt), HOUR(createdAt)
        ORDER BY data, hora
        """
        return db.execute_query(query)

    @staticmethod
    def enriquecer_com_bitrix(df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriquece os dados das famílias com informações do Bitrix24
        
        Args:
            df: DataFrame com os dados das famílias
            
        Returns:
            DataFrame enriquecido com dados do Bitrix24
        """
        # Buscar dados do Bitrix24
        deals_df = bitrix_service.analisar_deals()
        if deals_df is None:
            return df
            
        # Juntar com dados do Bitrix24
        df_final = pd.merge(
            df,
            deals_df[['UF_CRM_1722605592778', 'TITLE']],
            left_on='ID_Familia',
            right_on='UF_CRM_1722605592778',
            how='left'
        )
        
        # Usar ID_Familia quando não tiver TITLE
        df_final['Nome_Familia'] = df_final['TITLE'].fillna(df_final['ID_Familia'])
        
        return df_final

    @staticmethod
    def clear_cache():
        """Limpa o cache do serviço"""
        FamiliaService.get_familias_status.clear()
        FamiliaService.get_option_details.clear()
        FamiliaService.get_dados_grafico.clear()

# Instância global
familia_service = FamiliaService()