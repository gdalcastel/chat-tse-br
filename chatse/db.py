import os
import sqlite3
from pathlib import Path

ESQUEMA = """
Base local da apuração de presidente em 2026. Os números saem desta base.
Não invente voto, percentual nem nome de lugar.

Turnos
- turno 1: eleição 6257, totalizada em 05/10/2026. Vários candidatos.
- turno 2: eleição 6258, totalizada em 25/10/2026. Lula (13, PT) e Flávio Bolsonaro (22, PL).

Grão
Cada linha de `local` e de `voto_zona` é uma zona dentro de um município.
Uma cidade com várias zonas não é uma linha só. Para a cidade inteira use
`voto_municipio` e `municipio`. Para o estado, `voto_uf` e `uf_total`.
Para o país, `voto_brasil` e `brasil`.
ZZ é o exterior. O nome do município, nesse caso, é o posto consular.

Colunas de busca
`municipio_norm` e `candidato_norm` estão sem acento e em minúsculas.
Use essas colunas para achar nome. Exemplo: municipio_norm = 'sao paulo',
candidato_norm = 'flavio bolsonaro'.

Percentual
`percentual` já é a fatia sobre os votos válidos daquele lugar e turno.
Não recalcule somando percentual. Não some `votos_validos` a partir de
`voto_zona`: esse número se repete em cada candidato da mesma zona.
Comparecimento, eleitores, brancos, nulos e seções também se repetem ali.
Para esses totais, use `municipio`, `uf_total` ou `brasil`.

Tabelas e visões
- voto_zona(turno, uf, municipio, municipio_norm, municipio_codigo, zona, candidato, candidato_norm, numero, partido, votos, votos_validos, brancos, nulos, comparecimento, eleitores, secoes, percentual)
- voto_municipio(turno, uf, municipio, municipio_norm, municipio_codigo, candidato, candidato_norm, numero, partido, votos, votos_validos, brancos, nulos, comparecimento, eleitores, secoes, zonas, percentual)
- voto_uf(turno, uf, candidato, candidato_norm, numero, partido, votos, votos_validos, brancos, nulos, comparecimento, eleitores, secoes, percentual)
- voto_brasil(turno, candidato, candidato_norm, numero, partido, votos, votos_validos, brancos, nulos, comparecimento, eleitores, secoes, percentual)
- municipio, uf_total, brasil: os mesmos totais, sem candidato
- fonte(chave, valor): origem e data da totalização

Exemplos
Zonas do Brasil com menos votos no Flávio no 2º turno:
SELECT municipio, uf, zona, votos, percentual
FROM voto_zona
WHERE turno = 2 AND uf != 'ZZ' AND candidato_norm = 'flavio bolsonaro' AND votos_validos > 0
ORDER BY votos ASC
LIMIT 10;

Cidade inteira, os dois turnos:
SELECT turno, candidato, votos, percentual, votos_validos
FROM voto_municipio
WHERE municipio_norm = 'macapa'
ORDER BY turno, votos DESC;

Onde a abstenção caiu do 1º para o 2º turno:
SELECT a.municipio, a.uf,
       ROUND(100.0 * (a.eleitores - a.comparecimento) / a.eleitores, 2) AS abstencao_1,
       ROUND(100.0 * (b.eleitores - b.comparecimento) / b.eleitores, 2) AS abstencao_2
FROM municipio a
JOIN municipio b
  ON a.uf = b.uf AND a.municipio_codigo = b.municipio_codigo
 AND a.turno = 1 AND b.turno = 2
WHERE a.eleitores > 0 AND b.eleitores > 0
ORDER BY (abstencao_2 - abstencao_1) ASC
LIMIT 10;
""".strip()


def caminho_base() -> Path:
    bruto = os.environ.get("CHATSE_DB")
    if bruto:
        return Path(bruto)
    return Path(__file__).resolve().parents[1] / "data" / "chatse.sqlite"


def conectar() -> sqlite3.Connection:
    caminho = caminho_base()
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Base não encontrada em {caminho}. Rode o projeto a partir da pasta chatse."
        )
    conn = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
