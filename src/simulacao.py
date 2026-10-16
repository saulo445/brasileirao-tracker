"""Simulação de Monte Carlo do restante do Brasileirão.

Ideia: cada time tem uma força de ataque e de defesa calculada a partir dos
gols marcados e sofridos nos jogos já disputados (separando casa e fora).
Os placares dos jogos que faltam são sorteados com a distribuição de Poisson
e o campeonato é simulado milhares de vezes.
"""
import numpy as np
import pandas as pd

N_SIMULACOES = 10_000
PESO_MEDIA = 5  # "jogos fictícios" na média da liga: suaviza times com poucos jogos


def calcular_forcas(jogos_finalizados: pd.DataFrame, times: list) -> dict:
    """Retorna as médias da liga e a força de cada time (1.0 = média)."""
    media_casa = jogos_finalizados["gols_casa"].mean()
    media_fora = jogos_finalizados["gols_fora"].mean()

    forcas = {}
    for t in times:
        em_casa = jogos_finalizados[jogos_finalizados["casa"] == t]
        fora = jogos_finalizados[jogos_finalizados["fora"] == t]

        def taxa(gols, n, media):
            # média suavizada: puxa para a média da liga quando há poucos jogos
            return ((gols + PESO_MEDIA * media) / (n + PESO_MEDIA)) / media

        forcas[t] = {
            "ataque_casa": taxa(em_casa["gols_casa"].sum(), len(em_casa), media_casa),
            "defesa_casa": taxa(em_casa["gols_fora"].sum(), len(em_casa), media_fora),
            "ataque_fora": taxa(fora["gols_fora"].sum(), len(fora), media_fora),
            "defesa_fora": taxa(fora["gols_casa"].sum(), len(fora), media_casa),
        }
    return {"media_casa": media_casa, "media_fora": media_fora, "times": forcas}


def simular(classificacao: pd.DataFrame, jogos: pd.DataFrame,
            n: int = N_SIMULACOES, seed: int = 42) -> pd.DataFrame:
    """Simula os jogos restantes e devolve as probabilidades por time."""
    rng = np.random.default_rng(seed)
    times = classificacao["time"].tolist()
    idx = {t: i for i, t in enumerate(times)}

    finalizados = jogos[jogos["status"] == "FINISHED"]
    restantes = jogos[jogos["status"] != "FINISHED"]
    f = calcular_forcas(finalizados, times)

    # ponto de partida: a tabela oficial de hoje
    base = classificacao.set_index("time")
    pontos = np.tile(base["pontos"].to_numpy(float), (n, 1))
    vitorias = np.tile(base["vitorias"].to_numpy(float), (n, 1))
    saldo = np.tile(base["saldo"].to_numpy(float), (n, 1))
    gols_pro = np.tile(base["gols_pro"].to_numpy(float), (n, 1))

    for _, j in restantes.iterrows():
        c, v = j["casa"], j["fora"]
        if c not in idx or v not in idx:
            continue
        lam_c = f["media_casa"] * f["times"][c]["ataque_casa"] * f["times"][v]["defesa_fora"]
        lam_v = f["media_fora"] * f["times"][v]["ataque_fora"] * f["times"][c]["defesa_casa"]
        gc = rng.poisson(lam_c, n)
        gv = rng.poisson(lam_v, n)
        ic, iv = idx[c], idx[v]
        pontos[:, ic] += np.where(gc > gv, 3, np.where(gc == gv, 1, 0))
        pontos[:, iv] += np.where(gv > gc, 3, np.where(gc == gv, 1, 0))
        vitorias[:, ic] += gc > gv
        vitorias[:, iv] += gv > gc
        saldo[:, ic] += gc - gv
        saldo[:, iv] += gv - gc
        gols_pro[:, ic] += gc
        gols_pro[:, iv] += gv

    # critérios do Brasileirão: pontos, vitórias, saldo, gols pró (+ sorteio)
    nota = (pontos * 1e9 + vitorias * 1e6 + (saldo + 500) * 1e3 + gols_pro
            + rng.random(pontos.shape))
    ordem = np.argsort(-nota, axis=1)
    posicao = np.empty_like(ordem)
    linhas = np.arange(n)[:, None]
    posicao[linhas, ordem] = np.arange(1, len(times) + 1)

    resultado = pd.DataFrame({
        "time": times,
        "pontos_atuais": base["pontos"].to_numpy(),
        "pontos_esperados": pontos.mean(axis=0).round(1),
        "prob_campeao": (posicao == 1).mean(axis=0),
        "prob_g6_libertadores": (posicao <= 6).mean(axis=0),
        "prob_rebaixamento": (posicao >= len(times) - 3).mean(axis=0),
        "posicao_media": posicao.mean(axis=0).round(1),
    })
    for col in ["prob_campeao", "prob_g6_libertadores", "prob_rebaixamento"]:
        resultado[col] = (resultado[col] * 100).round(1)
    return resultado.sort_values("pontos_esperados", ascending=False).reset_index(drop=True)
