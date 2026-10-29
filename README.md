# Chatse

Pergunte o que quiser sobre a apuração de presidente de 2026. O programa roda na sua máquina e devolve os números oficiais do TSE. Dá para cruzar turno, estado, município, zona, candidato, votos, comparecimento, abstenção, brancos e nulos. O exterior entra como `ZZ`.

A sua chave de modelo fica no aplicativo que você já usa, como o Cursor ou o Claude. O Chatse não recebe essa chave e não chama nenhum serviço seu.

## O que tem na base

- 1º turno, eleição 6257, totalizado em 05/10/2026, com todos os candidatos.
- 2º turno, eleição 6258, totalizado em 25/10/2026, Lula e Flávio Bolsonaro.
- Cada zona de cada município, no Brasil e nos postos no exterior.

Os arquivos vieram de [resultados.tse.jus.br](https://resultados.tse.jus.br). A soma das zonas reproduz o total nacional publicado pelo TSE.

## Rodar na sua máquina

É preciso Python 3.11 ou mais novo.

```bash
git clone https://github.com/gdalcastel/chatse.git
cd chatse
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m chatse --checar
```

No Windows, ative com `.venv\Scripts\activate`.

O `--checar` imprime a quantidade de zonas e os votos nacionais de Lula e de Flávio. Se esses números aparecerem, a base local está pronta.

## Ligar no modelo

No Cursor, abra a configuração de MCP e acrescente o servidor. Troque o caminho pelo da pasta onde você clonou:

```json
{
  "mcpServers": {
    "chatse": {
      "command": "/caminho/da/pasta/chatse/.venv/bin/python",
      "args": ["-m", "chatse"],
      "cwd": "/caminho/da/pasta/chatse"
    }
  }
}
```

No Claude Desktop, o mesmo bloco entra em `claude_desktop_config.json`.

Reinicie o aplicativo. A partir daí, pergunte em português. O modelo consulta a base local e responde com os números dela.

Exemplos:

- Quais as 10 zonas do Brasil com menos votos no Flávio no segundo turno?
- Compare o primeiro e o segundo turno em Macapá.
- Em quais capitais Lula virou do primeiro para o segundo turno?
- Onde a abstenção mais caiu entre os turnos?

Uma zona não é a cidade inteira quando a cidade tem várias zonas. São Paulo tem 57. Palmas tem uma. Peça “a cidade” quando quiser o município somado.
