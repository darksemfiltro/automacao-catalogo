# Direção visual do Catálogo

O motor está em `pipeline/build_cenas.py`, `gen_comp.py`, `ilustras.py` e `mg.py`.

## Planejar antes de gerar

1. Roteiro, tempos medidos e escolhas autorais entram em `plan_scenes`.
2. O motor salva `plano_cenas.json`: tipo, fundo, entrada, duração, motivo e receita.
3. Só depois `build_elements` monta objetos e dados alinhados à fala.
4. `gen_comp` executa o plano; não sorteia estilos durante o render.

## Gramática visual

- Capítulo é tema. Seu título entra por até 2,4 s.
- Fundos continuam escuros, mas pertencem a cada cena: azul, petróleo, ameixa ou preto.
- Nenhum diagrama, grade ou campo de estrelas deve cobrir automaticamente o episódio.
- Alternar objeto contextual e detalhe; dados alternam painel e número com unidade.
- Fenômenos são tomadas dedicadas. Não reiniciar a mesma receita a cada corte.
- Ações como destruir, inundar e girar devem ser específicas à fala.
- Entradas variam entre fade, deslocamento e assentamento, conforme o plano.
- Não empilhar flutuação, zoom e brilho sobre todos os objetos e painéis.
- O conteúdo definido em `cenas.json` orienta o assunto e as âncoras; não obriga fundo fixo.
- Objetos e números entram nas palavras alinhadas; não criar números para preencher gráficos.
- Manter as unidades: km/h, K, graus, %, hectares, km, anos etc.
- Frases curtas, sem sopa de palavras. Texto não deve esconder o objeto.
- Movimento interno das receitas é suficiente; não adicionar sweep de rotina.

## Aparência

Tema `cartoon`: texto azul com contorno escuro, fontes Baloo 2 e Nunito;
ilustrações vetoriais saturadas com contorno. `doodle` é uma alternativa tipográfica,
também sobre fundo escuro. Nunca usar tela branca.

## Revisão

Rode os testes de `pipeline`, o gauntlet estrito, a densidade e o HyperFrames check.
Inspecione quadros de tipos diferentes e escute a sincronia antes de publicar.
Uma composição regenerada não atualiza MP4s já exportados: guarde-os como revisões
anteriores e renderize a versão revisada quando aprovada.
