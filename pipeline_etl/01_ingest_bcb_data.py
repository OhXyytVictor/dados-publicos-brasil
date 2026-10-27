"""
==============================================================================
PROJETO: Pipeline Macroeconomico - Dados Abertos Banco Central e IBGE
ARQUIVO: 01_ingest_bcb_data.py
AUTOR: Victor Ramos
OBJETIVO: Ingestao automatizada de series temporais publicas da API do BCB
==============================================================================
"""

import sys
import requests
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URI = "postgresql://postgres:5336@localhost:5432/postgres"

# Mapeamento oficial de series temporais do Banco Central do Brasil (SGS)
SERIES_CONFIG = {
    "ipca_mensal": {
        "id": 433,
        "descricao": "IPCA - Variacao mensal (%)"
    },
    "taxa_selic_acumulada_mes": {
        "id": 4390,
        "descricao": "Taxa de juros - Selic acumulada no mes (%)"
    },
    "cambio_dolar_mensal": {
        "id": 3696,
        "descricao": "Taxa de cambio - Dolar americano (R$ / US$) - Media mensal"
    },
    "indice_volume_vendas_tecnologia": {
        "id": 1455,
        "descricao": "Indice de volume de vendas no varejo - Equipamentos e informatica (IBGE/PMC)"
    }
}

def fetch_series(series_id):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?formato=json"
    headers = {"User-Agent": "Portfolio-Dados-Analytics/1.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df

def main():
    print("[INFO] Iniciando pipeline de ingestao de dados abertos macroeconomicos...")
    engine = create_engine(DATABASE_URI)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS macroeconomia;"))

    dfs = {}
    for name, cfg in SERIES_CONFIG.items():
        print(f"[INFO] Coletando serie {cfg['id']} ({name})...")
        df_series = fetch_series(cfg["id"])
        # Filtra a partir do ano 2000 para manter consistencia do Plano Real consolidado
        df_series = df_series[df_series["data"] >= "2000-01-01"].copy()
        df_series.rename(columns={"valor": name}, inplace=True)
        dfs[name] = df_series

    print("[INFO] Consolidando series temporais em matriz mensal...")
    # Base principal: IPCA
    df_merged = dfs["ipca_mensal"]
    for name in ["taxa_selic_acumulada_mes", "cambio_dolar_mensal", "indice_volume_vendas_tecnologia"]:
        df_merged = pd.merge(df_merged, dfs[name], on="data", how="left")

    df_merged["ano_mes"] = df_merged["data"].dt.strftime("%Y-%m")
    df_merged.sort_values("data", inplace=True)
    df_merged.reset_index(drop=True, inplace=True)

    print(f"[INFO] Inserindo {len(df_merged)} meses historicos no PostgreSQL...")
    df_merged.to_sql(
        "fato_indicadores_macro",
        engine,
        schema="macroeconomia",
        if_exists="replace",
        index=False
    )

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE macroeconomia.fato_indicadores_macro 
            ADD CONSTRAINT pk_fato_indicadores PRIMARY KEY (data);
            CREATE INDEX IF NOT EXISTS idx_macro_anomes ON macroeconomia.fato_indicadores_macro(ano_mes);
        """))

    print("[INFO] Ingestao de dados macroeconomicos concluida com sucesso!")

if __name__ == "__main__":
    main()
