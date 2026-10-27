# 01 · Entender o projeto

Use para aprender como o sistema funciona antes de mexer, ou para tirar dúvidas.

```text
Você vai me ensinar o projeto Catálogo, um pipeline aberto que transforma um roteiro
em vídeo explicativo em português (narração, tempos por palavra, cenas vetoriais e
render com HyperFrames). Eu sou [iniciante / intermediário] e meu objetivo é
[criar vídeos para o meu canal / adaptar o sistema para outro tema / contribuir].

Leia, nesta ordem: README.md, AGENTS.md, sistema/CENAS-NIVEL-1.md,
sistema/FLUXO-NIVEL-1.md, sistema/CONSTRAINTS.md e demonstracao/README.md.
Depois olhe a pasta episodios/EP05-tipos-de-tempestade/.

Explique em português simples, em até 15 linhas cada:
1. O caminho completo, do roteiro.md até o MP4, uma etapa por linha, com o script de
   cada etapa e o arquivo que ela gera.
2. Quais etapas são automáticas e quais exigem a minha decisão ou revisão.
3. O que é cada arquivo de episodios/EP05-tipos-de-tempestade/ (roteiro.md,
   producao/cenas.json, producao/episode.json) e o que é gerado e não vai para o git.
4. O que é "a barra" (sistema/CONSTRAINTS.md) e por que não se afrouxa.
5. Quais partes eu consigo mudar sem programar (roteiro, cenas.json) e quais exigem
   código (ilustras.py, mg.py, build_cenas.py).

No fim, faça 3 perguntas curtas para checar se entendi e espere minhas respostas.
Não altere nenhum arquivo.
```

## Perguntas úteis depois do tour

```text
Quais cenas o motor sabe fazer hoje? Liste os tipos de cena, as receitas de
mg.py (cenas em tela cheia e widgets de dados) e as ilustrações de ilustras.py,
agrupadas por tema.
```

```text
Pegue o episodio EP05 e me mostre, segmento a segmento, qual cena o motor escolheu
(plano_cenas.json depois de rodar build_cenas.py --plan-only) e por quê.
```
