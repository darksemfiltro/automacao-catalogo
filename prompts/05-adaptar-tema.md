# 05 · Ensinar um tema novo ao motor

O motor vem com 116 ilustrações vetoriais (`pipeline/ilustras.py`), 15 cenas em
tela cheia e 9 widgets de dados (`pipeline/mg.py`). Um tema novo pode pedir um
objeto ou uma cena que ainda não existe. Estes prompts pedem à IA que o crie,
com teste, sem quebrar o resto.

Para ver o que existe hoje:

```bash
python pipeline/ilustras.py --list
python pipeline/mg.py
```

## Prompt: criar uma ilustração nova

```text
Você está ajudando num projeto aberto chamado Catálogo. Leia AGENTS.md,
sistema/CONSTRAINTS.md, sistema/ESTILO-VISUAL.md e pipeline/ilustras.py (veja como
funcionam LIB, ALIASES, DARK e as funções como tornado, hurricane e lightning).

Preciso de uma ilustração vetorial chamada "[nome]" para [descrição: o que é, cores,
forma]. Ela aparece sobre fundo escuro, em estilo cartoon com contorno escuro, no mesmo
nível de detalhe das existentes.

Tarefa:
1. Crie a função [nome](size=None) em ilustras.py seguindo o padrão das vizinhas
   (viewBox 400x400, helper _svg ou _prop) e registre em LIB, com ALIASES em português
   e em inglês para as palavras que devem chamá-la na fala ("[palavra1]", "[palavra2]").
2. Se ela só aparece bem sobre fundo escuro, acrescente em DARK.
3. Registre a categoria em _cat, perto das outras do mesmo tema.
4. Renderize um PNG de teste (HTML com o SVG e a fonte Baloo 2 de vendor/fonts, captura
   com o Chromium do HyperFrames) e me mostre. Ajuste até ficar legível em 300 px.
5. Escreva um teste em pipeline/ que confirme: has("[nome]") é verdadeiro, render
   devolve SVG bem formado e os aliases resolvem.
6. Rode python -m unittest discover -s pipeline -p "test_*.py" e mostre o resultado.
Não altere o comportamento das outras ilustrações.
```

## Prompt: criar uma cena em tela cheia (fenômeno)

```text
Leia pipeline/mg.py (funções scene_vortex, scene_snowstorm e scene_seismic, o dicionário
RECIPES e _A, que descreve uma animação GSAP) e pipeline/build_cenas.py (mapas de
fenômeno por palavra, perto de "seismic" e "snowstorm"). Leia também
sistema/CENAS-NIVEL-1.md: a animação é uma timeline GSAP determinística, sem
aleatoriedade sem semente e sem timers.

Preciso de uma cena em tela cheia chamada "[nome]" que mostre [fenômeno, por exemplo:
um raio descendo de uma nuvem com clarão e trovão visual]. Ela explica a fala, tem
começo e fim e não cobre o capítulo inteiro.

Tarefa:
1. Crie scene_[nome](uid, p) em mg.py com o mesmo contrato das outras (devolva o dicionário
   que elas devolvem) e registre em RECIPES.
2. Ligue as palavras da fala ao fenômeno nos mapas de build_cenas.py, sem mudar o que já
   existe.
3. Faça um episódio mínimo de teste (2 ou 3 segmentos) que use a cena via cenas.json
   ({"tipo":"mg","id":"[nome]","modo":"full"}), gere a composição e rode gauntlet --strict,
   checa_densidade.py e "npx --no-install hyperframes check". Tire snapshots em 4 instantes
   e me mostre.
4. Escreva testes que não precisem de navegador (a receita está em RECIPES, devolve os
   campos esperados, não repete ids) e rode a suíte inteira.
Tudo que for novo precisa passar pela barra de sistema/CONSTRAINTS.md sem exceção.
```

## Prompt: criar um widget de dados novo

```text
Leia pipeline/mg.py (w_speed_gauge, w_thermometer, w_size_compare) e o catálogo de
cenas em sistema/CENAS-NIVEL-1.md. Quero um widget "[nome]" que mostre [dado: por
exemplo, uma pressão em hPa com escala de 900 a 1050]. A unidade aparece sempre ao lado
do número. Siga o contrato dos outros widgets (vb, mode "panel", inner, anims),
registre em RECIPES, use o widget numa cena de teste, tire um snapshot e escreva um
teste. Rode a suíte inteira no fim.
```

## Prompt: um tema inteiro de uma vez

```text
Quero produzir episódios sobre [TEMA], que o motor ainda cobre pouco. Leia
pipeline/ilustras.py e pipeline/mg.py e faça um relatório de vocabulário: para cada
conceito do roteiro episodios/EP[NN]-[tema]/roteiro.md, diga se já existe ilustração,
cena em tela cheia ou widget. Liste o que falta, ordenado pelo que aparece mais vezes,
e proponha o menor conjunto de ilustrações novas que cobre o episódio. Não crie nada
ainda: espere eu aprovar a lista.
```
