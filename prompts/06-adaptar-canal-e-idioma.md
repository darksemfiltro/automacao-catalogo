# 06 · Adaptar para o seu canal e para outro idioma

O projeto nasceu para o canal Dark Sem Filtro, mas o motor é seu. Os prompts
abaixo trocam identidade visual, tom e idioma sem quebrar a barra de qualidade.

## Prompt: criar a identidade do seu canal

```text
Você está ajudando a adaptar o projeto aberto Catálogo para o meu canal. Leia
BIBLIA-CANAL.md, sistema/ESTILO-VISUAL.md, canal.yaml e referencias/README.md.

Meu canal: [nome]. Público: [descrição]. Tema geral: [tema]. Tom: [direto, bem-humorado,
sério...]. Formato: [tipos de X, "como funciona", ranking...]. Duração: [60 s / 8 a 12 min].

Tarefa:
1. Reescreva BIBLIA-CANAL.md para o meu canal, mantendo as seções (posicionamento,
   formato, voz editorial, identidade visual, título e thumbnail, compliance, SEO).
   Troque o que é do Dark Sem Filtro por escolhas minhas, sem inventar dados sobre o
   meu público: use [a definir] onde faltar informação e me pergunte.
2. Proponha a paleta e as fontes. As cores do tema "cartoon" estão em
   pipeline/gen_comp.py e as das cenas em pipeline/mg.py (CYAN, AMBER...). Mostre uma
   tabela de "cor atual → cor proposta" e só mude depois da minha aprovação.
3. Se eu quiser outra fonte, ela precisa entrar em vendor/PINS.json com versão, origem e
   sha256, e o arquivo woff2 em vendor/fonts/ com a licença. Rode python pipeline/vendor.py.
4. Rode a suíte, gere a composição do EP05 com o tema novo e me mostre 4 quadros.
Não mude nenhum limite de sistema/CONSTRAINTS.md. Fonte e imagem de terceiros precisam
de licença que permita uso em vídeo gratuito.
```

## Prompt: outro idioma

```text
O projeto Catálogo narra em português do Brasil. Quero produzir em [inglês / espanhol / ...].
Leia README.md, sistema/FONETICA-PTBR.md, pipeline/fonetica.py, pipeline/align_mms.py,
pipeline/build_cenas.py e pipeline/tts.py.

Faça um levantamento, sem alterar nada ainda, de tudo que está preso ao português:
1. fonetica.py (números por extenso, siglas, unidades, abreviações);
2. o campo language do manifesto de voz e o que cada provedor aceita;
3. align_mms.py: o alinhador usa romanização e um modelo multilíngue; diga se funciona
   para o meu idioma e o que mudaria;
4. textos fixos em build_cenas.py, mg.py e gen_comp.py (rótulos, unidades como "km/h",
   legendas, separador decimal e de milhar);
5. o tema "doodle", que não traduz o roteiro sozinho.
Entregue uma lista de mudanças ordenada por esforço e me pergunte por onde começar. Depois
implemente em passos pequenos, com um teste por mudança, e produza um episódio curto de
teste no novo idioma. Não quebre o português: os testes atuais continuam passando.
```

## Prompt: duração maior (episódio de vários minutos)

```text
Leia sistema/CONSTRAINTS.md (limites de duração do episódio e do plano), AGENTS.md e
sistema/FLUXO-NIVEL-1.md. Quero um episódio de [10 a 15] minutos com [11 a 14] capítulos
no formato do BIBLIA-CANAL.md. Planeje o roteiro por capítulo (tipo, 2 a 4 fatos com número
e fonte, comparação com algo conhecido, consequência), estime as palavras (cerca de 165 por
minuto) e me mostre o plano antes de escrever. Na produção, gere e revise por capítulo,
para eu ouvir o áudio aos poucos.
```
