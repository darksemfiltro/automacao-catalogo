# CONSTRAINTS — a barra de qualidade do canal

Este arquivo é a **fonte única** dos limites do motor. O número vive aqui; o
código lê aqui; a documentação cita aqui. Antes ele vivia em pelo menos sete
lugares (defaults do CLI, literais em `render_final.py`, README, FLUXO,
CONTRIBUTING e a skill) e já divergira: a skill anunciava `--max-gap 2.8`
enquanto o resto do repositório usava `0.9`.

Duas regras que acompanham o arquivo:

- **Esta barra não é afrouxada para fazer uma mudança passar.** Se um limite
  precisa ceder, isso é uma decisão editorial com responsável e data de
  expiração na tabela de exceções, não um número editado no lugar.
- **Toda linha com número tem um comando que produz o veredicto.** Limite sem
  comando é aspiração, não restrição.

`pipeline/constraints.py` valida e carrega este arquivo;
`pipeline/floor_guard.py` vigia o diff para que afrouxar a barra seja barulhento.
`AGENTS.md` e `CLAUDE.md` apontam para cá.

## Piso — sempre aplicado, sem configuração

Regras que não têm número porque não são negociáveis:

1. Final somente por `pipeline/render_final.py`. A CLI do HyperFrames é
   preview/demo e não constitui final validado.
2. Não inventar aprovação humana. `storyboard.py review` registra uma revisão
   efetivamente realizada, com responsável, observações e quadros usados.
3. Não cortar silêncio detectado sem remontar e realinhar todos os tempos
   derivados. Pausa expressiva é conteúdo.
4. Não copiar voz, modelo de voz ou licença de terceiros para distribuição.
5. Não fixar caminho da máquina do mantenedor. Ferramentas rodam da raiz e
   aceitam caminho do usuário.
6. Sem segredo no código, nos manifests de exemplo ou no histórico.
7. Sem `TODO`, stub que lança ou `except` vazio no motor.
8. Editar as fontes, nunca o storyboard derivado: `roteiro.md` e `cenas.json`.

## Limites com número

| Chave | Valor | Por quê | Verificado por | Roda em |
|-------|-------|---------|----------------|---------|
| `plano.max_gap_s` | 0,9 s | trecho de plano sem conteúdo vira tela parada; 0,9 s é abaixo do-limite de perception de movimento em 30 fps | `python pipeline/gauntlet.py <proj>/episode.json --strict` | todo render final |
| `plano.tolerancia_adjacencia_s` | 0,05 s | arredondamento de tempo aceito entre cenas; acima disso é lacuna/sobreposição real | `python -m unittest pipeline.test_nivel1` | toda edição do motor |
| `montagem.max_buraco_s` | 2,5 s | maior intervalo sem clipe acima de z-index 5 tolerated antes de a tela parecer vazia | `python pipeline/checa_densidade.py <comp>/index.html` | todo render final |
| `montagem.min_z` | 5 | faixa de trilhas considerada "conteúdo"; abaixo disso é fundo ou legenda | `python pipeline/checa_densidade.py` | toda verificação de densidade |
| `render.tolerancia_duracao_s` | 0,15 s | divergência entre o MP4 e `episode.total` acima disso indica plano e render fora de sincronia | `python pipeline/render_final.py` (ffprobe) | todo render final |
| `audio.lufs_integrado` | −16 LUFS | loudness de narração falada para YouTube; normalização two-pass por segmento | `python pipeline/assemble.py` (ebur128) | toda montagem |
| `audio.true_peak_dbtp` | −1,5 dBTP | evita clip em plataforma que recomprime | `python pipeline/assemble.py` (ebur128) | toda montagem |
| `audio.lra_lu` | 11 LU | largura de loudness; acima disso a dinâmica fica cansativa | `python pipeline/assemble.py` (ebur128) | toda montagem |
| `audio.bed_lufs` | −30 LUFS | o bed musical existe para sustentação, não para competir com a narração | `python pipeline/assemble.py` (ebur128) | toda montagem com bed |
| `alinhamento.editorial_ratio_minimo` | 0,95 | MMS é forçado; abaixo disso parte do roteiroeditorial não foi localizada na fala e as âncoras de cena ficam no lugar errado | `python pipeline/align_mms.py` + leitura de `alignment_<v>.json` | todo episódio narrado |
| `referencias.tamanho_min_px` | 24 px | abaixo disso o texto não é legível em 1080p | `python -m unittest pipeline.test_nivel1` | toda edição de tokens |
| `referencias.tamanho_max_px` | 160 px | acima disso o texto estoura o quadro | `python -m unittest pipeline.test_nivel1` | toda edição de tokens |
| `episodio.duracao_min_s` | 600 s | 10 min é o piso de formato do canal (`BIBLIA-CANAL.md`) | `python pipeline/build_cenas.py` + `episode.json` | todo episódio |
| `episodio.duracao_max_s` | 900 s | 15 min é o teto de formato do canal | `python pipeline/build_cenas.py` + `episode.json` | todo episódio |
| `direcao.critica_obrigatoria` | falso | a crítica de direção em contexto fresco é recomendada e registrada; torná-la bloqueante é decisão do mantenedor, não um padrão presumido | `python pipeline/critica.py validate` | registro de direção |

Os limites `plano.*`, `montagem.*` e `render.*` **não são opcionais**: passar a
flag na mão é o caminho da exceção, e o `floor_guard` acusa a flag.

## Ratchets — medido, ainda não verificado por gate

| Métrica | Hoje | Direção |
|---------|------|---------|
| Testes na suíte do motor | 150 | não pode cair |
| `editorial_aligned_ratio` mínimo em EP05 | 1,0 (18/18 segmentos) | não pode cair abaixo de `alinhamento.editorial_ratio_minimo` |
| Achados do gauntlet em plano novo | 0 | não pode subir |

## Exceções

Nenhuma. Se aparecer uma linha aqui, ela precisa de responsável e data, e
`floor_guard` acusa a linha nova tanto quanto a edição do limite.

## Dependências remotas — declaradas, não verificadas

Os hashes do `workflow.fingerprint` cobrem arquivos locais. Estas dependências
não são cobertas e são a razão de o primeiro render exigir internet:

| Dependência | Versão | Situação |
|-------------|--------|----------|
| GSAP | 3.14.2 | vendorizado em `vendor/gsap.min.js` com `PINS.json`; cópia local entra no hash da composição. Sem o arquivo local, `gen_comp.py` volta à CDN e avisa. |
| Baloo 2, Nunito, Patrick Hand, Caveat | `@fontsource` 5.3.0 (SIL OFL 1.1) | vendorizadas em `vendor/fonts/*.woff2`, sha256 por arquivo, com `fonts.css` gerado a partir dos pinos. Sem os arquivos, `gen_comp.py` volta ao Google Fonts e avisa. `vendor/fonts/LICENCA-OFL-1.1.txt` acompanha o pacote. |
| Chromium do HyperFrames/Playwright | revisão baixada na primeira execução | **não coberto por hash**. `npx --no-install hyperframes doctor` antes de confiar em reprodutibilidade. |
| Registro do HyperFrames | URL raw do GitHub em `hyperframes.json` | só é consultado se a composição usar blocos do registro. O EP05 não usa. |

Ou seja: com `vendor/` no clone, `index.html` **não referencia nenhuma URL
remota** de biblioteca ou fonte. O que resta depende de rede é o navegador, e
isso está declarado acima em vez de descoberto no meio de um render.

Verifique com `python pipeline/vendor.py` (confere todo sha256) e
`python pipeline/verifica.py` (roda as verificações do projeto, incluindo o
Gate 3).

## O que este arquivo não faz

Ele não mede qualidade editorial. Ele reprova overlap, objeto invisível,
texto sobre objeto, tela parada e buraco de montagem — regras mecânicas. Se a
direção do episódio está repetitiva, feia ou sem contraste com a fala, nenhum
número aqui acusa: isso é `pipeline/critica.py` e revisão humana registrada.

```json
{
  "schema_version": 1,
  "revisado_em": "2026-10-04",
  "piso": [
    "Final somente por pipeline/render_final.py",
    "Nao inventar aprovacao humana",
    "Nao cortar silencio sem remontar e realinhar tempos derivados",
    "Nao copiar voz ou modelo para distribuicao",
    "Nao fixar caminho da maquina do mantenedor",
    "Sem segredo no codigo",
    "Sem TODO, stub que lanca ou except vazio no motor",
    "Editar as fontes, nunca o storyboard derivado"
  ],
  "limites": {
    "plano.max_gap_s": {
      "valor": 0.9,
      "unidade": "s",
      "motivo": "trecho de plano sem conteudo vira tela parada",
      "verificado_por": "python pipeline/gauntlet.py <proj>/episode.json --strict",
      "roda_em": "todo render final"
    },
    "plano.tolerancia_adjacencia_s": {
      "valor": 0.05,
      "unidade": "s",
      "motivo": "arredondamento aceito entre cenas; acima disso e lacuna ou sobreposicao",
      "verificado_por": "python -m unittest discover -s pipeline -p test_*.py",
      "roda_em": "toda edicao do motor"
    },
    "montagem.max_buraco_s": {
      "valor": 2.5,
      "unidade": "s",
      "motivo": "maior intervalo sem clipe de conteudo antes de a tela parecer vazia",
      "verificado_por": "python pipeline/checa_densidade.py <comp>/index.html",
      "roda_em": "todo render final"
    },
    "montagem.min_z": {
      "valor": 5,
      "unidade": "z-index",
      "motivo": "faixa de trilhas considerada conteudo; abaixo disso e fundo ou legenda",
      "verificado_por": "python pipeline/checa_densidade.py",
      "roda_em": "toda verificacao de densidade"
    },
    "render.tolerancia_duracao_s": {
      "valor": 0.15,
      "unidade": "s",
      "motivo": "divergencia entre o MP4 e episode.total acima disso indica fora de sincronia",
      "verificado_por": "python pipeline/render_final.py (ffprobe)",
      "roda_em": "todo render final"
    },
    "audio.lufs_integrado": {
      "valor": -16.0,
      "unidade": "LUFS",
      "motivo": "loudness de narracao falada para YouTube, two-pass por segmento",
      "verificado_por": "python pipeline/assemble.py (ebur128)",
      "roda_em": "toda montagem"
    },
    "audio.true_peak_dbtp": {
      "valor": -1.5,
      "unidade": "dBTP",
      "motivo": "evita clip em plataforma que recomprime",
      "verificado_por": "python pipeline/assemble.py (ebur128)",
      "roda_em": "toda montagem"
    },
    "audio.lra_lu": {
      "valor": 11.0,
      "unidade": "LU",
      "motivo": "largura de loudness; acima disso a dinamica fica cansativa",
      "verificado_por": "python pipeline/assemble.py (ebur128)",
      "roda_em": "toda montagem"
    },
    "audio.bed_lufs": {
      "valor": -30.0,
      "unidade": "LUFS",
      "motivo": "o bed musical sustenta, nao compete com a narracao",
      "verificado_por": "python pipeline/assemble.py (ebur128)",
      "roda_em": "toda montagem com bed"
    },
    "alinhamento.editorial_ratio_minimo": {
      "valor": 0.95,
      "unidade": "ratio",
      "motivo": "abaixo disso parte do roteiro editorial nao foi localizada na fala e as ancoras de cena ficam no lugar errado",
      "verificado_por": "python pipeline/align_mms.py e leitura de alignment_<v>.json",
      "roda_em": "todo episodio narrado"
    },
    "referencias.tamanho_min_px": {
      "valor": 24,
      "unidade": "px",
      "motivo": "abaixo disso o texto nao e legivel em 1080p",
      "verificado_por": "python -m unittest discover -s pipeline -p test_*.py",
      "roda_em": "toda edicao de tokens"
    },
    "referencias.tamanho_max_px": {
      "valor": 160,
      "unidade": "px",
      "motivo": "acima disso o texto estoura o quadro",
      "verificado_por": "python -m unittest discover -s pipeline -p test_*.py",
      "roda_em": "toda edicao de tokens"
    },
    "episodio.duracao_min_s": {
      "valor": 600,
      "unidade": "s",
      "motivo": "10 min e o piso de formato do canal",
      "verificado_por": "python pipeline/build_cenas.py e episode.json",
      "roda_em": "todo episodio"
    },
    "episodio.duracao_max_s": {
      "valor": 900,
      "unidade": "s",
      "motivo": "15 min e o teto de formato do canal",
      "verificado_por": "python pipeline/build_cenas.py e episode.json",
      "roda_em": "todo episodio"
    },
    "direcao.critica_obrigatoria": {
      "valor": false,
      "unidade": "booleano",
      "motivo": "a critica de direcao em contexto fresco e recomendada e registrada; bloqueia-la e decisao do mantenedor",
      "verificado_por": "python pipeline/critica.py validate",
      "roda_em": "registro de direcao"
    }
  },
  "medido": [
    {"metrica": "testes na suite do motor", "hoje": 150, "direcao": "nao pode cair"},
    {"metrica": "editorial_aligned_ratio minimo em EP05", "hoje": 1.0, "direcao": "nao pode cair abaixo de alinhamento.editorial_ratio_minimo"},
    {"metrica": "achados do gauntlet em plano novo", "hoje": 0, "direcao": "nao pode subir"}
  ],
  "excecoes": [],
  "remoto": [
    {"dependencia": "GSAP", "versao": "3.14.2", "situacao": "vendorizado com PINS.json e coberto pelo hash da composicao; sem o arquivo local gen_comp volta a CDN e avisa"},
    {"dependencia": "Baloo 2, Nunito, Patrick Hand, Caveat", "versao": "fontsource 5.3.0, SIL OFL 1.1", "situacao": "woff2 vendorizadas com sha256 e fonts.css gerado dos pinos; sem os arquivos gen_comp volta ao Google Fonts e avisa"},
    {"dependencia": "Chromium do HyperFrames/Playwright", "versao": "revisao baixada na primeira execucao", "situacao": "nao coberto por hash; rode hyperframes doctor antes de confiar em reprodutibilidade"},
    {"dependencia": "registro do HyperFrames", "versao": "url raw do GitHub", "situacao": "consultado apenas se a composicao usar blocos do registro"}
  ]
}
```