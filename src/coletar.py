"""Coleta a classificação e os jogos do Brasileirão e salva em CSV.

Fonte: https://www.football-data.org (API v4, plano gratuito).
A chave da API vem da variável de ambiente FOOTBALL_API_KEY (GitHub Secrets).
"""
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from simulacao import simular

API = "https://api.football-data.org/v4/competitions/BSA"
PASTA = Path(__file__).resolve().parent.parent / "data"


def buscar(caminho: str) -> dict:
    chave = os.environ.get("FOOTBALL_API_KEY")
    if not chave:
        raise SystemExit("Defina a variável de ambiente FOOTBALL_API_KEY.")
    resp = requests.get(f"{API}/{caminho}", headers={"X-Auth-Token": chave}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def classificacao_atual() -> pd.DataFrame:
    dados = buscar("standings")
    tabela = next(s["table"] for s in dados["standings"] if s["type"] == "TOTAL")
    return pd.DataFrame([{
        "posicao": t["position"],
        "time": t["team"].get("shortName") or t["team"]["name"],
        "pontos": t["points"],
        "jogos": t["playedGames"],
        "vitorias": t["won"],
        "empates": t["draw"],
        "derrotas": t["lost"],
        "gols_pro": t["goalsFor"],
        "gols_contra": t["goalsAgainst"],
        "saldo": t["goalDifference"],
    } for t in tabela])


def jogos_temporada() -> pd.DataFrame:
    dados = buscar("matches")
    return pd.DataFrame([{
        "rodada": m["matchday"],
        "data_utc": m["utcDate"],
        "status": m["status"],
        "casa": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
        "fora": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
        "gols_casa": m["score"]["fullTime"]["home"],
        "gols_fora": m["score"]["fullTime"]["away"],
    } for m in dados["matches"]])


def main():
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()

    tabela = classificacao_atual()
    jogos = jogos_temporada()
    probs = simular(tabela, jogos)

    (PASTA / "classificacao").mkdir(parents=True, exist_ok=True)
    (PASTA / "probabilidades").mkdir(parents=True, exist_ok=True)
    tabela.to_csv(PASTA / "classificacao" / f"{hoje}.csv", index=False)
    probs.to_csv(PASTA / "probabilidades" / f"{hoje}.csv", index=False)
    jogos.to_csv(PASTA / "jogos.csv", index=False)

    # histórico acumulado: uma linha por time por dia (base para gráficos)
    historico = PASTA / "historico_probabilidades.csv"
    novo = probs.assign(data=hoje)
    if historico.exists():
        antigo = pd.read_csv(historico)
        novo = pd.concat([antigo[antigo["data"] != hoje], novo], ignore_index=True)
    novo.to_csv(historico, index=False)

    print(f"Coleta de {hoje}: {len(tabela)} times, "
          f"{(jogos['status'] != 'FINISHED').sum()} jogos restantes simulados.")
    print(probs.to_string(index=False))


if __name__ == "__main__":
    main()
