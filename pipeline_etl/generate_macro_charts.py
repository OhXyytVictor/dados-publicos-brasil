"""
==============================================================================
PROJETO: Pipeline Macroeconomico - Dados Abertos Banco Central e IBGE
ARQUIVO: generate_macro_charts.py
AUTOR: Victor Ramos
OBJETIVO: Geracao de graficos analiticos minimalistas seguindo storytelling
==============================================================================
"""

import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

OUTPUT_DIR = "docs/img"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATABASE_URI = "postgresql://postgres:5336@localhost:5432/postgres"

def set_minimal_style():
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.edgecolor"] = "#cbd5e1"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["text.color"] = "#1e293b"
    plt.rcParams["axes.labelcolor"] = "#475569"
    plt.rcParams["xtick.color"] = "#64748b"
    plt.rcParams["ytick.color"] = "#64748b"
    plt.rcParams["figure.facecolor"] = "#ffffff"
    plt.rcParams["axes.facecolor"] = "#ffffff"

def generate_chart_1(conn):
    print("[INFO] Gerando Grafico 1: Serie Temporal Dolar vs Vendas de Tecnologia...")
    query = """
        SELECT 
            data,
            cambio_dolar_brl,
            vendas_media_movel_12m
        FROM macroeconomia.vw_indicadores_consolidados
        WHERE data >= '2015-01-01' AND vendas_media_movel_12m IS NOT NULL
        ORDER BY data;
    """
    df = pd.read_sql(query, conn)
    df["data"] = pd.to_datetime(df["data"])

    fig, ax1 = plt.subplots(figsize=(10, 4.5), dpi=200)

    color_dolar = "#2563eb"  # Azul escuro
    color_vendas = "#64748b" # Cinza azulado

    ax1.plot(df["data"], df["cambio_dolar_brl"], color=color_dolar, linewidth=2.2, label="Dolar Comercial (R$)")
    ax1.set_ylabel("Cotacao Media do Dolar (R$)", color=color_dolar, fontsize=10, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=color_dolar)
    ax1.grid(True, linestyle="--", alpha=0.3, color="#94a3b8")
    ax1.spines["top"].set_visible(False)

    ax2 = ax1.twinx()
    ax2.plot(df["data"], df["vendas_media_movel_12m"], color=color_vendas, linewidth=1.8, linestyle="--", label="Vendas Tecnologia (Media Movel 12M)")
    ax2.set_ylabel("Indice de Vendas (IBGE/PMC)", color=color_vendas, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=color_vendas)
    ax2.spines["top"].set_visible(False)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))

    plt.title("Evolucao Cambial e Demanda no Varejo de Tecnologia no Brasil (2015 - 2026)", 
              fontsize=12, fontweight="bold", pad=15, loc="left", color="#0f172a")

    output_path = os.path.join(OUTPUT_DIR, "01_evolucao_dolar_vs_vendas_tecnologia.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [PASS] Grafico 1 salvo em: {output_path}")

def generate_chart_2(conn):
    print("[INFO] Gerando Grafico 2: Ambientes Macroeconomicos...")
    query = """
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
            WHEN quartil_dolar <= 2 AND quartil_juros <= 2 THEN 'Cenario Favoravel (Dolar/Juros Baixos)'
            WHEN quartil_dolar >= 3 AND quartil_juros >= 3 THEN 'Cenario Severo (Dolar/Juros Altos)'
            ELSE 'Cenario Moderado'
        END AS ambiente,
        ROUND(AVG(indice_volume_vendas)::NUMERIC, 1) AS volume_medio
    FROM quartis_macro
    GROUP BY ambiente
    ORDER BY volume_medio ASC;
    """
    df = pd.read_sql(query, conn)

    fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=200)

    colors = ["#94a3b8", "#64748b", "#2563eb"]
    bars = ax.barh(df["ambiente"], df["volume_medio"], color=colors, height=0.55, edgecolor="none")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.grid(axis="x", linestyle="--", alpha=0.3, color="#94a3b8")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1.2, bar.get_y() + bar.get_height()/2, f"{width:.1f}", 
                va="center", ha="left", fontsize=9, fontweight="bold", color="#1e293b")

    ax.set_xlim(0, 105)
    ax.set_xlabel("Indice Medio de Volume de Vendas (Base 100 = Media Historica)", fontsize=9, labelpad=8)
    plt.title("Desempenho de Vendas de Tecnologia por Cenario Macroeconomico", 
              fontsize=11, fontweight="bold", pad=15, loc="left", color="#0f172a")

    output_path = os.path.join(OUTPUT_DIR, "02_cenarios_macroeconomicos_vendas.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [PASS] Grafico 2 salvo em: {output_path}")

def main():
    set_minimal_style()
    conn = psycopg2.connect(DATABASE_URI)
    generate_chart_1(conn)
    generate_chart_2(conn)
    conn.close()
    print("[INFO] Todos os graficos macroeconomicos foram gerados com sucesso!")

if __name__ == "__main__":
    main()
