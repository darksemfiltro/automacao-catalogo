# Catálogo de cenas e decisões de montagem

O Nível 1 significa execução local sem serviço pago obrigatório. Não significa
garantia de qualidade automática, licença universal de modelos ou ausência de
custo de hardware. Este repositório mantém **HyperFrames + GSAP**, não Remotion.

## Cenas implementadas

| Tipo no plano | Uso | Implementação |
| --- | --- | --- |
| `objeto` | Mostrar aquilo de que se fala | SVG contextual de `ilustras.py` |
| `detalhe` | Aproximar um objeto vetorial | Objeto com movimento `kenburns` |
| `dados` | Valor e unidade | Widgets em `mg.py`, gráficos, barras, medidores |
| `dado_texto` | Destacar um dado sem painel | Callout grande com unidade |
| `fenomeno` | Explicar uma transformação | Receita contextual em tomada dedicada |

`build_cenas.py` escolhe tipos para o episódio inteiro antes de montar os elementos.
`episode.json.scene_plan` é a fonte do storyboard; `cenas.json` guarda intervenções
autorais. Edite as fontes e regenere, em vez de editar o storyboard derivado.

## Receitas com apresentador — extensão, não componentes prontos

| Receita | Composição pretendida | Região protegida |
| --- | --- | --- |
| Talking Head | Filmagem ocupa a tela | Vídeo completo, `object-fit:contain` |
| Split | Filmagem numa coluna; evidência na outra | Toda a coluna da filmagem |
| PiP | Apresentador num card separado do conteúdo | Todo o card, sem texto por cima |

O motor original possui elementos `foto`/`video` para mídia de apoio, mas não
possui diretor de apresentador, rastreamento temporal, áudio original sincronizado
em todos esses layouts ou edição automática de filmagens. Não coloque `split`,
`pip` ou `talking_head` em `scene_plan`: o validador recusa tipos não implementados.
Essas receitas orientam uma futura extensão sem prometer funcionalidade inexistente.

`analisar_video.py` entrega quadros com timestamps e candidatos a silêncio para
essa análise. A política padrão preserva todo o enquadramento e não permite overlay
na área do vídeo. Detectar um rosto em alguns frames não protege corpo/mãos nem
movimentos entre amostras. Crop requer revisão do trecho completo e implementação
da composição correspondente.

## Motion design disponível

- Entradas: `fade`, `slide_in`, `cut_pop`, escolhidas no plano.
- Movimento de objetos: `drift`, `kenburns`; restringir zoom aos objetos vetoriais.
- Semântica: receitas de `mg.py` e efeitos de `ilustras.py`; um fenômeno deve
  explicar a fala e ter início/fim. Consulte os scripts antes de inventar nomes.
- Dados: contadores, barras e escalas sempre com unidade.
- Timeline GSAP determinística; não usar timers independentes ou aleatoriedade
  sem semente. A documentação do Studio usa equivalentes React/Remotion, mas
  importar esses componentes diretamente não funciona neste motor.

## Pausas e cortes

Para TTS, ajuste `[gap:X]` no roteiro (pausa antes da frase), meça, monte e alinhe
novamente. `gap_after=0` no manifesto evita somar duas pausas. Não remova silêncio
da narração montada depois de calcular os tempos.

Para filmagem, `silencedetect` usa −35 dB por pelo menos 0,6 s e só **sugere**
trechos. Respiração, pontuação e silêncio dramático podem ser intencionais.
Este estágio não corta o arquivo e não gera EDL executável. Se uma extensão
aplicar cortes, precisa salvar intervalos fonte/destino e recalcular palavras,
legendas, overlays e duração. O Studio consultado segue `locked-final-cut`:
ele também não autoriza deduzir “cortar silêncios automaticamente”.
