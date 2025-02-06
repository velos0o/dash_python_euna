def get_family_status_query():
    return """
    WITH dados_completos AS (
        SELECT 
            f.idfamilia,
            f.nome_completo,
            f.telefone,
            f.email,
            f.is_menor,
            f.birthdate,
            f.paymentOption,
            TIMESTAMPDIFF(YEAR, f.birthdate, CURDATE()) as idade,
            COUNT(DISTINCT m.unique_id) as total_membros
        FROM euna_familias f
        LEFT JOIN familias m ON f.idfamilia = m.unique_id
        GROUP BY 
            f.idfamilia, f.nome_completo, f.telefone, f.email,
            f.is_menor, f.birthdate, f.paymentOption
    )
    SELECT 
        idfamilia,
        GROUP_CONCAT(
            CASE 
                WHEN paymentOption IS NULL OR paymentOption = '' 
                THEN CONCAT_WS(' | ',
                    nome_completo,
                    telefone,
                    email,
                    CONCAT('Idade: ', idade),
                    CASE WHEN is_menor = 1 THEN 'Menor de idade' ELSE 'Maior de idade' END
                )
            END
            SEPARATOR '\n'
        ) as pessoas_sem_opcao,
        SUM(CASE WHEN paymentOption IN ('A', 'B', 'C', 'D') THEN 1 ELSE 0 END) as continua,
        SUM(CASE WHEN paymentOption = 'E' THEN 1 ELSE 0 END) as cancelou,
        MAX(total_membros) as total_membros
    FROM dados_completos
    GROUP BY idfamilia
    """