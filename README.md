# Catálogo

Um guia e um motor para criar vídeos explicativos em português no formato
**"todos os tipos de X"**. Você escreve o roteiro. O sistema gera a narração, os
tempos por palavra, as cenas animadas e o vídeo final.

Feito para a comunidade do canal **Dark Sem Filtro**. É **gratuito e aberto**: você
pode usar, estudar, modificar e compartilhar. A única proibição de uso é **vender**: o
projeto, uma obra derivada ou qualquer coisa feita com ele entregue a clientes. Vídeos
publicados de graça no seu canal são livres. Veja a [licença](LICENSE).

## Veja o que ele faz

[`demonstracao/EP05-tipos-de-tempestade-final-v2.mp4`](demonstracao/EP05-tipos-de-tempestade-final-v2.mp4)
é um vídeo de 58 segundos sobre os tipos de tempestade. Foi feito de ponta a ponta
com este repositório: roteiro, voz, cenas, painéis de dados com unidade e render
final. A [página da demonstração](demonstracao/README.md) mostra como ele foi feito.

## Comece em 10 minutos

1. Instale [Python 3.10+](https://www.python.org/downloads/), [Node.js 22+](https://nodejs.org/) e o [FFmpeg](https://ffmpeg.org/download.html).
2. Baixe o projeto e rode o instalador na pasta dele.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

Linux ou macOS:

```bash
bash instalar.sh
```

O instalador cria o ambiente `.venv`, instala o HyperFrames, confere as
dependências fixadas e gera uma composição de teste. Não pede administrador e não
instala pacotes no sistema (os caches do pip, do npm e o Chromium do HyperFrames ficam nas pastas de cache do seu usuário). Deu erro? Use o [prompt de instalação](prompts/00-instalacao.md).

3. Abra a composição do episódio de exemplo, sem narração, no Studio do HyperFrames:

```sh
python pipeline/gen_comp.py episodios/EP05-tipos-de-tempestade/producao --spec episode.json --theme cartoon --out-dir hyperframes_demo
npx --no-install hyperframes preview episodios/EP05-tipos-de-tempestade/producao/hyperframes_demo
```

Nos comandos, use o Python do projeto: `.venv\Scripts\python.exe` no Windows ou
`.venv/bin/python` no Linux e no macOS. Ou ative o ambiente (`.\.venv\Scripts\Activate.ps1`
ou `source .venv/bin/activate`) e escreva só `python`.

## Como funciona

```text
roteiro.md → segments.json → roteiro_fonetico.json → WAVs por frase
            → timing.json + alignment.json → episode.json
            → storyboard + index.html + SVGs → revisão → gates → MP4
```

O roteiro guarda uma frase por segmento. A narração vem de qualquer provedor que
produza um WAV por frase. O alinhador descobre o tempo de cada palavra falada, e o
motor usa esses tempos para colocar imagens, números e textos na hora certa.
`gauntlet.py` confere o plano, `checa_densidade.py` procura trechos sem conteúdo e
`render_final.py` só renderiza com storyboard, composição e revisão atuais.

## Mapa do repositório

| Caminho | O que tem |
| --- | --- |
| `instalar.ps1`, `instalar.sh` | Instalação das dependências |
| `prompts/` | Prompts prontos para colar numa IA: instalação, voz, episódios, adaptações, Pexels, Pixabay |
| `pipeline/` | Os scripts Python do sistema e os testes |
| `sistema/` | Regras de roteiro, fonética, estilo visual, catálogo de cenas e a barra de qualidade |
| `episodios/EP05-tipos-de-tempestade/` | Episódio de exemplo: `roteiro.md`, `producao/cenas.json`, `producao/episode.json`, `producao/fontes.md` |
| `demonstracao/` | O vídeo de exemplo |
| `vendor/` | GSAP e fontes fixados por versão e sha256, para a composição não depender de CDN |
| `referencias/base/` | Referência visual original e contrato de tokens |
| `BIBLIA-CANAL.md` | Identidade e formato editorial do canal original |
| `AGENTS.md`, `CLAUDE.md` | Regras para agentes de IA que trabalham no projeto |

## Narração: escolha a sua voz

`pipeline/tts.py` troca de provedor sem mexer no resto:

| Provedor | O que é | Guia |
| --- | --- | --- |
| `omnivoice` | Modelo local que clona uma voz a partir de uma gravação sua | [sistema/FLUXO-NIVEL-1.md](sistema/FLUXO-NIVEL-1.md) |
| `comando` | Qualquer programa local, como o Piper | [prompts/02-voz-local.md](prompts/02-voz-local.md) |
| `openai` | API compatível com OpenAI, na nuvem ou num servidor local | [prompts/03-voz-api.md](prompts/03-voz-api.md) |

A configuração fica em `sistema/voz.json`. O que é só da sua máquina vai em
`sistema/voz.local.json`, que o git ignora. Use uma voz sua ou uma voz que você tem
autorização para usar. Confira a licença do modelo: os pesos do OmniVoice são só para
uso não comercial.

```sh
python pipeline/build_tts_manifest.py episodios/EP06-meu-tema/producao roteiro_fonetico_v1.json v1 --sem-referencia
python pipeline/tts.py episodios/EP06-meu-tema/producao/tts_manifest_v1.json --check
python pipeline/tts.py episodios/EP06-meu-tema/producao/tts_manifest_v1.json
```

Sem `--sem-referencia`, o manifesto pede `--ref-audio` e `--ref-text` (a sua voz de
referência e a transcrição dela), que o OmniVoice usa para clonar.

## Crie o seu episódio

```sh
python pipeline/novo_episodio.py "Tipos de vulcão" --id EP06
```

Escreva o roteiro em `episodios/EP06-tipos-de-vulcao/roteiro.md`:

```text
# EP06 — Tipos de vulcão

## Abertura
- `ab01` [gap:0.00] Existem quatro tipos de vulcão.
```

Depois siga o [prompt 04](prompts/04-novo-episodio.md), que leva da pesquisa ao MP4,
ou o [fluxo completo](sistema/FLUXO-NIVEL-1.md). Em resumo:

```sh
python pipeline/parse_roteiro.py episodios/EP06-tipos-de-vulcao/roteiro.md episodios/EP06-tipos-de-vulcao/producao/segments_v1.json
python pipeline/fonetica.py --in episodios/EP06-tipos-de-vulcao/producao/segments_v1.json --out episodios/EP06-tipos-de-vulcao/producao/roteiro_fonetico_v1.json
python pipeline/build_tts_manifest.py episodios/EP06-tipos-de-vulcao/producao roteiro_fonetico_v1.json v1 --sem-referencia
python pipeline/tts.py episodios/EP06-tipos-de-vulcao/producao/tts_manifest_v1.json
python pipeline/measure_durations.py episodios/EP06-tipos-de-vulcao/producao v1
python pipeline/assemble.py --project episodios/EP06-tipos-de-vulcao/producao --version v1
python pipeline/align_mms.py --project episodios/EP06-tipos-de-vulcao/producao --timing episodios/EP06-tipos-de-vulcao/producao/timing_v1.json --phonetic episodios/EP06-tipos-de-vulcao/producao/roteiro_fonetico_v1.json --audio-dir episodios/EP06-tipos-de-vulcao/producao/assets/audio/norm_v1 --out episodios/EP06-tipos-de-vulcao/producao/alignment_v1.json --device cpu
python pipeline/build_cenas.py episodios/EP06-tipos-de-vulcao/producao --timing timing_v1.json --align alignment_v1.json --segments segments_v1.json --out episode.json
python pipeline/gauntlet.py episodios/EP06-tipos-de-vulcao/producao/episode.json --strict
python pipeline/storyboard.py create episodios/EP06-tipos-de-vulcao/producao
python pipeline/gen_comp.py episodios/EP06-tipos-de-vulcao/producao --spec episode.json --theme cartoon
```

O alinhamento exige `torch`: instale com `instalar.ps1 -Alinhamento` ou
`bash instalar.sh --alinhamento`. Se o roteiro não tem `cenas.json`, `build_cenas.py`
escolhe as cenas sozinho. Com um `cenas.json` você controla objetos, painéis e textos.
Use o do EP05 como modelo.

Antes do render final, olhe os quadros (`npx --no-install hyperframes snapshot ...`),
registre a revisão com `python pipeline/storyboard.py review ...` e só então rode
`python pipeline/render_final.py <pasta-producao> --output final-v1.mp4`. A CLI direta
do HyperFrames serve para pré-visualizar e não passa pelos gates.

O motor tem objetos e cenas ligados aos temas dos episódios de origem (estrelas,
planetas, clima, biomas, energia). Um tema novo pode pedir mais: o
[prompt 05](prompts/05-adaptar-tema.md) ensina a acrescentar.

## Use IA para fazer o trabalho pesado

A pasta [`prompts/`](prompts/README.md) tem prompts prontos, do primeiro dia às
adaptações:

| Prompt | Para quê |
| --- | --- |
| [00](prompts/00-instalacao.md) | Instalar e resolver erro de instalação |
| [01](prompts/01-entender-o-projeto.md) | Um tour guiado |
| [02](prompts/02-voz-local.md) · [03](prompts/03-voz-api.md) | Voz local ou por API, e como acrescentar outra API |
| [04](prompts/04-novo-episodio.md) | Do tema ao MP4 |
| [05](prompts/05-adaptar-tema.md) | Ilustrações, cenas e widgets novos |
| [06](prompts/06-adaptar-canal-e-idioma.md) | Identidade do seu canal e outro idioma |
| [07](prompts/07-fonte-pexels.md) · [08](prompts/08-fonte-pixabay.md) | Vídeos e fotos do Pexels e do Pixabay |
| [09](prompts/09-outras-automacoes.md) | Base para qualquer automação nova |
| [10](prompts/10-resolver-erros.md) | Diagnosticar um erro |

O sistema é uma boa base para outras automações: o padrão é um script por etapa, que
lê e grava arquivos na pasta do episódio. O [prompt 09](prompts/09-outras-automacoes.md)
mostra onde plugar cada ideia.

## Verificação

```sh
python -m unittest discover -s pipeline -p "test_*.py" -v
python pipeline/verifica.py
```

A suíte roda sem GPU, sem voz e sem render. `verifica.py` roda, em ordem, a barra de
qualidade, as dependências fixadas, os testes, uma composição de teste, o
`hyperframes check` e a vigia da barra. O projeto não usa integração contínua: rode
isso na sua máquina antes de enviar uma contribuição.

## A barra de qualidade

[`sistema/CONSTRAINTS.md`](sistema/CONSTRAINTS.md) é a fonte única dos limites:
ritmo do plano, buraco de montagem, tolerância de duração, alvos de áudio e tokens
de referência. Os scripts leem de lá. Afrouxar um limite exige uma exceção escrita,
com responsável e data, e `python pipeline/floor_guard.py` acusa quem edita um limite
sem isso.

```sh
python pipeline/constraints.py --list
python pipeline/floor_guard.py
python pipeline/vendor.py
```

## Limites atuais

- O repositório não traz voz, modelo, referência vocal, música nem efeitos sonoros de
  terceiros. Cada pessoa usa os seus. O vídeo de exemplo foi narrado com OmniVoice.
- A faixa de duração de episódio em `sistema/CONSTRAINTS.md` (10 a 15 minutos) é a do
  canal original. Vídeos curtos como o de exemplo são demonstrações.
- O alinhamento MMS pode falhar em CUDA. Use `--device cpu` no `align_mms.py`.
- `hyperframes snapshot` pode enviar os quadros a um serviço de visão (Gemini) se você
  tiver uma chave configurada no ambiente. Para evitar, não defina essa chave.
- O motor não tem cena de raio, de apresentador (Talking Head, Split, PiP) nem edição
  automática de filmagem. Veja o [catálogo de cenas](sistema/CENAS-NIVEL-1.md).
- Os roteiros são material editorial. Confira cada número em fonte primária antes de
  publicar (o EP05 tem as fontes em `producao/fontes.md`).

## Contribuir

Leia o [guia de contribuição](CONTRIBUTING.md) e o [código de conduta](CODE_OF_CONDUCT.md).
Correções, ilustrações novas, provedores de voz e prompts melhores são bem-vindos.

## Licença

[Licença Gratuita e Aberta do Dark Sem Filtro](LICENSE): use, estude, modifique e
compartilhe de graça. É proibido vender o projeto, obras derivadas ou trabalhos feitos com
ele para clientes. Quem redistribui código ou documentação mantém a mesma licença.
Modelos, vozes, fontes e mídia de terceiros mantêm as licenças deles; veja
[THIRD_PARTY.md](THIRD_PARTY.md).
