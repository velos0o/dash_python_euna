def get_family_status_query():
    return """
    WITH requerentes_por_familia AS (
        SELECT 
            familia,
            COUNT(DISTINCT unique_id) as total_requerentes_esperado
        FROM familiares
        GROUP BY familia
    ),
    status_atual AS (
        SELECT 
            ef.idfamilia,
            GROUP_CONCAT(
                CASE 
                    WHEN ef.paymentOption IS NULL OR ef.paymentOption = '' 
                    THEN CONCAT_WS(' | ',
                        COALESCE(f.nome_familia, ef.nome_completo),
                        CONCAT('CPF: ', COALESCE(f.cpf, 'Não informado')),
                        CONCAT('RG: ', COALESCE(f.rg, 'Não informado')),
                        CONCAT('Passaporte: ', COALESCE(f.passaporte, 'Não informado')),
                        CONCAT('WhatsApp: ', COALESCE(f.whatsapp, ef.telefone, 'Não informado')),
                        CONCAT('Email: ', COALESCE(ef.`e-mail`, 'Não informado')),
                        CONCAT('Idade: ', TIMESTAMPDIFF(YEAR, ef.birthdate, CURDATE())),
                        CASE 
                            WHEN ef.is_menor = 1 THEN 'Menor de idade'
                            ELSE 'Maior de idade'
                        END
                    )
                END
                SEPARATOR '\n'
            ) as pessoas_sem_opcao,
            SUM(CASE 
                WHEN ef.paymentOption IN ('A', 'B', 'C', 'D') AND (
                    ef.is_menor = 0 OR 
                    TIMESTAMPDIFF(YEAR, ef.birthdate, CURDATE()) >= 12
                ) THEN 1 
                ELSE 0 
            END) as continua,
            SUM(CASE 
                WHEN ef.paymentOption = 'E' THEN 1 
                ELSE 0 
            END) as cancelou,
            COUNT(*) as total_atual
        FROM euna_familias ef
        LEFT JOIN familiares f ON ef.idfamilia = f.familia
        GROUP BY ef.idfamilia
    )
    SELECT 
        sa.idfamilia,
        sa.pessoas_sem_opcao,
        sa.continua,
        sa.cancelou,
        sa.total_atual,
        COALESCE(rpf.total_requerentes_esperado, 0) as total_requerentes_esperado
    FROM status_atual sa
    LEFT JOIN requerentes_por_familia rpf ON sa.idfamilia = rpf.familia
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