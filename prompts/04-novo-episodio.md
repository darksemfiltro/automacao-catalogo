# 04 · Criar um episódio

O caminho completo, do tema ao MP4. O exemplo pronto é o
[EP05](../episodios/EP05-tipos-de-tempestade/), um vídeo de 58 segundos que você
vê em [demonstracao/](../demonstracao/).

```text
roteiro.md → segmentos → fonética → narração → tempos por palavra → cenas
          → storyboard → composição → revisão → render final
```

## Prompt 1: pesquisar e escrever o roteiro

```text
Você está ajudando a criar um episódio do formato "Todos os tipos de [TEMA]" para o
projeto aberto Catálogo. Leia BIBLIA-CANAL.md, sistema/ROTEIRO-SPEC-DRIVEN.md e
episodios/EP05-tipos-de-tempestade/roteiro.md (exemplo de formato).

Tema: [TEMA]. Duração: cerca de [60 segundos / 3 minutos]. Idioma: português do Brasil.

Tarefa:
1. Liste os [4 a 6] tipos que cabem no tema, com um critério claro de classificação.
   Se o tema admite mais tipos do que cabem, diga isso no roteiro ("quatro tipos") em
   vez de afirmar que a lista é completa.
2. Para cada tipo, pesquise em fonte primária (agência oficial, universidade, órgão
   técnico) pelo menos um número com unidade. Guarde para cada número a fonte e o link
   em episodios/EP[NN]-[tema]/producao/fontes.md, no formato de
   episodios/EP05-tipos-de-tempestade/producao/fontes.md. Se a fonte só trouxer uma
   regra prática, escreva "costuma" e não "só". Se só achar fonte secundária, marque.
3. Escreva roteiro.md no formato do exemplo: um "#" para o episódio, um "##" por
   capítulo e uma linha por frase, com id único e [gap:X]. O nome do tipo abre cada
   capítulo, como manchete. Frases de 10 a 15 palavras, voz ativa, números com unidade.
   O primeiro capítulo promete uma pergunta e o último a faz.
4. Revise o texto antes de me entregar: tire adjetivo vazio, advérbio, frase de efeito,
   travessão e qualquer afirmação sem fonte. Cada número falado precisa estar no
   fontes.md.
Não grave nada fora da pasta do episódio e não invente fonte ou dado.
```

## Prompt 2: produzir

```text
Leia AGENTS.md, sistema/CONSTRAINTS.md e sistema/FLUXO-NIVEL-1.md. Tenho o roteiro
em episodios/EP[NN]-[tema]/roteiro.md. Faça a produção passo a passo, parando e
me mostrando o resultado de cada etapa antes de seguir:

1. python pipeline/novo_episodio.py "[Título]" --id EP[NN]   (se a pasta ainda não existe)
2. parse_roteiro.py, fonetica.py e build_tts_manifest.py (use --sem-referencia se o
   meu provedor de voz não clona voz; veja prompts/02-voz-local.md e 03-voz-api.md).
3. python pipeline/tts.py <manifesto> --check e depois sem --check. Peça que eu ouça
   as primeiras frases antes de continuar.
4. measure_durations.py e assemble.py. O áudio precisa ficar em -16 LUFS, como diz a barra.
5. align_mms.py com --device cpu se não houver CUDA. O alinhamento precisa ficar em 100%.
   Abaixo disso, pare e me explique.
6. build_cenas.py. Se eu quiser controlar as cenas, edite producao/cenas.json (nunca o
   episode.json nem o storyboard), usando as ilustrações de "python pipeline/ilustras.py
   --list" e as receitas de pipeline/mg.py. Cada número falado ganha um painel com
   unidade. Cada capítulo tem pelo menos um objeto.
7. python pipeline/gauntlet.py <episode.json> --strict até chegar a 0 achados.
8. storyboard.py create, gen_comp.py, checa_densidade.py e hyperframes check.
9. hyperframes snapshot em 8 a 12 instantes e me mostre as imagens. Eu reviso.
10. Só depois da minha revisão: storyboard.py review com o meu nome e as minhas
    observações, e render_final.py. Não escreva aprovação em meu nome.

Regras: nunca afrouxe a barra, nunca renderize com a CLI direta (só render_final.py),
nunca sobrescreva WAVs sem me avisar e não grave caminhos da minha máquina em arquivo
versionado.
```

## Prompt 3: corrigir uma frase depois de pronto

```text
O episodio EP[NN] já foi produzido. Preciso trocar a frase [id] de "[texto antigo]"
para "[texto novo]". Mude só o roteiro.md, regenere apenas esse segmento (build_tts_manifest.py
com --only [id] e tts.py com --overwrite), refaça measure_durations, assemble, align_mms,
build_cenas, gauntlet, storyboard e a composição, e me avise que a revisão anterior
perdeu a validade. Os outros WAVs não podem mudar.
```

## Dicas

- Um episódio por pasta. `novo_episodio.py` recusa um id que já existe.
- Edite sempre as fontes (`roteiro.md`, `cenas.json`). O que é gerado pode ser apagado e refeito.
- Revisão registrada com `storyboard.py review` é uma revisão feita de verdade, por uma pessoa, com quadros.
