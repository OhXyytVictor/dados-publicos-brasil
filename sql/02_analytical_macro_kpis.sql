-- ==============================================================================
-- PROJETO: Pipeline Macroeconomico - Dados Abertos Banco Central e IBGE
-- ARQUIVO: 02_analytical_macro_kpis.sql
-- AUTOR: Victor Ramos
-- OBJETIVO: Consultas analiticas de impacto macroeconomico no varejo de tecnologia
-- ==============================================================================

-- 1. Analise de Impacto de Choques Cambiais no Volume de Vendas de Tecnologia
-- Compara meses com alta expressiva do dolar (> 2,5% MoM) contra a media movel de vendas
WITH variacao_cambial AS (
    SELECT 
        ano_mes,
        cambio_dolar_brl,
        dolar_variacao_mom_pct,
        indice_volume_vendas,
        vendas_media_movel_3m,
        CASE 
            WHEN dolar_variacao_mom_pct > 3.0 THEN 'Choque de Alta do Dolar (> 3%)'
            WHEN dolar_variacao_mom_pct < -3.0 THEN 'Apreciacao do Real (< -3%)'
            ELSE 'Estabilidade Cambial'
        END AS regime_cambial
    FROM macroeconomia.vw_indicadores_consolidados
    WHERE indice_volume_vendas IS NOT NULL
)
SELECT 
    regime_cambial,
    COUNT(*) AS total_meses,
    ROUND(AVG(dolar_variacao_mom_pct)::NUMERIC, 2) AS variacao_dolar_media_pct,
    ROUND(AVG(indice_volume_vendas)::NUMERIC, 2) AS indice_vendas_medio,
    ROUND(AVG(vendas_media_movel_3m)::NUMERIC, 2) AS media_movel_vendas_3m
FROM variacao_cambial
GROUP BY regime_cambial
ORDER BY indice_vendas_medio DESC;

-- 2. Segmentacao de Pressao Macroeconomica em Quartis (NTILE)
-- Cruza nivel de Selic e Dolar para classificar o ambiente de consumo de bens duraveis
WITH quartis_macro AS (
    SELECT 
        ano_mes,
        cambio_dolar_brl,
        selic_mensal_pct,
        indice_volume_vendas,
        NTILE(4) OVER (ORDER BY cambio_dolar_brl ASC) AS quartil_dolar,
        NTILE(4) OVER (ORDER BY selic_mensal_pct ASC) AS quartil_juros
    FROM macroeconomia.vw_indicadores_consolidados
    WHERE indice_volume_vendas IS NOT NULL
)
SELECT 
    CASE 
        WHEN quartil_dolar <= 2 AND quartil_juros <= 2 THEN 'Cenario Favoravel (Dolar Baixo e Juros Baixos)'
        WHEN quartil_dolar >= 3 AND quartil_juros >= 3 THEN 'Cenario Severo (Dolar Alto e Juros Restritivos)'
        ELSE 'Cenario Moderado'
    END AS ambiente_macroeconomico,
    COUNT(*) AS meses_observados,
    ROUND(AVG(cambio_dolar_brl)::NUMERIC, 2) AS dolar_medio,
    ROUND(AVG(selic_mensal_pct)::NUMERIC, 2) AS selic_mensal_media,
    ROUND(AVG(indice_volume_vendas)::NUMERIC, 2) AS volume_vendas_medio
FROM quartis_macro
GROUP BY 
    CASE 
        WHEN quartil_dolar <= 2 AND quartil_juros <= 2 THEN 'Cenario Favoravel (Dolar Baixo e Juros Baixos)'
        WHEN quartil_dolar >= 3 AND quartil_juros >= 3 THEN 'Cenario Severo (Dolar Alto e Juros Restritivos)'
        ELSE 'Cenario Moderado'
    END
ORDER BY volume_vendas_medio DESC;
