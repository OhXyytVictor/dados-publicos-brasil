-- ==============================================================================
-- PROJETO: Pipeline Macroeconomico - Dados Abertos Banco Central e IBGE
-- ARQUIVO: 01_schema_macroeconomia.sql
-- AUTOR: Victor Ramos
-- OBJETIVO: Criacao de views analiticas e semantic layer macroeconomica
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS macroeconomia;

-- 1. View Semantica: Indicadores Consolidados com Variacoes Temporais
DROP VIEW IF EXISTS macroeconomia.vw_indicadores_consolidados CASCADE;
CREATE VIEW macroeconomia.vw_indicadores_consolidados AS
SELECT 
    data,
    ano_mes,
    ROUND(ipca_mensal::NUMERIC, 2) AS ipca_mensal_pct,
    ROUND(taxa_selic_acumulada_mes::NUMERIC, 2) AS selic_mensal_pct,
    ROUND(cambio_dolar_mensal::NUMERIC, 4) AS cambio_dolar_brl,
    ROUND(indice_volume_vendas_tecnologia::NUMERIC, 2) AS indice_volume_vendas,
    -- Variacao MoM do Dolar
    ROUND(
        ((cambio_dolar_mensal - LAG(cambio_dolar_mensal) OVER (ORDER BY data)) 
        / NULLIF(LAG(cambio_dolar_mensal) OVER (ORDER BY data), 0) * 100)::NUMERIC, 
        2
    ) AS dolar_variacao_mom_pct,
    -- Medias moveis de vendas de tecnologia (3 meses e 12 meses)
    ROUND(
        AVG(indice_volume_vendas_tecnologia) OVER (
            ORDER BY data ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )::NUMERIC, 
        2
    ) AS vendas_media_movel_3m,
    ROUND(
        AVG(indice_volume_vendas_tecnologia) OVER (
            ORDER BY data ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        )::NUMERIC, 
        2
    ) AS vendas_media_movel_12m
FROM macroeconomia.fato_indicadores_macro;

-- 2. View Analitica: Ciclos Cambiais e Elasticidade de Vendas
DROP VIEW IF EXISTS macroeconomia.vw_ciclos_cambiais_tecnologia CASCADE;
CREATE VIEW macroeconomia.vw_ciclos_cambiais_tecnologia AS
SELECT 
    TO_CHAR(data, 'YYYY') AS ano,
    ROUND(AVG(cambio_dolar_mensal)::NUMERIC, 2) AS dolar_medio_ano,
    ROUND(SUM(ipca_mensal)::NUMERIC, 2) AS ipca_acumulado_ano,
    ROUND(AVG(taxa_selic_acumulada_mes * 12)::NUMERIC, 2) AS selic_anualizada_media,
    ROUND(AVG(indice_volume_vendas_tecnologia)::NUMERIC, 2) AS indice_vendas_medio,
    ROUND(MIN(cambio_dolar_mensal)::NUMERIC, 2) AS dolar_minimo,
    ROUND(MAX(cambio_dolar_mensal)::NUMERIC, 2) AS dolar_maximo
FROM macroeconomia.fato_indicadores_macro
WHERE data >= '2010-01-01'
GROUP BY TO_CHAR(data, 'YYYY')
ORDER BY ano DESC;
