def get_family_status_query():
    return """
    WITH analise_familias AS (
        SELECT 
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            -- Contagem por opção
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            -- Pessoas sem opção
            SUM(CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
            -- Total de pessoas na euna_familias
            COUNT(*) as Total_euna,
            -- Status da família
            CASE 
                WHEN SUM(CASE WHEN e.paymentOption IN ('A','B','C','D') THEN 1 ELSE 0 END) > 0 THEN 'Continua'
                WHEN SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) > 0 THEN 'Cancelou'
                ELSE 'Pendente'
            END as status_familia,
            -- Informações adicionais
            GROUP_CONCAT(
                CASE WHEN e.paymentOption IS NULL OR e.paymentOption = '' 
                THEN CONCAT_WS(' | ',
                    e.nome_completo,
                    e.telefone,
                    e.`e-mail`,
                    CASE WHEN e.is_menor = 1 THEN 'Menor' ELSE 'Maior' END
                )
                END
                SEPARATOR '\n'
            ) as pessoas_sem_opcao
        FROM euna_familias e
        LEFT JOIN familiares f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0
          AND e.isSpecial = 0
          AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia

        UNION ALL

        -- Linha de totais
        SELECT 
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(CASE WHEN paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            SUM(CASE WHEN paymentOption IS NULL OR paymentOption = '' THEN 1 ELSE 0 END) AS Sem_Opcao,
            COUNT(*) as Total_euna,
            'Total' as status_familia,
            NULL as pessoas_sem_opcao
        FROM euna_familias
        WHERE is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
    ),
    contagem_requerentes AS (
        -- Contagem esperada de requerentes por família
        SELECT 
            familia as ID_Familia,
            COUNT(DISTINCT unique_id) as total_requerentes_esperado
        FROM familiares
        GROUP BY familia
    )
    SELECT 
        a.*,
        COALESCE(c.total_requerentes_esperado, 0) as total_requerentes_esperado,
        COALESCE(c.total_requerentes_esperado, 0) - a.Total_euna as diferenca_requerentes
    FROM analise_familias a
    LEFT JOIN contagem_requerentes c ON a.ID_Familia = c.ID_Familia
    ORDER BY 
        CASE WHEN a.Nome_Familia = 'Total' THEN 1 ELSE 0 END,
        a.ID_Familia
    WITH status_familias AS (
        -- Status por família com opções de pagamento
        SELECT 
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            CASE 
                WHEN SUM(CASE WHEN e.paymentOption IN ('A','B','C','D') THEN 1 ELSE 0 END) > 0 THEN 'Continua'
                WHEN SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) > 0 THEN 'Cancelou'
                ELSE 'Sem Status'
            END as status_familia
        FROM euna_familias e
        LEFT JOIN familiares f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0
          AND e.isSpecial = 0
          AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia

        UNION ALL

        -- Linha de totais
        SELECT 
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(CASE WHEN paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            'Total' as status_familia
        FROM euna_familias
        WHERE is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
    ),
    contagem_requerentes AS (
        -- Contagem de requerentes por família da tabela familiares
        SELECT 
            familia as ID_Familia,
            COUNT(DISTINCT unique_id) as total_requerentes_esperado
        FROM familiares
        GROUP BY familia
    )
    SELECT 
        s.*,
        COALESCE(c.total_requerentes_esperado, 0) as total_requerentes_esperado
    FROM status_familias s
    LEFT JOIN contagem_requerentes c ON s.ID_Familia = c.ID_Familia
    ORDER BY 
        CASE WHEN s.Nome_Familia = 'Total' THEN 1 ELSE 0 END,
        s.ID_Familia
    WITH dados_familia AS (
        SELECT 
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E
        FROM euna_familias e
        LEFT JOIN familiares f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0
          AND e.isSpecial = 0
          AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia

        UNION ALL

        SELECT 
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(CASE WHEN paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) AS E
        FROM euna_familias
        WHERE is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
    )
    SELECT *
    FROM dados_familia
    ORDER BY 
        CASE WHEN Nome_Familia = 'Total' THEN 1 ELSE 0 END,
        ID_Familia
    WITH requerentes_por_familia AS (
        SELECT 
            familia,
            COUNT(DISTINCT id) as total_requerentes
        FROM familiares
        WHERE is_requerente_principal = 1
           OR is_conjuge = 1
           OR (is_familiar = 1 AND is_menor = 0)
        GROUP BY familia
    ),
    status_familia AS (
        SELECT 
            e.idfamilia AS ID_Familia,
            COALESCE(f.nome_familia, 'Sem Nome') AS Nome_Familia,
            SUM(CASE WHEN e.paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN e.paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN e.paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN e.paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN e.paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            GROUP_CONCAT(
                CASE 
                    WHEN e.paymentOption IS NULL OR e.paymentOption = '' 
                    THEN CONCAT_WS(' | ',
                        e.nome_completo,
                        e.telefone,
                        e.`e-mail`,
                        CONCAT('Idade: ', TIMESTAMPDIFF(YEAR, e.birthdate, CURDATE())),
                        CASE WHEN e.is_menor = 1 THEN 'Menor de idade' ELSE 'Maior de idade' END
                    )
                END
                SEPARATOR '\n'
            ) as pessoas_sem_opcao
        FROM euna_familias e
        LEFT JOIN familiares f ON TRIM(e.idfamilia) = TRIM(f.unique_id)
        WHERE e.is_menor = 0
          AND e.isSpecial = 0
          AND e.hasTechnicalProblems = 0
        GROUP BY e.idfamilia, f.nome_familia
    ),
    totais AS (
        SELECT 
            'TOTAL' AS ID_Familia,
            'Total' AS Nome_Familia,
            SUM(CASE WHEN paymentOption = 'A' THEN 1 ELSE 0 END) AS A,
            SUM(CASE WHEN paymentOption = 'B' THEN 1 ELSE 0 END) AS B,
            SUM(CASE WHEN paymentOption = 'C' THEN 1 ELSE 0 END) AS C,
            SUM(CASE WHEN paymentOption = 'D' THEN 1 ELSE 0 END) AS D,
            SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) AS E,
            NULL as pessoas_sem_opcao
        FROM euna_familias
        WHERE is_menor = 0
          AND isSpecial = 0
          AND hasTechnicalProblems = 0
    )
    SELECT 
        r.ID_Familia as idfamilia,
        r.Nome_Familia as nome_familia,
        r.A,
        r.B,
        r.C,
        r.D,
        r.E,
        r.pessoas_sem_opcao,
        (r.A + r.B + r.C + r.D) as continua,
        r.E as cancelou,
        (r.A + r.B + r.C + r.D + r.E) as total_atual,
        COALESCE(rpf.total_requerentes, 0) as total_esperado
    FROM (
        SELECT * FROM status_familia
        UNION ALL
        SELECT * FROM totais
    ) r
    LEFT JOIN requerentes_por_familia rpf ON TRIM(r.ID_Familia) = TRIM(rpf.familia)
    ORDER BY 
        CASE WHEN r.Nome_Familia = 'Total' THEN 1 ELSE 0 END,
        r.ID_Familia
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