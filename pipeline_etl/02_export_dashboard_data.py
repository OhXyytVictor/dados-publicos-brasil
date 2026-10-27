"""
==============================================================================
PROJETO: Pipeline Macroeconomico - Dados Abertos Banco Central e IBGE
ARQUIVO: 02_export_dashboard_data.py
AUTOR: Victor Ramos
OBJETIVO: Exportar as views analiticas do PostgreSQL para JSON, consumido
          pelo dashboard interativo estatico (docs/dashboard_macro.html)
==============================================================================
"""

import json
import os

import psycopg2

DATABASE_URI = "postgresql://postgres:5336@localhost:5432/postgres"
OUTPUT_PATH = os.path.join("docs", "macro_data.json")

Q_MENSAL = """
SELECT ano_mes, ipca_mensal_pct, selic_mensal_pct, cambio_dolar_brl,
       indice_volume_vendas, vendas_media_movel_12m
FROM macroeconomia.vw_indicadores_consolidados
ORDER BY data;
"""

Q_ANUAL = """
SELECT ano, dolar_medio_ano, ipca_acumulado_ano, selic_anualizada_media,
       indice_vendas_medio, dolar_minimo, dolar_maximo
FROM macroeconomia.vw_ciclos_cambiais_tecnologia
ORDER BY ano;
"""


def to_float(value):
    return float(value) if value is not None else None


def main():
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()

    cur.execute(Q_MENSAL)
    mensal = [[r[0]] + [to_float(x) for x in r[1:]] for r in cur.fetchall()]

    cur.execute(Q_ANUAL)
    anual = [[r[0]] + [to_float(x) for x in r[1:]] for r in cur.fetchall()]
    conn.close()

    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        json.dump({"mensal": mensal, "anual": anual}, fp, separators=(",", ":"))

    print(f"[PASS] {len(mensal)} meses e {len(anual)} anos exportados para {OUTPUT_PATH}")

    # Injeta os dados no template para o dashboard funcionar tambem via file://
    template_path = os.path.join("docs", "dashboard_macro.template.html")
    with open(template_path, "r", encoding="utf-8") as fp:
        html = fp.read()
    payload = json.dumps({"mensal": mensal, "anual": anual}, separators=(",", ":"))
    with open(os.path.join("docs", "dashboard_macro.html"), "w", encoding="utf-8") as fp:
        fp.write(html.replace("/*DATA*/", payload))
    print("[PASS] docs/dashboard_macro.html gerado")


if __name__ == "__main__":
    main()
