"""Serviço de integração com Bitrix24"""
import requests
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import streamlit as st
from datetime import datetime, timedelta
from ..utils.constants import BITRIX_CONFIG
import time

class BitrixService:
    """Classe para interagir com a API do Bitrix24"""
    
    def __init__(self):
        self.base_url = BITRIX_CONFIG['base_url']
        self.token = BITRIX_CONFIG['token']
        self.timeout = BITRIX_CONFIG['timeout']
        self.max_retries = BITRIX_CONFIG['max_retries']
        self._session = requests.Session()

    def consultar_bitrix(
        self, 
        table: str, 
        filtros: Optional[Dict[str, Any]] = None
    ) -> Optional[List[List[Any]]]:
        """
        Consulta a API do Bitrix24 com retry em caso de falha
        
        Args:
            table: Nome da tabela/entidade no Bitrix24
            filtros: Filtros a serem aplicados na consulta
            
        Returns:
            Lista de listas com os dados retornados ou None em caso de erro
        """
        url = f"{self.base_url}?token={self.token}&table={table}"
        retries = 0
        
        while retries < self.max_retries:
            try:
                if filtros:
                    response = self._session.post(
                        url,
                        json=filtros,
                        timeout=self.timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                else:
                    response = self._session.get(url, timeout=self.timeout)
                
                response.raise_for_status()
                data = response.json()
                
                if not data or len(data) < 2:  # Deve ter pelo menos cabeçalho e dados
                    raise requests.exceptions.RequestException("Resposta vazia ou inválida")
                    
                return data
            
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries == self.max_retries:
                    st.error(f"Erro ao consultar Bitrix24: {e}")
                    return None
                time.sleep(1)  # Espera 1 segundo antes de tentar novamente

    def get_deals_category_32(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Busca deals da categoria 32 e seus campos personalizados
        
        Returns:
            Tuple contendo dois DataFrames:
            - Primeiro DataFrame com os dados básicos dos deals
            - Segundo DataFrame com os campos personalizados
        """
        # Filtro para categoria 32
        filtros_deal = {
            "dimensionsFilters": [[{
                "fieldName": "CATEGORY_ID",
                "values": [32],
                "type": "INCLUDE",
                "operator": "EQUALS"
            }]],
            "fields": [
                {"name": "ID"},
                {"name": "TITLE"},
                {"name": "STAGE_ID"},
                {"name": "STAGE_NAME"},
                {"name": "CATEGORY_ID"}
            ]
        }
        
        # Buscar deals
        deals_data = self.consultar_bitrix("crm_deal", filtros_deal)
        if not deals_data:
            return None, None
        
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        
        # Buscar campos personalizados
        deal_ids = deals_df['ID'].tolist()
        chunks = [deal_ids[i:i+100] for i in range(0, len(deal_ids), 100)]
        
        all_uf_data = []
        for chunk in chunks:
            filtros_uf = {
                "dimensionsFilters": [[{
                    "fieldName": "DEAL_ID",
                    "values": chunk,
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }]],
                "fields": [
                    {"name": "DEAL_ID"},
                    {"name": "UF_CRM_1722605592778"},
                    {"name": "UF_CRM_1738699062493"}
                ]
            }
            
            uf_data = self.consultar_bitrix("crm_deal_uf", filtros_uf)
            if uf_data:
                all_uf_data.extend(uf_data[1:] if len(all_uf_data) > 0 else uf_data)
        
        if not all_uf_data:
            return deals_df, None
        
        deals_uf_df = pd.DataFrame(all_uf_data[1:], columns=all_uf_data[0])
        return deals_df, deals_uf_df

    def analisar_deals(self) -> Optional[Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]]:
        """
        Analisa os deals da categoria 32
        
        Returns:
            Tupla contendo:
            - Dicionário com métricas
            - DataFrame com detalhamento
            - DataFrame completo
            Ou None em caso de erro
        """
        try:
            # 1. Consultar crm_deal (categoria 32 - Negociação de Taxa)
            filtros_deal = {
                "dimensionsFilters": [[{
                    "fieldName": "CATEGORY_ID",
                    "values": [32],
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }]],
                "select": [
                    "ID", "TITLE", "DATE_CREATE", "ASSIGNED_BY_NAME", 
                    "STAGE_ID", "STAGE_NAME", "CATEGORY_NAME"
                ]
            }
            
            deals_data = self.consultar_bitrix("crm_deal", filtros_deal)
            if not deals_data:
                st.error("Não foi possível obter os dados de negócios")
                return None
            
            # Converter para DataFrame
            deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
            if deals_df.empty:
                st.warning("Nenhum negócio encontrado na categoria 32")
                return None
            
            # 2. Consultar campos personalizados
            deal_ids = deals_df["ID"].tolist()
            filtros_uf = {
                "dimensionsFilters": [[{
                    "fieldName": "DEAL_ID",
                    "values": deal_ids,
                    "type": "INCLUDE",
                    "operator": "EQUALS"
                }]],
                "select": ["DEAL_ID", "UF_CRM_1738699062493"]
            }
            
            deals_uf_data = self.consultar_bitrix("crm_deal_uf", filtros_uf)
            if not deals_uf_data:
                st.error("Não foi possível obter os dados complementares")
                return None
            
            deals_uf_df = pd.DataFrame(deals_uf_data[1:], columns=deals_uf_data[0])
            
            # 3. Mesclar os dataframes
            df_completo = pd.merge(
                deals_df,
                deals_uf_df[["DEAL_ID", "UF_CRM_1738699062493"]],
                left_on="ID",
                right_on="DEAL_ID",
                how="left"
            )
            
            # 4. Calcular métricas
            metricas = {
                "total_negocios": len(df_completo),
                "categoria_name": df_completo["CATEGORY_NAME"].iloc[0] if not df_completo.empty else "N/A",
                "com_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""]),
                "sem_conteudo": len(df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() == ""]),
                "stage_negociacao": df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]["STAGE_NAME"].iloc[0] if not df_completo.empty else "N/A",
                "total_stage_negociacao": len(df_completo[df_completo["STAGE_ID"] == "C32:UC_GBPN8V"]),
                "com_conteudo_em_negociacao": len(df_completo[
                    (df_completo["STAGE_ID"] == "C32:UC_GBPN8V") & 
                    (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
                ]),
                "com_conteudo_fora_negociacao": len(df_completo[
                    (df_completo["STAGE_ID"] != "C32:UC_GBPN8V") & 
                    (df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != "")
                ])
            }
            
            # 5. Preparar dados detalhados
            detalhamento = []
            for _, row in df_completo[df_completo["UF_CRM_1738699062493"].astype(str).str.strip() != ""].iterrows():
                detalhamento.append({
                    "ID": row["ID"],
                    "Título": row["TITLE"],
                    "Data Criação": pd.to_datetime(row["DATE_CREATE"]).strftime("%d/%m/%Y"),
                    "Responsável": row["ASSIGNED_BY_NAME"],
                    "Etapa": row["STAGE_NAME"],
                    "Status": "GEROU O LINK"
                })
            
            df_detalhamento = pd.DataFrame(detalhamento)
            df_detalhamento = df_detalhamento.sort_values(by="ID", ascending=False)
            
            return metricas, df_detalhamento, df_completo
            
        except Exception as e:
            st.error(f"Erro ao analisar dados: {str(e)}")
            return None

# Instância global
bitrix_service = BitrixService()