---
name: catalogo-sistema-video
description: Sistema de produção de vídeo do canal Catálogo (dark/faceless PT-BR, formato "todos os tipos de X explicados"). Use SEMPRE que for mexer em roteiro, capítulos, cenas, ilustrações SVG, composição HyperFrames, temas visuais, voz, assets ou pipeline deste canal — inclusive ao corrigir sincronia, densidade de cena, tipografia ou ao criar um episódio novo.
---

# Catálogo — sistema de vídeo

As regras comuns a todos os agentes estão em `AGENTS.md`. Para narração local,
referências, storyboard e render final, siga `sistema/FLUXO-NIVEL-1.md`, o
catálogo `sistema/CENAS-NIVEL-1.md` e a barra `sistema/CONSTRAINTS.md`. Os
números dos gates vivem na barra, não neste arquivo. O final validado usa
`pipeline/render_final.py`.

Canal dark/faceless PT-BR. Formato: **catálogo** — um tema por capítulo, com o nome
em uma cartela breve, e **objetos vetoriais animados** + motion graphics e textos
entrando sincronizados na palavra falada.

> **Regra visual do canal:** fundo é SEMPRE escuro — **nunca tela branca**. O visual é
> 100% **motion graphics vetorial**: diagramas em tomadas dedicadas e objetos concretos animados
> em primeiro plano, escolhidos pelo sentido da fala.

Runtimes externos: **HyperFrames** (`npx hyperframes`) · **FFmpeg** · uma fonte de
narração à escolha do usuário. OmniVoice é uma opção local, mas os pesos
pré-treinados `k2-fsa/OmniVoice` têm licença **CC-BY-NC**. A produção mora em
`episodios/EP05-tipos-de-tempestade/producao/`; instruções portáveis estão em `README.md`.

Episódio de exemplo: `EP05`, tipos de tempestade (vídeo de 58 s que demonstra o motor de ponta a ponta).
O vídeo pronto fica em `demonstracao/`.

## 1. Regra de ouro

Regra de produção vai no **motor** (`pipeline/`), nunca como dado do episódio.
O episódio só entrega: `roteiro.md` + `cenas.json`. Se algo quebra num vídeo, conserta
no motor.

## 2. Direção visual observada nas referências

Os arquivos de análise em `referencia/_analise/` são locais e não fazem parte do
repositório público. A direção visual extraída dessa análise é:

- Capítulo = tema, com **título breve** na entrada (até 2,4 s); não segurar cartela estática.
- Fundo **escuro sempre**, escolhido por cena. O diagrama não é fundo permanente.
  Planejar tipos e entradas em `plano_cenas.json` antes de gerar os elementos.
- Cada trecho da fala recebe **objetos relacionados** da biblioteca `ilustras.py`;
  ações como destruir/inundar/girar precisam de movimento próprio. Sem objeto
  relacionado, usar o par visual do fenômeno, nunca deixar só o fundo.
- **Dados viram motion graphics:** número/porcentagem → widget animado com a UNIDADE
  (velocímetro km/h, termômetro/graus, escala K, %, hectares, km, duração...).
- **Nunca esquecer a unidade** do número dito (km/h, graus, K, %, hectares, km, anos).
- Callouts de número ("2.500 K", "5,5 TONELADAS", "60% a 80%") em texto grande.
- Legendas curtas ligadas à cena (não "sopa de palavras").

Tema do canal: `cartoon` (PT) — texto azul grosso com contorno preto e glow.
(`doodle` é legado da versão EN e também vive no escuro.)

## 3. Formato do roteiro

`episodios/EPxx-<tema>/roteiro.md`:

```
# EP05 — Tipos de tempestade

## Tornado
- `to01` [gap:0.35] Tornado.
- `to02` [gap:0.15] Uma coluna de ar que gira e toca o chão.
```

- `#` título do episódio · `##` abre um CAPÍTULO (o texto vira o título na tela).
- `- \`id\`` uma linha falável, id único. `[gap:X]` = pausa antes (s).
- **Números podem ficar em algarismo** — o `fonetica.py` expande antes do TTS.

## 4. O plano visual (`cenas.json`)

Opcional: sem ele o motor **autogera** (número→callout, enumeração→lista,
palavra-chave→objeto, senão a ilustração do capítulo). Com ele, você controla.

```jsonc
{
  "theme": "cartoon",
  "chapters": {
    "ana-vermelha": { "titulo": "ANÃ VERMELHA", "fundo": "space", "cor": "#29a8ff", "ilustra": "red_dwarf" }
  },
  "cenas": {
    "av06": [
      { "tipo": "ilustra", "id": "hourglass", "pos": "esquerda" },
      { "tipo": "callout", "texto": "1 TRILHÃO DE ANOS", "palavra": "trilhão", "pos": "dir" }
    ]
  }
}
```

Tipos de elemento: **`mg`** (motion graphic — ver abaixo), **`ilustra`** (objeto
contextual animado), `callout` (`texto`+`sub`), `palavra` (destaque/pílula), `lista`,
`frase`, `foto`, `video`, `transicao` (sweep de capítulo), `textao` e `heroi`.
Posições: `centro`, `centro_alto`, `centro_baixo`, `esquerda`, `direita`; callouts:
`baixo`, `acima`, `esq`, `dir`, `centro`.

### Motion graphics (`pipeline/mg.py`) — o padrão visual

Duas famílias de `mg`:

```jsonc
// Receita contextual disponível para tomadas de fenômeno; não cobre o capítulo inteiro.
"chapters": { "tornado": { "mg": "vortex", "cor": "#56ccff" } }

// WIDGET de dados: cartão escuro posicionado como objeto, com a UNIDADE.
"cenas": { "tn03": [
  { "tipo": "mg", "id": "speed_gauge", "modo": "panel", "pos": "centro_alto",
    "params": { "valor": 300, "max": 400, "unidade": "km/h" }, "palavra": "300" }
]}
```

`python pipeline/mg.py` lista as receitas. Cenas: `vortex` (tornado), `spiral_storm`
(furacão), `seismic`, `wave_stack` (tsunami), `wildfire`, `water_rise`, `drought`,
`snowstorm`, `volcano`, `wind_field`, `ocean_depth`, `globe_grid`, `star_warp`,
`star_glow` (estrela por `cor`), `hr_diagram`. Widgets: `speed_gauge`, `magnitude_scale`,
`thermometer`, `pct_ring`, `area_counter`, `distance_ruler`, `duration_bar`,
`size_compare`, `k_scale`.

- `plan_scenes` decide o episódio inteiro antes da montagem: objeto, detalhe, dados,
  dado em texto e fenômeno. O fenômeno base é candidato, nunca fundo obrigatório.
- O diretor (`direct_segment`) emite: **número → widget com unidade** (ou `callout` se
  não houver widget) + legenda curta; sem número → legenda da cena (1ª do capítulo) ou
  palavra-chave.
- Unidades reconhecidas e normalizadas em `_UNIT`/`_unit_display` (`km/h`, `graus`, `K`,
  `%`, `hectares`, `km`, minutos/semanas...). Sempre exiba a unidade.
- A animação é toda no timeline GSAP único e pausado (seek-safe): kinds `mg_loop`,
  `mg_once`, `mg_draw`, `mg_count`. **Não** anime objeto JS puro (`{v:0}`) — o runtime
  do HyperFrames não lida bem; conte pelo `this.progress()` do próprio elemento.

### Objetos contextuais

`ilustras.py` é a biblioteca reutilizável de objetos. `auto_elements()` chama
`semantic_objects()` em toda cena, inclusive quando `cenas.json` define textos ou
widgets. A escolha considera palavras alinhadas, tema, fenômeno e ação; um objeto
`ilustra` explícito continua sendo a decisão autoral. Painéis de dados e callouts
ocupam a janela central, e os objetos retomam depois deles se a fala continuar.

### Diretor de cena (o "cérebro")

`direct_segment()` e `auto_elements()` no `build_cenas.py` emitem, por segmento:
- **objetos contextualizados** com entrada alinhada à palavra e ações vetoriais;
- o tipo de cada cena vem do plano prévio (`plan_scenes`);
- **número** → widget `mg` com UNIDADE (via `build_widget`/`WIDGET_UNITS`) + legenda;
  se nenhum widget casar, vira `callout` com o número + unidade (nunca perde a unidade);
- **sem número** → legenda curta da cena (1ª do capítulo) ou palavra-chave saliente.

Regras:
- **Âncora é a palavra falada** (`palavra`), nunca offset fixo. Sem a palavra, cai para
  uma fração do segmento (último recurso). O mapeamento editorial→falado (`tempo.py`)
  consome o bloco de números expandidos ("2500"→"dois mil e quinhentos").
- **Gauntlet:** `gauntlet.py --strict` reprova objeto sobreposto, **texto sobre objeto/motion** e
  **ritmo parado**. Cenas `mg` de tela cheia contam apenas como fundo e não satisfazem
  a cobertura de objetos; o intervalo máximo padrão é 0,9 s. Rode
  `build_cenas → gauntlet --strict → gen_comp`.

## 5. Motion graphics (`pipeline/mg.py`)

A biblioteca vetorial de motion graphics é o padrão visual (ver §4). Cada receita devolve
`{vb, mode, inner, anims}`: `inner` é SVG puro e `anims` é uma lista de tweens GSAP
(`mg_loop`/`mg_once`/`mg_draw`/`mg_count`). Para adicionar uma receita: escreva a função
`scene_*`/`w_*` e registre em `RECIPES`. As cores vêm de parâmetros (`cor`) ou do tema.

`ilustras.py` fornece os objetos de primeiro plano em todos os episódios.

## 5b. Objetos (`pipeline/ilustras.py`)

Biblioteca SVG autoral (nada de arte de terceiros), estilo flat com contorno grosso.
`python pipeline/ilustras.py --list` mostra os ids. As estrelas são geradas por
`star_ball()`; os objetos são funções (`hourglass`, `thermometer`, `snowflake`, `flame`,
`lightning`, `comet`, `planet_rings`, `brain`, `crown`... 60+). O ponto do canal é
**mostrar o que é falado**: o dicionário `WORD_PROP` em `build_cenas.py` casa cada
palavra (e sinônimos) com um objeto — "frio"→snowflake, "calor"→flame, "energia"→lightning.

A biblioteca é **temática do canal** (não do episódio): planetas, desastres naturais,
usinas, biomas do Brasil, vida/ciência e mundo — para reaproveitar em qualquer vídeo.
**Antes de gerar um episódio novo, consulte `ilustras.py --list`** e reutilize os objetos;
só crie novos se faltar.

Para adicionar um objeto: escreva a função e registre em `LIB` (e em `ALIASES`). Para
que ele apareça na autogeração, adicione as palavras em `WORD_PROP`. O `gen_comp.py`
exporta só os usados (inclusive os de `imagens`) para `hyperframes/assets/ilustra/`.

## 6. Pipeline (episódio novo)

```powershell
$repo = (Get-Location).Path  # execute a partir da raiz do clone
$p = Join-Path $repo "episodios/EP05-tipos-de-tempestade/producao"
$rot = Join-Path $repo "episodios/EP05-tipos-de-tempestade/roteiro.md"
$v = "v1"
$motor = Join-Path $repo "pipeline"
Set-Location $p

# 1) roteiro -> segmentos -> texto falável
python (Join-Path $motor "parse_roteiro.py") $rot segments_$v.json
python (Join-Path $motor "fonetica.py") --in segments_$v.json --out roteiro_fonetico_$v.json

# 2) TTS: gere WAVs por segmento com uma voz para a qual você tem direitos
python (Join-Path $motor "build_tts_manifest.py") $p roteiro_fonetico_$v.json $v `
  --ref-audio "caminho/para/voz.wav" --ref-text-file "caminho/para/voz.txt"
python (Join-Path $motor "tts.py") (Join-Path $p "tts_manifest_$v.json")  # provedor em sistema/voz.json

# 3) durações + master (loudnorm two-pass, -16 LUFS)
python (Join-Path $motor "measure_durations.py") $p $v
python (Join-Path $motor "assemble.py") --project $p --version $v

# 4) alinhamento por palavra (MMS_FA; requer torch, torchaudio e uroman)
python (Join-Path $motor "align_mms.py") --project $p `
  --timing timing_$v.json --phonetic roteiro_fonetico_$v.json `
  --audio-dir assets/audio/norm_$v --out alignment_$v.json
# Se aparecer "Could not run 'torchaudio::forced_align' ... 'CUDA' backend", use --device cpu.

# 5) cenas + composição
python (Join-Path $motor "build_cenas.py") $p --timing timing_$v.json --align alignment_$v.json `
  --segments segments_$v.json --cenas cenas.json --out episode.json
python (Join-Path $motor "gauntlet.py") episode.json --fix
python (Join-Path $motor "gauntlet.py") episode.json --strict
python (Join-Path $motor "critica.py") $p brief        # prompt adversarial de direção
python (Join-Path $motor "critica.py") $p review --critic "quem leu" `
  --notas "..." --achados "..." --verdict go
python (Join-Path $motor "storyboard.py") create $p
python (Join-Path $motor "gen_comp.py") $p --spec episode.json --theme cartoon

# 6) gates
python (Join-Path $motor "checa_densidade.py") hyperframes\index.html
npx hyperframes check hyperframes --json

# 7) preview de 60 s: o script retorna uma pasta temporária fora da origem
$preview = python (Join-Path $motor "prepare_preview.py") --project $p --seconds 60
npx hyperframes render $preview --quality draft --fps 30 --workers 4 --output renders\preview_60s_$v.mp4
```

Os limites (`--max-gap`, `--max`) não vão na linha de comando: vivem em
`sistema\CONSTRAINTS.md` e são lidos pelos scripts. Passá-los à mão é caminho de
exceção, e `pipeline\floor_guard.py` acusa a flag no diff.

Depois da revisão humana, registre responsável, notas e quadros com
`storyboard.py review` (veja `sistema/FLUXO-NIVEL-1.md`). O final é executado
por `python (Join-Path $motor "render_final.py") $p --output "final_$v.mp4"`.
O wrapper verifica storyboard, composição, crítica de direção e revisão antes de
executar os gates. CLI direta fica reservada a demos e previews; ela contorna
esse contrato, e o plugin `.opencode/plugin/render-gate.js` recusa o render
direto para que a exceção seja visível.

Para um **segundo episódio em paralelo**, use uma pasta-projeto separada (ex.:
`episodios/EP06-outro-tema/producao/`) como `--project`; todos os scripts aceitam qualquer pasta. Sem
`cenas.json` na pasta, o motor **autogera** tudo (é o teste de generalização).

## 7. Verificação visual barata

Em vez de renderizar para conferir, use `snapshot` em timestamps específicos:

```powershell
npx hyperframes snapshot hyperframes --at "40,120,200,330,492" --no-end -o renders\snaps
```

Gera PNGs + `contact-sheet.jpg`. É o jeito rápido de julgar legibilidade, ritmo e
coerência com a fala sem renderizar o vídeo inteiro.

## 8. Gates de qualidade (o que impede vídeo ruim)

Os números vivem em `sistema\CONSTRAINTS.md` e são lidos pelos scripts. Este é o
resumo; o arquivo é a fonte.

- **Densidade:** `checa_densidade.py` — nenhum trecho acima de
  `montagem.max_buraco_s` sem conteúdo.
- **Ritmo/posicionamento:** `gauntlet.py --strict` — `texto_obj`, `invisivel`,
  `overlap`, `plano_intervalo` e `plano_repetido` têm de zerar; `--strict` também
  reprova por ritmo parado acima de `plano.max_gap_s` e por repetição.
- **Alinhamento:** `alignment_vX.json` precisa de `editorial_aligned_ratio` ≥
  `alinhamento.editorial_ratio_minimo` em todo segmento (o MMS_FA forçado chega a
  1.0 no EP05). Abaixo disso as âncoras de cena caem no lugar errado.
- **Áudio:** master em `audio.lufs_integrado` / `audio.true_peak_dbtp` /
  `audio.lra_lu`, 48 kHz estéreo.
- **Duração do MP4:** `render.tolerancia_duracao_s` de diferença para
  `episode.total` — conferido com ffprobe no `render_final.py`.
- **Barra não se afrouxa em silêncio:** `floor_guard.py` acusa limite editado,
  flag passada na mão, teste pulado, verificador calado e stub no motor.
- **Direção:** nenhum número acima acusa repetição de direção ou falta de
  contraste. Isso é `critica.py`, com contexto fresco — e continua não sendo
  aprovação humana.
- **Fidelidade visual:** conferir quadros com `snapshot`; referências locais são
  opcionais e não são distribuídas no repositório.
- **Movimento por cena:** cada `fundo` tem parallax ambiente (`scale(1.06)` +
  `drift`). É o que impede um painel de 4 s cuja única animação é a entrada de
  1,2 s de trippingar `motion_frozen`. Não remova o drift sem rodar
  `hyperframes check`.
- **Dependências:** GSAP e as woff2 de Baloo 2, Nunito, Patrick Hand e Caveat
  estão em `vendor/`, com versão e sha256 em `vendor/PINS.json`. A composição
  não busca nada em CDN; `python pipeline/vendor.py` confere cada hash.
- **Verificação completa local:** `python pipeline/verifica.py` roda as mesmas
  etapas do projeto, Gate 3 incluído. Etapa pulada aparece no resumo, nunca some.

## 8.1 Crítica de direção (contexto fresco)

O `gauntlet` tem regra, não gosto. Depois do `--fix`, e **antes** de gerar o
storyboard, peça a leitura adversarial de `plano_cenas.json` por alguém sem o
raciocínio de quem montou:

```powershell
python (Join-Path $motor "critica.py") $p brief      # o prompt, pronto
```

O registro (`critica.json`) carrega `human_approval: false` e fica amarrado por
hash ao plano e ao contrato lidos: editar qualquer um dos dois invalida a
crítica. Por padrão ela é recomendada; `direcao.critica_obrigatoria` no
CONSTRAINTS.md é quem decide se ela bloqueia o final.

## 9. Áudio / voz

- Voz: escolha um áudio de referência com autorização de uso e forneça a
  transcrição em `.txt` ou `--ref-text`. Os arquivos de voz ficam locais.
- Semente fixa por segmento (`90000 + n*1000`): `@2` no id do roteiro regera só aquela
  frase sem mexer nas outras.
- Regras de fonética: `sistema\FONETICA-PTBR.md`. Número por extenso, sigla falada,
  `tipo K` → `tipo cá`, `2500 K` → `dois mil e quinhentos Kélvin`.
- O OmniVoice lê pontuação: a emoção vem de vírgula/ponto/parágrafo, não de tags.

### Efeitos sonoros (SFX)

Acento sonoro SÓ em momento especial — **nunca em todo corte**. O `collect_sfx`
(no `build_cenas.py`) gera os cues sozinho: transição de capítulo→`whoosh`, widget `mg`→
`pop`, tela-herói→`impact-bass-1` (supernova→`impact-bass-2`), `textao`→`whoosh-short`,
gráfico/medidor/barra→`pop`, comparação/crescimento→`sparkle`, pergunta final→`ping`; cues a
menos de 1,1 s são fundidos (vence o de maior prioridade). O `gen_comp.py` vira cada cue em
`<audio>` (track 91, `data-volume` ~0.35) e copia só os arquivos usados para
`hyperframes/assets/sfx/`.

A biblioteca de nomes fica em `episodios/EP05-tipos-de-tempestade/producao/assets/sfx/manifest.json`. Os MP3 são
opcionais, ficam locais e não são distribuídos no repositório (ver `CREDITS.md`):
`whoosh`, `whoosh-short`, `whoosh-cinematic`, `pop`, `ping`, `sparkle`, `chime`,
`impact-bass-1/2`, `riser`, `glitch-1/2/3`, `click`, `click-soft`, `error`, `notification`,
`key-press`, `typing`. Para forçar um cue num ponto exato, adicione um elemento
`{"tipo":"sfx","nome":"riser","start":12.3,"gain":0.35}` no plano.

## 10. Compliance

- Nada de footage ou efeitos de terceiros sem licença adequada ao uso e à
  distribuição pretendidos. Arte SVG do motor é original; SFX locais são opcionais.
- Verificar separadamente a licença da voz e do modelo TTS. Os pesos
  pré-treinados `k2-fsa/OmniVoice` são CC-BY-NC.
- Números com fonte; sem desinformação.
- Marcar conteúdo gerado por IA no upload.
- A referência serve para **análise**, não para reaproveitamento de mídia.
