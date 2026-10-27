# 08 · Vídeos e imagens do Pixabay

Mesmo desenho do [prompt 07](07-fonte-pexels.md), para o
[Pixabay](https://pixabay.com/api/docs/). Leia o 07 primeiro: a estrutura de pastas,
o `CREDITS.json` e a ligação com as cenas são iguais. Aqui ficam só as diferenças.

## O que fazer antes

1. Crie uma conta e pegue a chave da API em https://pixabay.com/api/docs/.
2. Guarde a chave na variável de ambiente `PIXABAY_API_KEY` (veja [prompts/README.md](README.md)).
3. Leia a Licença de Conteúdo do Pixabay e os termos da API. Pontos que costumam
   pesar: o arquivo não pode ser distribuído sozinho e sem alteração, não pode ser
   revendido, e a API pede que você baixe e guarde o arquivo, sem ligar a imagem
   direto ao servidor deles. O projeto já tem uma nota sobre isso em
   [THIRD_PARTY.md](../THIRD_PARTY.md). Confirme os termos atuais antes de usar.

## Diferenças em relação ao Pexels

| Ponto | Pexels | Pixabay (confira na documentação) |
| --- | --- | --- |
| Autenticação | Cabeçalho `Authorization` | Parâmetro `key` na URL da busca |
| Rotas | Separadas para fotos e vídeos | Uma para imagens, outra para vídeos |
| Resposta de vídeo | Lista de arquivos por qualidade | Objeto com tamanhos (`large`, `medium`, `small`, `tiny`) |
| Limite | Por hora e por mês | Por janela de tempo curta |

Como a chave vai na URL, o código nunca deve imprimir a URL completa nem gravá-la em
log. Mostre só a consulta.

## Prompt: criar a busca e o download

```text
Você está ajudando num projeto aberto chamado Catálogo (vídeos explicativos em
português, com HyperFrames). Leia AGENTS.md, sistema/CONSTRAINTS.md, THIRD_PARTY.md,
sistema/CENAS-NIVEL-1.md, pipeline/gen_comp.py (elementos "foto" e "video") e, se já
existir, pipeline/midia_pexels.py, que serve de modelo.

Quero buscar vídeos e imagens no Pixabay. A chave está na variável de ambiente
PIXABAY_API_KEY (não vou colar a chave aqui). Antes de escrever código, leia a
documentação atual em https://pixabay.com/api/docs/ e a Licença de Conteúdo, e me
resuma: rotas de imagem e de vídeo, parâmetros (q, lang, image_type, video_type,
orientation, per_page, safesearch), formato das respostas, limites de uso, a regra sobre
guardar o arquivo em vez de ligar direto e o que a licença permite e proíbe. Se algo
não estiver claro, diga em vez de supor.

Tarefa:
1. Crie pipeline/midia_pixabay.py com a biblioteca padrão, com a mesma interface de
   linha de comando e o mesmo CREDITS.json do midia_pexels.py (licença "Pixabay Content
   License"). Se o Pexels ainda não existe, crie um módulo comum pipeline/midia_base.py
   com o que for igual (registro de origem, download sem sobrescrever, pausa entre
   pedidos) e use nos dois.
2. A chave vai na URL: nenhuma mensagem de erro, log ou teste pode imprimir a URL
   completa. Mostre só a consulta.
3. Baixe e guarde o arquivo em producao/assets/midia/. Nunca use a URL do Pixabay como
   src de uma cena.
4. Trate 400, 429 e rede fora do ar com mensagens em português.
5. Testes em pipeline/test_midia_pixabay.py com servidor HTTP simulado. Nenhum teste
   chama a rede de verdade nem exige a chave. Rode a suíte inteira.
Pare antes de ligar ao plano de cenas e me mostre o resultado.
```

## Prompt: um buscador só para as duas fontes

```text
Leia pipeline/midia_pexels.py e pipeline/midia_pixabay.py. Crie pipeline/midia.py, uma
interface única: python pipeline/midia.py <pasta-producao> --consulta "[termo]"
--fonte pexels|pixabay|todas --tipo video|foto --listar. Com "todas", junte os resultados
de cada fonte, mostre de onde veio cada um e, ao baixar, registre a licença correta no
CREDITS.json. Se uma chave não estiver definida, pule aquela fonte e avise, em vez de
falhar. Testes sem rede e suíte completa no fim.
```
