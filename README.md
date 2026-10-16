# ⚽ brasileirao-tracker

Coleta **diária e automática** da classificação do Brasileirão Série A e estimativa das chances de cada time ser **campeão**, ir para a **Libertadores (G6)** ou ser **rebaixado (Z4)**.

Tudo roda sozinho no **GitHub Actions**: todo dia às 06:07 o workflow busca os dados, simula o resto do campeonato e faz commit dos resultados neste repositório.

## Como funciona

```
football-data.org (API)  →  src/coletar.py  →  src/simulacao.py  →  data/*.csv  →  commit automático
        ↑                                                                               │
        └──────────────────────── GitHub Actions (cron diário) ─────────────────────────┘
```

1. **Coleta:** `coletar.py` busca a classificação e todos os jogos da temporada na API.
2. **Força dos times:** para cada time, calcula ataque e defesa em casa e fora a partir dos gols marcados e sofridos até agora (com uma suavização pela média da liga, para não exagerar com poucos jogos).
3. **Simulação de Monte Carlo:** o placar de cada jogo que falta é sorteado com a **distribuição de Poisson**, e o campeonato é simulado **10.000 vezes**.
4. **Probabilidades:** conta em quantas simulações cada time terminou em 1º, no G6 ou no Z4. O desempate segue o regulamento: pontos, vitórias, saldo e gols pró.

## Dados gerados

| Arquivo | Conteúdo |
|---|---|
| `data/classificacao/AAAA-MM-DD.csv` | Tabela oficial do dia |
| `data/probabilidades/AAAA-MM-DD.csv` | % campeão, % G6, % rebaixamento, pontos e posição esperados |
| `data/historico_probabilidades.csv` | Todas as datas juntas (base para gráficos de evolução) |
| `data/jogos.csv` | Jogos da temporada (realizados e restantes) |

## Rodar localmente

```bash
pip install -r requirements.txt
export FOOTBALL_API_KEY="sua_chave"   # chave gratuita em football-data.org
python src/coletar.py
```

## Limitações

O modelo é **simples de propósito**: usa só gols marcados e sofridos. Ele não considera lesões, troca de técnico, elenco, calendário ou motivação. Por isso os números são **estimativas**, não previsões garantidas.

## Tecnologias

Python · pandas · NumPy · API REST · GitHub Actions (cron) · GitHub Secrets

---
Dados: [football-data.org](https://www.football-data.org)
