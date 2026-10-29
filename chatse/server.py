import json
import os
import re
import sqlite3
import sys

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from chatse.db import ESQUEMA, caminho_base, conectar

mcp = FastMCP("chatse")

_PROIBIDO = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|detach|pragma|vacuum|replace|create|grant|reindex)\b",
    re.IGNORECASE,
)


def consulta_segura(sql: str) -> str:
    texto = sql.strip()
    if texto.endswith(";"):
        texto = texto[:-1].strip()
    if not texto:
        raise ValueError("A consulta veio vazia.")
    if ";" in texto:
        raise ValueError("Envie uma única consulta.")
    if _PROIBIDO.search(texto):
        raise ValueError("Só é permitida leitura. A consulta precisa ser um SELECT.")
    inicio = texto.lstrip().lower()
    if not (inicio.startswith("select") or inicio.startswith("with")):
        raise ValueError("A consulta precisa começar com SELECT ou WITH.")
    return texto


@mcp.tool()
def esquema() -> str:
    """Descreve a base local da apuração de presidente em 2026 e como cruzar turno, lugar e candidato. Chame antes da primeira consulta se ainda não souber as tabelas."""
    return ESQUEMA


@mcp.tool()
def consultar(sql: str) -> str:
    """Executa um SELECT na base local. Serve para qualquer pergunta ou cruzamento: votos, percentual, comparecimento, abstenção, brancos, nulos, zona, município, estado, exterior e os dois turnos. Não invente o SQL sem olhar o esquema. Devolve no máximo 200 linhas."""
    try:
        consulta = consulta_segura(sql)
        with conectar() as conn:
            cursor = conn.execute(consulta)
            colunas = [item[0] for item in cursor.description or []]
            linhas = []
            for row in cursor:
                if len(linhas) == 200:
                    break
                linhas.append([row[nome] for nome in colunas])
    except sqlite3.Error as exc:
        return json.dumps({"erro": str(exc)}, ensure_ascii=False)
    except ValueError as exc:
        return json.dumps({"erro": str(exc)}, ensure_ascii=False)
    return json.dumps(
        {"colunas": colunas, "linhas": linhas, "quantidade": len(linhas)},
        ensure_ascii=False,
    )


def checar() -> int:
    caminho = caminho_base()
    print(f"Base: {caminho}")
    with conectar() as conn:
        zonas = conn.execute("SELECT COUNT(*) FROM local").fetchone()[0]
        turnos = conn.execute(
            "SELECT turno, COUNT(*) FROM local GROUP BY turno ORDER BY turno"
        ).fetchall()
        pais = conn.execute(
            """
            SELECT turno, candidato, votos
            FROM voto_brasil
            WHERE candidato_norm IN ('lula', 'flavio bolsonaro')
            ORDER BY turno, votos DESC
            """
        ).fetchall()
    print(f"Zonas: {zonas}")
    for turno, quantidade in turnos:
        print(f"Turno {turno}: {quantidade} zonas")
    for turno, candidato, votos in pais:
        print(f"Turno {turno} {candidato}: {votos}")
    return 0


def preparar_http() -> int:
    porta = int(os.environ.get("CHATSE_PORT", "8000"))
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = porta
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            f"127.0.0.1:{porta}",
            f"localhost:{porta}",
            "127.0.0.1",
            "localhost",
            f"host.docker.internal:{porta}",
        ],
        allowed_origins=[
            f"http://127.0.0.1:{porta}",
            f"http://localhost:{porta}",
        ],
    )
    return porta


def main() -> None:
    if "--checar" in sys.argv:
        try:
            raise SystemExit(checar())
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            raise SystemExit(1) from exc
    if "--http" in sys.argv:
        porta = preparar_http()
        print(f"Chatse em http://127.0.0.1:{porta}/mcp", flush=True)
        mcp.run(transport="streamable-http")
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
