import requests
import pandas as pd
from typing import Optional, Dict, Any, Tuple

class Bitrix24API:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self._session = requests.Session()
    
    def _make_request(self, table: str, filtros: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Faz requisição para a API do Bitrix24 com retry e timeout"""
        url = f"{self.base_url}?token={self.token}&table={table}"
        
        try:
            if filtros:
                response = self._session.post(url, json=filtros, timeout=30)
            else:
                response = self._session.get(url, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None
    
    def get_deals_category_32(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Busca deals da categoria 32 e seus campos personalizados"""
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
        deals_data = self._make_request("crm_deal", filtros_deal)
        if not deals_data:
            return None, None
        
        deals_df = pd.DataFrame(deals_data[1:], columns=deals_data[0])
        
        # Buscar campos personalizados apenas para os IDs encontrados
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
            
            uf_data = self._make_request("crm_deal_uf", filtros_uf)
            if uf_data:
                all_uf_data.extend(uf_data[1:] if len(all_uf_data) > 0 else uf_data)
        
        if not all_uf_data:
            return deals_df, None
        
        deals_uf_df = pd.DataFrame(all_uf_data[1:], columns=all_uf_data[0])
        return deals_df, deals_uf_df