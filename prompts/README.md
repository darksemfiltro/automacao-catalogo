# Prompts guia

Esta pasta guarda prompts prontos para você colar numa IA e ela fazer o trabalho
pesado: instalar, configurar a voz, criar episódios e adaptar o sistema.

## Como usar

1. Abra a pasta do projeto numa ferramenta de IA que lê e edita arquivos, como
   Claude Code, Codex, OpenCode, Cursor ou Continue. Para uma IA no navegador,
   cole também o conteúdo dos arquivos que o prompt pedir.
2. Abra o prompt do que você quer fazer, copie o bloco de texto e cole na IA.
3. Troque o que estiver entre `[colchetes]` pelo seu caso.
4. Leia o que a IA propõe antes de aprovar. Peça que ela rode os testes e mostre
   o resultado.

A IA pode ser um modelo na nuvem ou um modelo local, como os que rodam no Ollama
ou no LM Studio. Modelos pequenos erram mais: peça um passo de cada vez.

## Índice

| Prompt | Para quê |
| --- | --- |
| [00-instalacao.md](00-instalacao.md) | Instalar as dependências e resolver erro de instalação |
| [01-entender-o-projeto.md](01-entender-o-projeto.md) | Um tour guiado pelo projeto |
| [02-voz-local.md](02-voz-local.md) | Narração com um modelo de voz local |
| [03-voz-api.md](03-voz-api.md) | Narração por API, e como acrescentar outra API |
| [04-novo-episodio.md](04-novo-episodio.md) | Criar um episódio do zero |
| [05-adaptar-tema.md](05-adaptar-tema.md) | Ensinar ao motor objetos e cenas de um tema novo |
| [06-adaptar-canal-e-idioma.md](06-adaptar-canal-e-idioma.md) | Trocar identidade visual, tom e idioma |
| [07-fonte-pexels.md](07-fonte-pexels.md) | Usar vídeos e fotos do Pexels |
| [08-fonte-pixabay.md](08-fonte-pixabay.md) | Usar vídeos e imagens do Pixabay |
| [09-outras-automacoes.md](09-outras-automacoes.md) | Base para qualquer automação nova |
| [10-resolver-erros.md](10-resolver-erros.md) | Diagnosticar um erro qualquer |

## Variáveis de ambiente

Chaves de API ficam só na sua máquina. O jeito mais simples é o arquivo `.env`:

1. Copie o modelo: `copy .env.example .env` (Windows) ou `cp .env.example .env` (Linux e macOS).
2. Abra o `.env` e preencha só o que você vai usar. Uma variável por linha, no formato
   `NOME=valor`. Linhas com `#` são comentários.
3. Pronto. O `pipeline/tts.py` lê o `.env` sozinho, a cada execução.

O git ignora o `.env`, então ele não sobe por engano. Nunca envie esse arquivo a ninguém,
não cole o conteúdo dele no chat de uma IA e não o coloque dentro de uma pasta que você
compartilha. Se uma chave vazar, apague-a no site do serviço e crie outra. Uma variável
já definida no sistema vale mais do que a do `.env`.

As variáveis:

| Variável | Para quê |
| --- | --- |
| `CATALOGO_VOZ_PROVEDOR` | `omnivoice`, `openai` ou `comando`. Vence o campo `provedor` de `sistema/voz.json`. |
| `OPENAI_API_KEY` | Chave da API de voz compatível com OpenAI. O nome vem de `api.chave_env`. |
| `OMNIVOICE_HOME` | Pasta onde o OmniVoice está instalado. |
| `CATALOGO_REF_AUDIO` | Sua voz de referência para clonar (OmniVoice). |
| `PEXELS_API_KEY` | Chave do Pexels, para o prompt 07. |
| `PIXABAY_API_KEY` | Chave do Pixabay, para o prompt 08. |

Se preferir não usar o `.env`, defina a variável no terminal. No Windows, vale para a
sessão do PowerShell atual:

```powershell
$env:OPENAI_API_KEY = "cole-sua-chave-aqui"
```

Para guardar de forma permanente use `setx OPENAI_API_KEY "cole-sua-chave-aqui"` e
abra um terminal novo. No Linux e no macOS: `export OPENAI_API_KEY="cole-sua-chave-aqui"`
no seu `~/.bashrc` ou `~/.zshrc`. Não cole chaves no chat da IA: diga só o nome
da variável.

As automações novas (Pexels, Pixabay e outras) devem ler as chaves do ambiente. Para elas
enxergarem o `.env`, chame `voz_config.carregar_env()` no início do script.

## Regras que todo prompt carrega

Os prompts repetem este contexto de propósito, para funcionarem sozinhos:

- A IA lê `AGENTS.md` e `sistema/CONSTRAINTS.md` antes de mexer em código.
- Nenhum limite de `sistema/CONSTRAINTS.md` é afrouxado para uma mudança passar.
- Nada de caminho da sua máquina nem chave de API dentro do código.
- Depois de mudar código, a IA roda a suíte e mostra o resultado.
- A [licença](../LICENSE) vale para o código e os textos que a IA gerar: gratuito, sem vender.
