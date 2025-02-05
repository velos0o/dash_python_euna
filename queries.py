def get_family_status_query():
    return """
    WITH sem_opcao_pagamento AS (
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
                        END,
                        CASE 
                            WHEN f.is_requerente_principal = 1 THEN 'Requerente Principal'
                            ELSE 'Dependente'
                        END,
                        CASE 
                            WHEN f.is_italiano = 1 THEN 'Italiano'
                            ELSE 'Não Italiano'
                        END,
                        CASE 
                            WHEN ef.isSpecial = 1 THEN 'Caso Especial'
                            ELSE ''
                        END,
                        CASE 
                            WHEN ef.hasTechnicalProblems = 1 THEN 'Problemas Técnicos'
                            ELSE ''
                        END,
                        CASE 
                            WHEN ef.aire = 1 THEN 'AIRE'
                            ELSE ''
                        END
                    )
                END
                SEPARATOR '\n'
            ) as pessoas_sem_opcao
        FROM euna_familias ef
        LEFT JOIN familiares f ON ef.idfamilia = f.unique_id
        WHERE ef.paymentOption IS NULL OR ef.paymentOption = ''
        GROUP BY ef.idfamilia
    ),
    contagem_status AS (
        SELECT 
            idfamilia,
            SUM(CASE WHEN paymentOption IN ('A', 'B', 'C', 'D') THEN 1 ELSE 0 END) as continua,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) as cancelou
        FROM euna_familias
        GROUP BY idfamilia
    ),
    total_membros AS (
        SELECT 
            unique_id as idfamilia,
            COUNT(DISTINCT id) as total_membros
        FROM familiares
        GROUP BY unique_id
    )
    SELECT 
        cs.idfamilia,
        COALESCE(sop.pessoas_sem_opcao, '') as pessoas_sem_opcao,
        cs.continua,
        cs.cancelou,
        COALESCE(tm.total_membros, 0) as total_membros
    FROM contagem_status cs
    LEFT JOIN sem_opcao_pagamento sop ON cs.idfamilia = sop.idfamilia
    LEFT JOIN total_membros tm ON cs.idfamilia = tm.idfamilia
    """

def get_payment_options_query():
    return """
    SELECT 
        paymentOption,
        COUNT(*) as total,
        GROUP_CONCAT(DISTINCT nome_completo SEPARATOR ', ') as pessoas
    FROM euna_familias
    WHERE paymentOption IS NOT NULL AND paymentOption != ''
    GROUP BY paymentOption
    ORDER BY paymentOption
    """