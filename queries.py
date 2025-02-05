def get_family_status_query():
    return """
    WITH status_atual AS (
        SELECT 
            idfamilia,
            GROUP_CONCAT(
                CASE 
                    WHEN paymentOption IS NULL OR paymentOption = '' 
                    THEN CONCAT_WS(' | ',
                        nome_completo,
                        telefone,
                        `e-mail`,
                        CONCAT('Idade: ', TIMESTAMPDIFF(YEAR, birthdate, CURDATE())),
                        CASE 
                            WHEN is_menor = 1 THEN 'Menor de idade'
                            ELSE 'Maior de idade'
                        END
                    )
                END
                SEPARATOR '\n'
            ) as pessoas_sem_opcao,
            COUNT(CASE 
                WHEN paymentOption IN ('A', 'B', 'C', 'D') THEN 1 
            END) as continua,
            COUNT(CASE 
                WHEN paymentOption = 'E' THEN 1 
            END) as cancelou,
            COUNT(*) as total_atual
        FROM euna_familias
        GROUP BY idfamilia
    )
    SELECT 
        idfamilia,
        pessoas_sem_opcao,
        continua,
        cancelou,
        total_atual,
        total_atual as total_esperado
    FROM status_atual
    """

def get_payment_options_query():
    return """
    SELECT 
        paymentOption,
        COUNT(*) as total,
        GROUP_CONCAT(
            CONCAT(
                nome_completo,
                CASE 
                    WHEN is_menor = 1 THEN ' (Menor)'
                    WHEN TIMESTAMPDIFF(YEAR, birthdate, CURDATE()) >= 12 THEN ' (Maior 12)'
                    ELSE ' (Menor 12)'
                END
            )
            ORDER BY nome_completo
            SEPARATOR ', '
        ) as pessoas
    FROM euna_familias
    WHERE paymentOption IS NOT NULL AND paymentOption != ''
    GROUP BY paymentOption
    ORDER BY 
        CASE paymentOption
            WHEN 'A' THEN 1
            WHEN 'B' THEN 2
            WHEN 'C' THEN 3
            WHEN 'D' THEN 4
            WHEN 'E' THEN 5
            ELSE 6
        END
    """

def get_deals_without_stage_query():
    return """
    SELECT 
        d.ID,
        d.TITLE,
        d.STAGE_ID,
        d.STAGE_NAME
    FROM crm_deal d
    JOIN crm_deal_uf uf ON d.ID = uf.DEAL_ID
    WHERE 
        d.CATEGORY_ID = 32
        AND uf.UF_CRM_1738699062493 IS NOT NULL 
        AND uf.UF_CRM_1738699062493 != ''
        AND d.STAGE_ID != 'C32:UC_GBPN8V'
    """