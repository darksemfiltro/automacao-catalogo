# Fluxo local de produção

Execute da raiz do clone. Nos exemplos, `P` significa a pasta
`episodios/EP06-meu-tema/producao`; substitua-a pelo caminho real, entre aspas
quando houver espaços. Python 3.10+ para o motor; para ML, prefira um ambiente
separado Python 3.10–3.13. O clone de demonstração não precisa de modelos.

## 1. Narração

A narração sai por `pipeline/tts.py`, que escolhe o provedor em `sistema/voz.json`
(campo `provedor`), na variável `CATALOGO_VOZ_PROVEDOR` ou em `--provedor`:

| Provedor | O que é | Guia |
| --- | --- | --- |
| `omnivoice` | Modelo local que clona uma voz de referência | esta seção |
| `comando` | Programa local chamado por segmento (Piper, por exemplo) | `prompts/02-voz-local.md` |
| `openai` | API compatível com OpenAI, na nuvem ou num servidor local | `prompts/03-voz-api.md` |

Prepare roteiro, segmentos e fonética conforme o README e gere o manifesto com
`build_tts_manifest.py`. Para o OmniVoice, use a sua referência vocal e a transcrição
dela. Para os outros provedores, use `--sem-referencia`.

```sh
python pipeline/tts.py P/tts_manifest_v1.json --check
python pipeline/tts.py P/tts_manifest_v1.json
```

O `--check` valida manifesto e configuração sem sintetizar. O comando recusa
sobrescrever WAVs: use `--retomar` para gerar só o que falta depois de uma falha, e
`--overwrite` para refazer tudo.

### OmniVoice

`pipeline/omnivoice_tts.py` é o executor do OmniVoice e `tts.py` o chama. Ele carrega o
modelo uma vez por lote, valida a transcrição da referência e confere os WAVs gerados.
Há dois modos, em `sistema/voz.json` (`modo`) ou em `CATALOGO_VOZ_MODO`:

- `direto` (padrão): executa no seu ambiente local do OmniVoice. Informe a pasta com
  `OMNIVOICE_HOME` ou `--home "CAMINHO/Omnivoice"`.
- `central`: usa um serviço de voz persistente que você mantém, indicado em
  `central_runner` (ou `CATALOGO_CENTRAL_RUNNER`). Quem não tem esse serviço usa `direto`.

Ajustes só da sua máquina, como o caminho do serviço, vão em `sistema/voz.local.json`,
que o git ignora. Nenhum valor local é gravado no código.

Para uma instalação nova, siga a [instalação oficial](https://github.com/k2-fsa/OmniVoice).
Instale PyTorch apropriado ao hardware e `omnivoice==0.2.1` num ambiente dedicado
(versão testada nesta integração). A primeira execução pode baixar pesos.
Sem `--home`, o script usa o worker portátil incluído aqui:

```sh
python pipeline/omnivoice_tts.py P/tts_manifest_v1.json --python "CAMINHO/venv/Scripts/python.exe"
```

Linux/macOS: use `CAMINHO/venv/bin/python`. O pacote oficial exige dependências
de ML adicionais; não misture esse ambiente com o Python mínimo do quickstart.
O código OmniVoice é Apache-2.0, mas o modelo padrão é **CC-BY-NC** conforme a
[ficha oficial](https://huggingface.co/k2-fsa/OmniVoice). Para canais comerciais,
escolha um modelo/provedor com licença adequada. Este projeto aceita WAVs de
outros provedores; a referência vocal não é distribuída.

## 2. Palavras: alinhar ou transcrever

Para narração com roteiro conhecido, mantenha `measure_durations → assemble →
align_mms`. Isso produz `alignment_v1.json` compatível com `build_cenas.py`.

Para gravação sem texto conhecido, use ASR local:

```sh
python -m pip install -r requirements-transcribe.txt
python pipeline/transcrever.py P/entrada/video.mp4 --out P/analise/palavras.json --model small --language pt
```

CPU/int8 é o padrão. `--device cuda` ativa GPU quando compatível. Após baixar o
modelo uma vez, `--offline` proíbe downloads. A saída tem `words[].w`, `t`,
`t_end`, `probability`, em segundos da fonte. Revise nomes, números e unidades.
Esse ASR não é alinhamento forçado e não se passa diretamente como `--align`
do motor faceless: uma filmagem exige segmentação editorial e adaptação da
composição, conforme o catálogo. Não fabricar timestamps de palavras ausentes.

## 3. Quadros de filmagem (opcional)

```sh
python pipeline/analisar_video.py P/entrada/video.mp4 --out P/analise/tomada01 --interval 5
```

Exige FFmpeg/FFprobe. O destino deve ser novo. Abre-se `index.html` para ver a
folha de quadros; `analysis.json` traz tempos, dimensões e pausas candidatas.
Sem filmagem, este passo não se aplica. Não existe recorte facial automático.
Quadros reais orientam decisões; a política segura é conter a filmagem inteira.

## 4. Referências e storyboard

`novo_episodio.py` cria `entrada/`, `analise/`, `referencias/`, `assets/`,
`revisoes/` e `renders/`. Acrescente imagens e observações ao manifesto de
referências; veja [o contrato](../referencias/README.md). Não publique prints
de terceiros apenas porque foram úteis para análise.

```sh
python pipeline/build_cenas.py P --plan-only
python pipeline/build_cenas.py P
python pipeline/gauntlet.py P/episode.json --strict
python pipeline/critica.py P brief
python pipeline/critica.py P review --critic "Quem leu em contexto fresco" \
  --notas "Descreva o que foi conferido" --achados "Problemas encontrados" --verdict go
python pipeline/storyboard.py create P
python pipeline/gen_comp.py P
npx --no-install hyperframes check P/hyperframes --timeout 30000
npx --no-install hyperframes snapshot P/hyperframes --at "5,15,25" --no-end --output P/revisoes/quadros-v1
```

Use tempos que existam no seu episódio e cubram os tipos de cena. `storyboard.html`
mostra o plano completo, `storyboard.json` guarda tempos e hashes, e
`hyperframes/build.json` identifica a composição gerada. O roteiro e os áudios
precisam estar corretos antes da revisão. Se o gauntlet falhar, corrija a fonte
ou use seu `--fix`, confira o resultado e regenere os derivados.

O `gauntlet` reprova regras mecânicas; ele não julga direção. Por isso a etapa
`critica.py`: alguém relê `plano_cenas.json` e o contrato em contexto fresco, com
prompt adversarial, e registra achados. O registro carrega `human_approval: false`
e não substitui a revisão do passo seguinte. Editar o plano ou o contrato depois
disso invalida a crítica.

Os limites dos gates não vão na linha de comando: vivem em
[CONSTRAINTS.md](CONSTRAINTS.md) e são lidos pelos scripts. Passar `--max-gap` ou
`--max` na mão é caminho de exceção, e `pipeline/floor_guard.py` acusa a flag no
diff.

## 5. Revisão e render final

Assista ao preview, ouça o áudio e confira os quadros. Depois de uma revisão
real, registre quem revisou, observações concretas e os arquivos usados:

```sh
python pipeline/storyboard.py review P --reviewed-by "Nome do revisor" --notes "Descreva os trechos conferidos, áudio, legibilidade e ressalvas" --frames P/revisoes/quadros-v1/ARQUIVO_REAL.png
python pipeline/render_final.py P --validate-only
python pipeline/render_final.py P --output final-v1.mp4
```

Substitua `ARQUIVO_REAL.png` pelo nome produzido pelo snapshot. `--frames` aceita
vários arquivos, todos dentro da pasta de produção. O registro é uma declaração
de revisão; não é assinatura digital nem prova automática de inspeção humana.

O render final narrado rejeita ausência de narração, plano incompleto, revisão ausente, composição parcial
(`--seconds`), alterações posteriores nos insumos/composição/quadros e saída
MP4 já existente. Executa gauntlet estrito, densidade e HyperFrames check antes
de renderizar. Mudanças exigem regeneração e nova revisão.
Depois do render, FFprobe verifica presença de vídeo e duração em relação ao plano.

A CLI direta do HyperFrames permanece disponível para demos/previews e pode
contornar esses gates. Portanto, somente o wrapper representa o fluxo final
suportado, e o plugin `.opencode/plugin/render-gate.js` recusa o
`hyperframes render` direto para que a exceção seja visível. Os hashes cobrem
arquivos locais, e as dependências do render estão todas neles: GSAP e as woff2
das fontes estão em `vendor/`, fixadas por versão e sha256 em `vendor/PINS.json`.
Restam remotos o navegador do HyperFrames e o registro, ambos declarados em
[CONSTRAINTS.md](CONSTRAINTS.md). A revisão automática não substitui conferir o
episódio inteiro.
