from datetime import datetime, timedelta

def get_deals_filter(start_date=None, end_date=None, category_id=32):
    """
    Cria filtro otimizado para consulta de deals
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "dateRange": {
            "startDate": start_date,
            "endDate": end_date
        },
        "configParams": {
            "timeFilterColumn": "DATE_CREATE"
        },
        "dimensionsFilters": [[
            {
                "fieldName": "CATEGORY_ID",
                "values": [category_id],
                "type": "INCLUDE",
                "operator": "EQUALS"
            }
        ]],
        "fields": [
            {"name": "ID"},
            {"name": "TITLE"},
            {"name": "DATE_CREATE"},
            {"name": "STAGE_ID"},
            {"name": "STAGE_SEMANTIC_ID"},
            {"name": "CONTACT_ID"},
            {"name": "CONTACT_NAME"}
        ]
    }

def get_deal_uf_filter(deal_ids=None):
    """
    Cria filtro otimizado para campos personalizados
    """
    filter_params = {
        "fields": [
            {"name": "DEAL_ID"},
            {"name": "UF_CRM_1722605592778"},  # ID da família
            {"name": "UF_CRM_1715112972761"},  # Campo adicional relevante
            {"name": "UF_CRM_HUGGY"},          # Integração Huggy
            {"name": "UF_CRM_1725546396754"}   # Outro campo relevante
        ]
    }
    
    if deal_ids:
        filter_params["dimensionsFilters"] = [[
            {
                "fieldName": "DEAL_ID",
                "values": deal_ids,
                "type": "INCLUDE",
                "operator": "EQUALS"
            }
        ]]
    
    return filter_params