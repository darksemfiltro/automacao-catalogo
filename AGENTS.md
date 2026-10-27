# Produção e manutenção

Leia `sistema/CONSTRAINTS.md`, `sistema/CENAS-NIVEL-1.md`,
`sistema/FLUXO-NIVEL-1.md` e a documentação do canal antes de alterar produção.
Este motor é HyperFrames/GSAP; não migrar para Remotion apenas porque uma
referência o usa. O formato padrão é faceless.

- Execute ferramentas da raiz. Nunca fixe caminhos da máquina do mantenedor.
- Preserve alterações preexistentes, mídia fonte e vozes. Use diretórios por episódio.
- Narração por `pipeline/tts.py`: provedor `omnivoice`, `openai` (API compatível) ou `comando` (programa local), escolhido em `sistema/voz.json`. Ajustes só da sua máquina vão em `sistema/voz.local.json`, que o git ignora. Nunca copie vozes ou modelos para distribuição.
- Tempos da narração conhecida vêm de MMS; ASR de gravações vem de Faster-Whisper.
  Não trate confiança do ASR como prova de fidelidade ao roteiro.
- Examine referências reais e converta observações no contrato de tokens/cenas.
- Planeje antes do render: build_cenas → gauntlet → storyboard → composição →
  quadros/áudio → registro de revisão → render_final. Após correções, repita o necessário.
- Não invente aprovação humana. `storyboard.py review` é um registro de revisão
  efetivamente realizada, com responsável, observações e quadros usados.
- Final somente por `pipeline/render_final.py`. CLI direta é para preview/demo;
  ela contorna os gates do projeto e não constitui final validado. O plugin
  `.opencode/plugin/render-gate.js` recusa o `hyperframes render` direto; check,
  snapshot, preview e doctor continuam liberados.
- Silêncios detectados são candidatos; preserve pausas expressivas e o original.
  Não cortar sem remontar e realinhar todos os tempos derivados.
- Rostos: amostras não garantem rastreamento; enquadramento integral (`contain`),
  sem overlays sobre o vídeo, até existir revisão completa da região protegida.
- Execute `python -m unittest discover -s pipeline -p "test_*.py" -v`.
  Mídia e modelos não são necessários para a suíte; testes reais ficam separados.

## A barra

`sistema/CONSTRAINTS.md` é a fonte única dos limites. Leia antes de escrever
código, pegue os números de lá em vez de repetir literais e **não a afrouxe
para fazer uma mudança passar**: um limite só cede com exceção datada e
responsável. `pipeline/floor_guard.py` vigia o diff para que essa decisão
apareça no review em vez de passar em silêncio.

## Racionalizações comuns

| Discurso | Realidade |
|----------|-----------|
| "Já vi esse limite, 0,9 s é conservador demais aqui" | O limite é um número escolhido e revisado. Passar `--max-gap` na mão é caminho de exceção, e o guard acusa a flag. |
| "O teste está instável, pulo" | Sem o motivo escrito no commit, é a barra caindo. `TESTE_PULADO` é achado, não detalle. |
| "Vou encapsular a falha para o gate seguir" | `except: pass` em cima de um gate é como o gate deixa de existir. `VERIFICADOR_CALADO` é achado. |
| "O CLI já renderiza, o python é burocracia" | O CLI não revalida hashes nem confere a duração do MP4. `render_final.py` é a barreira; o resto é conveniência. |
| "A revisão está no storyboard, basta" | Storyboard é plano. A revisão é alguém olhando quadros com nome e observação. `critica.json` é direção, e também não aprova nada. |
| "É só um número, ajusto depois" | Números soltos no código viram documentação mentirosa: a skill já anunciava 2,8 s onde o motor usava 0,9 s. |
