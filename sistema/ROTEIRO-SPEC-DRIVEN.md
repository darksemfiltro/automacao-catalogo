# Roteiro Spec-Driven — Catálogo

> A regra-mãe: **arquitetura fora, execução dentro.** O que o roteiro tem e em que ordem
> é decidido antes (pela spec); como cada frase é escrita é a IA. Trocar essa ordem
> produz template — e template é o que a política de conteúdo inautêntico caça.

## 1. A spec do episódio (antes de escrever)

Nenhum bloco é escrito antes desta spec. Campos:

```markdown
# SPEC — <título de trabalho>

## Identidade
- Episódio: EP0X — Todos os tipos de <X>
- Tese (1 frase falável): <a ideia central numa respiração>
- Ângulo: <o recorte que só este canal faria>
- Pergunta final (o gancho prometido no bloco 1): <...>

## Lista (o catálogo)
| # | Tipo | Nº de fatos | Número-âncora | Objeto na tela |
|---|---|---|---|---|
| 1 | ... | 3 | 75% | red_dwarf |

## Pesquisa (com fonte — nada entra sem isto)
- [P1] <afirmação factual> — fonte: <NASA/IBGE/artigo> — confiança: alta

## Cenário visual
- Tema: cartoon · Fundo: escuro, variável por cena
- Ilustração-âncora de cada capítulo: <id de ilustras.py>
```

## 2. Formato do roteiro (o contrato de texto)

- Um `##` por capítulo; o texto do heading vira uma cartela breve de entrada.
- Uma linha por segmento: `- \`id\` [gap:0.20] texto`.
- Cada capítulo: **nome primeiro**, depois 2–4 fatos **com número**, uma comparação e
  uma consequência. Frases de ~10–15 palavras.
- Gancho: o primeiro bloco promete a pergunta final; o último bloco a responde.
- CTA curto no meio, sem repetir a referência palavra por palavra.

## 3. A spec de cenas (o que garante a sincronia)

Para cada segmento, os elementos visuais **ancorados na palavra falada**:

```jsonc
{
  "av06": [
    { "tipo": "ilustra", "id": "hourglass", "pos": "esquerda" },
    { "tipo": "callout", "texto": "1 TRILHÃO DE ANOS", "palavra": "trilhão", "pos": "dir" }
  ]
}
```

Regras:
- **Uma âncora = uma palavra do roteiro.** Se a palavra não existe, o elemento não entra.
- **Nada de offset fixo.** O tempo vem do `alignment_vX.json`.
- **Ilustração cobre o segmento inteiro** e entra em corte seco (a tela nunca fica vazia).
- Dedup: dois segmentos seguidos não repetem o mesmo objeto.
- Autogeração: sem spec para um segmento, o motor deriva número→callout,
  enumeração→lista e palavra-chave→objeto. Escreva spec só para refinar.

## 4. Duração

Meta editorial **10–15 min** (em geral, 11–14 capítulos). `parse_roteiro.py` mostra
uma estimativa de tempo; a revisão editorial decide se o episódio atingiu a meta.
Se faltar, **adicione tipos ou
fatos**, nunca enrole.

## 5. Os sete erros que o sistema impede

1. Um prompt único gerando o roteiro inteiro.
2. Transcrição de outro canal reescrita com sinônimos.
3. A mesma estrutura em vídeos seguidos.
4. Nenhuma revisão, ou revisão feita por quem escreveu.
5. Todas as partes pensadas do mesmo jeito.
6. Roteiro escrito sem objetivo (atrair, reter ou converter).
7. IA fazendo 100% — inclusive a parte que era para ser sua (o toque humano).
