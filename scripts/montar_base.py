"""Monta data/chatse.sqlite a partir dos JSON já baixados do TSE.

Uso:
  python scripts/montar_base.py \\
    --turno1 /caminho/turno1.json \\
    --turno2 /caminho/turno2.json \\
    --saida data/chatse.sqlite
"""

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path

VIEWS = """
CREATE VIEW municipio AS
SELECT turno, eleicao, uf, municipio_codigo, municipio, municipio_norm,
       SUM(votos_validos) AS votos_validos,
       SUM(brancos) AS brancos,
       SUM(nulos) AS nulos,
       SUM(comparecimento) AS comparecimento,
       SUM(eleitores) AS eleitores,
       SUM(secoes) AS secoes,
       COUNT(*) AS zonas
FROM local
GROUP BY turno, eleicao, uf, municipio_codigo, municipio, municipio_norm;

CREATE VIEW uf_total AS
SELECT turno, eleicao, uf,
       SUM(votos_validos) AS votos_validos,
       SUM(brancos) AS brancos,
       SUM(nulos) AS nulos,
       SUM(comparecimento) AS comparecimento,
       SUM(eleitores) AS eleitores,
       SUM(secoes) AS secoes,
       COUNT(*) AS zonas
FROM local
GROUP BY turno, eleicao, uf;

CREATE VIEW brasil AS
SELECT turno, eleicao,
       SUM(votos_validos) AS votos_validos,
       SUM(brancos) AS brancos,
       SUM(nulos) AS nulos,
       SUM(comparecimento) AS comparecimento,
       SUM(eleitores) AS eleitores,
       SUM(secoes) AS secoes,
       COUNT(*) AS zonas
FROM local
GROUP BY turno, eleicao;

CREATE VIEW voto_zona AS
SELECT l.turno, l.eleicao, l.uf, l.municipio, l.municipio_norm, l.municipio_codigo, l.zona,
       v.candidato, v.candidato_norm, v.numero, v.partido, v.votos,
       l.votos_validos, l.brancos, l.nulos, l.comparecimento, l.eleitores, l.secoes,
       CASE WHEN l.votos_validos = 0 THEN NULL
            ELSE ROUND(100.0 * v.votos / l.votos_validos, 2) END AS percentual
FROM voto v
JOIN local l ON l.id = v.local_id;

CREATE VIEW voto_municipio AS
SELECT l.turno, l.eleicao, l.uf, l.municipio, l.municipio_norm, l.municipio_codigo,
       v.candidato, v.candidato_norm, v.numero, v.partido,
       SUM(v.votos) AS votos,
       m.votos_validos, m.brancos, m.nulos, m.comparecimento, m.eleitores, m.secoes, m.zonas,
       CASE WHEN m.votos_validos = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(v.votos) / m.votos_validos, 2) END AS percentual
FROM voto v
JOIN local l ON l.id = v.local_id
JOIN municipio m
  ON m.turno = l.turno AND m.uf = l.uf AND m.municipio_codigo = l.municipio_codigo
GROUP BY l.turno, l.eleicao, l.uf, l.municipio, l.municipio_norm, l.municipio_codigo,
         v.candidato, v.candidato_norm, v.numero, v.partido,
         m.votos_validos, m.brancos, m.nulos, m.comparecimento, m.eleitores, m.secoes, m.zonas;

CREATE VIEW voto_uf AS
SELECT l.turno, l.eleicao, l.uf,
       v.candidato, v.candidato_norm, v.numero, v.partido,
       SUM(v.votos) AS votos,
       u.votos_validos, u.brancos, u.nulos, u.comparecimento, u.eleitores, u.secoes, u.zonas,
       CASE WHEN u.votos_validos = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(v.votos) / u.votos_validos, 2) END AS percentual
FROM voto v
JOIN local l ON l.id = v.local_id
JOIN uf_total u ON u.turno = l.turno AND u.uf = l.uf
GROUP BY l.turno, l.eleicao, l.uf, v.candidato, v.candidato_norm, v.numero, v.partido,
         u.votos_validos, u.brancos, u.nulos, u.comparecimento, u.eleitores, u.secoes, u.zonas;

CREATE VIEW voto_brasil AS
SELECT l.turno, l.eleicao,
       v.candidato, v.candidato_norm, v.numero, v.partido,
       SUM(v.votos) AS votos,
       b.votos_validos, b.brancos, b.nulos, b.comparecimento, b.eleitores, b.secoes, b.zonas,
       CASE WHEN b.votos_validos = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(v.votos) / b.votos_validos, 2) END AS percentual
FROM voto v
JOIN local l ON l.id = v.local_id
JOIN brasil b ON b.turno = l.turno
GROUP BY l.turno, l.eleicao, v.candidato, v.candidato_norm, v.numero, v.partido,
         b.votos_validos, b.brancos, b.nulos, b.comparecimento, b.eleitores, b.secoes, b.zonas;
"""


def norm(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return sem_acento.casefold()


def criar(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS voto_brasil;
        DROP VIEW IF EXISTS voto_uf;
        DROP VIEW IF EXISTS voto_municipio;
        DROP VIEW IF EXISTS voto_zona;
        DROP VIEW IF EXISTS brasil;
        DROP VIEW IF EXISTS uf_total;
        DROP VIEW IF EXISTS municipio;
        DROP TABLE IF EXISTS voto;
        DROP TABLE IF EXISTS local;
        DROP TABLE IF EXISTS fonte;

        CREATE TABLE local (
          id INTEGER PRIMARY KEY,
          turno INTEGER NOT NULL,
          eleicao TEXT NOT NULL,
          uf TEXT NOT NULL,
          municipio_codigo TEXT NOT NULL,
          municipio TEXT NOT NULL,
          municipio_norm TEXT NOT NULL,
          zona TEXT NOT NULL,
          votos_validos INTEGER NOT NULL,
          brancos INTEGER NOT NULL,
          nulos INTEGER NOT NULL,
          comparecimento INTEGER NOT NULL,
          eleitores INTEGER NOT NULL,
          secoes INTEGER NOT NULL
        );

        CREATE TABLE voto (
          local_id INTEGER NOT NULL REFERENCES local(id),
          candidato TEXT NOT NULL,
          candidato_norm TEXT NOT NULL,
          numero TEXT NOT NULL,
          partido TEXT NOT NULL,
          votos INTEGER NOT NULL
        );

        CREATE TABLE fonte (
          chave TEXT PRIMARY KEY,
          valor TEXT NOT NULL
        );

        CREATE INDEX idx_local_lugar ON local(turno, uf, municipio_norm);
        CREATE INDEX idx_voto_candidato ON voto(candidato_norm, local_id);
        """
    )


def inserir_local(conn, turno, eleicao, linha) -> int:
    cursor = conn.execute(
        """
        INSERT INTO local (
          turno, eleicao, uf, municipio_codigo, municipio, municipio_norm, zona,
          votos_validos, brancos, nulos, comparecimento, eleitores, secoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            turno,
            eleicao,
            linha["uf"],
            linha["cd"],
            linha["municipio"],
            norm(linha["municipio"]),
            linha["zona"],
            linha["vv"],
            linha["vb"],
            linha["vn"],
            linha["c"],
            linha["te"],
            linha["secoes"],
        ),
    )
    return int(cursor.lastrowid)


def inserir_voto(conn, local_id: int, candidato: str, numero: str, partido: str, votos: int) -> None:
    conn.execute(
        """
        INSERT INTO voto (local_id, candidato, candidato_norm, numero, partido, votos)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (local_id, candidato, norm(candidato), numero, partido, votos),
    )


def carregar_turno2(conn, caminho: Path) -> int:
    bruto = json.loads(caminho.read_text())
    linhas = bruto["rows"] if isinstance(bruto, dict) else bruto
    for linha in linhas:
        local_id = inserir_local(conn, 2, "6258", linha)
        inserir_voto(conn, local_id, "LULA", "13", "PT", linha["lula"])
        inserir_voto(conn, local_id, "FLAVIO BOLSONARO", "22", "PL", linha["flavio"])
    return len(linhas)


def carregar_turno1(conn, caminho: Path) -> int:
    linhas = json.loads(caminho.read_text())
    for linha in linhas:
        local_id = inserir_local(conn, 1, "6257", linha)
        for candidato in linha["candidatos"]:
            inserir_voto(
                conn,
                local_id,
                candidato["candidato"],
                candidato["numero"],
                candidato["partido"],
                candidato["votos"],
            )
    return len(linhas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--turno1", required=True, type=Path)
    parser.add_argument("--turno2", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    if args.saida.exists():
        args.saida.unlink()
    conn = sqlite3.connect(args.saida)
    try:
        criar(conn)
        n1 = carregar_turno1(conn, args.turno1)
        n2 = carregar_turno2(conn, args.turno2)
        conn.executemany(
            "INSERT INTO fonte (chave, valor) VALUES (?, ?)",
            [
                ("cargo", "presidente"),
                ("turno_1_eleicao", "6257"),
                ("turno_1_totalizacao", "05/10/2026"),
                ("turno_2_eleicao", "6258"),
                ("turno_2_totalizacao", "25/10/2026"),
                ("origem", "https://resultados.tse.jus.br"),
                ("zonas_turno_1", str(n1)),
                ("zonas_turno_2", str(n2)),
            ],
        )
        conn.executescript(VIEWS)
        conn.commit()
    finally:
        conn.close()
    print(f"{args.saida} turno1={n1} turno2={n2}")


if __name__ == "__main__":
    main()
