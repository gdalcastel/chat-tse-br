# Chatse

Pergunte o que quiser sobre a apuração de presidente de 2026. O programa roda na sua máquina e devolve os números oficiais do TSE. Dá para cruzar turno, estado, município, zona, candidato, votos, comparecimento, abstenção, brancos e nulos. O exterior entra como `ZZ`.

A sua chave de modelo fica no aplicativo que você já usa, como o Cursor ou o Claude. O Chatse não recebe essa chave e não chama nenhum serviço seu.

## O que tem na base

- 1º turno, eleição 6257, totalizado em 05/10/2026, com todos os candidatos.
- 2º turno, eleição 6258, totalizado em 25/10/2026, Lula e Flávio Bolsonaro.
- Cada zona de cada município, no Brasil e nos postos no exterior.

Os arquivos vieram de [resultados.tse.jus.br](https://resultados.tse.jus.br). A soma das zonas reproduz o total nacional publicado pelo TSE.

## Rodar com Docker

É preciso ter o Docker instalado.

```bash
git clone https://github.com/gdalcastel/chat-tse-br.git
cd chat-tse-br
make run
```

Esse comando constrói a imagem e sobe o Chatse nesta máquina, em `http://127.0.0.1:8000/mcp`. Deixe o terminal aberto. Para parar, use Ctrl+C.

## Ligar no ChatGPT

O ChatGPT, no navegador, não alcança o `localhost` direto. O `make run` deixa o programa na sua máquina. Um túnel da OpenAI sai da sua máquina e leva as perguntas até ele, sem publicar o Chatse na internet. O passo a passo oficial está em [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) e em [Connecting custom MCP servers in ChatGPT](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt).

Isso funciona no ChatGPT da web, nos planos Pro, Business, Enterprise e Edu. O aplicativo do celular não conecta um MCP.

1. Rode `make run` e deixe esse terminal aberto.
2. Entre em [platform.openai.com](https://platform.openai.com), abra as configurações de túnel e crie um túnel. Copie o `tunnel_id`. Crie também uma chave de API para o túnel.
3. Baixe o `tunnel-client` pelo link dessa mesma página, ou em [github.com/openai/tunnel-client](https://github.com/openai/tunnel-client).
4. Em outro terminal, com o `make run` ainda no ar:

```bash
export CONTROL_PLANE_API_KEY="cole-a-chave-aqui"
tunnel-client init \
  --profile chatse \
  --tunnel-id "cole-o-tunnel-id" \
  --mcp-server-url "http://127.0.0.1:8000/mcp"
tunnel-client doctor --profile chatse --explain
tunnel-client run --profile chatse
```

Se o `init` pedir um exemplo pronto, use o perfil HTTP da documentação e aponte para `http://127.0.0.1:8000/mcp`. O `tunnel-client help quickstart` mostra as opções da versão que você instalou. Deixe esse segundo terminal aberto.

5. No ChatGPT, abra Plugins, clique no mais e escolha Add custom MCP server.
6. Nome: Chatse. Em Connection, escolha Tunnel e selecione o túnel que você criou.
7. Autenticação: nenhuma. O Chatse não tem senha.
8. Leia o aviso, marque que entendeu e crie o plugin.
9. Abra uma conversa nova, digite `@` e escolha Chatse. Pergunte, por exemplo: “quais as 10 zonas do exterior com mais votos no Flávio no segundo turno?”

A chave da OpenAI fica só nesse túnel, no seu computador. Ela não entra no Chatse.

## Rodar sem Docker

É preciso Python 3.11 ou mais novo.

```bash
git clone https://github.com/gdalcastel/chat-tse-br.git
cd chat-tse-br
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m chatse --checar
```

No Windows, ative com `.venv\Scripts\activate`.

O `--checar` imprime a quantidade de zonas e os votos nacionais de Lula e de Flávio. Se esses números aparecerem, a base local está pronta. Para o mesmo endereço do Docker, use `python -m chatse --http`.

## Ligar no Cursor

No Cursor, abra a configuração de MCP e acrescente o servidor. Troque o caminho pelo da pasta onde você clonou:

```json
{
  "mcpServers": {
    "chatse": {
      "command": "/caminho/da/pasta/chat-tse-br/.venv/bin/python",
      "args": ["-m", "chatse"],
      "cwd": "/caminho/da/pasta/chat-tse-br"
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
