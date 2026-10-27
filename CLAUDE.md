# Instruções do projeto

Leia `sistema/CONSTRAINTS.md` antes de escrever código. A barra é uma, vive
nesse arquivo e não é afrouxada para fazer uma mudança passar.

Siga [AGENTS.md](AGENTS.md), o [catálogo de cenas](sistema/CENAS-NIVEL-1.md),
a [barra de qualidade](sistema/CONSTRAINTS.md) e o
[fluxo Nível 1](sistema/FLUXO-NIVEL-1.md). Essas são as mesmas regras para
Claude, Codex e outros agentes. A implementação deste projeto usa HyperFrames.

Catálogo explícito: objeto, detalhe, dados, dado em texto, fenômeno (nativos);
Talking Head, Split e PiP são receitas para adaptação com filmagem e não devem
ser anunciados como componentes prontos. Motion: fade, slide_in, cut_pop,
kenburns, drift e receitas semânticas em `mg.py`. Não adicionar movimento só
para preencher tempo. Cortes de silêncio exigem decisão editorial e realinhamento.

Nunca acione o render final sem storyboard atual, revisão registrada e gates.
