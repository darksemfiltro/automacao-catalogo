# 07 · Vídeos e fotos do Pexels

Ponto de partida para o motor buscar mídia de apoio no [Pexels](https://www.pexels.com/api/)
e usá-la nas cenas. O motor já sabe mostrar um arquivo: os elementos `foto` e
`video` de `pipeline/gen_comp.py` recebem `src`, posição e tamanho, `start`, `dur`
e, no vídeo, `media_start`. O que falta é buscar, baixar, registrar a origem e
inserir esses elementos no plano.

## O que fazer antes

1. Crie uma conta e peça a chave da API gratuita em https://www.pexels.com/api/.
2. Guarde a chave na variável de ambiente `PEXELS_API_KEY` (veja [prompts/README.md](README.md)).
3. Leia a licença e os termos da API do Pexels. Em geral: uso gratuito, sem exigir
   crédito, sem revender a mídia sem alteração e com limite de pedidos por hora e por
   mês. Confirme os termos atuais e anote o que valer.

## Desenho sugerido

```text
roteiro.md
   └─ palavras-chave por segmento (você ou a IA escolhe)
        └─ pipeline/midia_pexels.py   busca, baixa e registra
             ├─ producao/assets/midia/<id>.mp4 ou .jpg   (o git ignora)
             ├─ producao/assets/midia/CREDITS.json       autor, link, licença, data
             └─ producao/midia.json                       id do segmento → arquivo, recorte
                  └─ build_cenas.py / gen_comp.py → elementos "foto" e "video"
```

Regras que valem para qualquer fonte de mídia:

- A mídia fica na máquina de quem produz. Nunca vai para o repositório. Confira que
  `**/assets/midia/` está no `.gitignore`.
- Cada arquivo tem registro de origem: autor, link da página, licença, data do download.
- O vídeo entra mudo (`muted`) e sem texto de terceiros em cima de rostos.
- A cena precisa continuar passando em `gauntlet --strict`, `checa_densidade.py` e `hyperframes check`.

## Prompt: criar a busca e o download

```text
Você está ajudando num projeto aberto chamado Catálogo (vídeos explicativos em
português, com HyperFrames). Leia AGENTS.md, sistema/CONSTRAINTS.md, THIRD_PARTY.md,
sistema/CENAS-NIVEL-1.md, pipeline/gen_comp.py (veja como os elementos "foto" e
"video" são desenhados, perto de kind in ("foto", "video")) e pipeline/gauntlet.py.

Quero buscar vídeos e fotos no Pexels para ilustrar segmentos do roteiro. A chave está
na variável de ambiente PEXELS_API_KEY (não vou colar a chave aqui). Antes de escrever
código, leia a documentação atual da API em https://www.pexels.com/api/documentation/ e
me resuma: rotas de busca de fotos e de vídeos, parâmetros (query, orientation, size,
per_page), cabeçalho de autenticação, formato das respostas, limites de uso e o que a
licença permite e proíbe. Se algo não estiver claro, diga em vez de supor.

Tarefa:
1. Crie pipeline/midia_pexels.py com a biblioteca padrão (urllib), sem dependências novas:
   - buscar(consulta, tipo="video"|"foto", orientacao="landscape") → lista de candidatos
     com id, link da página, autor, link do autor, duração e as variantes de arquivo;
   - baixar(candidato, pasta): escolhe a variante de 1920 px ou a mais próxima, grava em
     producao/assets/midia/, recusa sobrescrever e respeita pausa entre pedidos;
   - registrar(candidato, arquivo): acrescenta ao CREDITS.json autor, link, licença
     ("Pexels License"), data e o termo de busca usado.
2. Uma linha de comando: python pipeline/midia_pexels.py <pasta-producao> --consulta
   "[termo]" --tipo video --quantos 3 --listar. Sem --baixar ela só lista; baixar exige
   --baixar e o número do candidato.
3. Tratar 401 (chave errada), 429 (limite) e rede fora do ar com mensagem em português que
   nunca inclua a chave.
4. Testes em pipeline/test_midia_pexels.py com um servidor HTTP simulado e respostas
   gravadas à mão. Nenhum teste chama a rede de verdade nem exige a chave.
5. Acrescente **/assets/midia/ ao .gitignore e rode a suíte inteira.
Não ligue ainda ao plano de cenas: pare aqui e me mostre o resultado.
```

## Prompt: ligar a mídia às cenas

```text
Leia pipeline/midia_pexels.py (já existe), pipeline/build_cenas.py e pipeline/gen_comp.py.
Quero que um segmento do roteiro use uma foto ou um vídeo baixado. O desenho é: um
arquivo producao/midia.json, escrito por mim ou pela busca, no formato
{"to02": {"arquivo": "assets/midia/12345.mp4", "tipo": "video", "inicio": 2.0,
"x": 960, "y": 120, "w": 880, "h": 520}}. Depois que build_cenas.py gera o
episode.json, um passo (pipeline/aplica_midia.py) lê o midia.json e acrescenta os
elementos "foto" ou "video" nos tempos do segmento, sem apagar nada do que existe.

Antes de escrever: confirme em gen_comp.py como o src é resolvido dentro da pasta
hyperframes (o arquivo precisa ser copiado para a composição?) e onde a duração do
vídeo é limitada. Garanta que o vídeo não passe do fim do segmento, que não cubra o
título do capítulo nem as legendas, e que o gauntlet --strict continue com 0 achados.
Escreva testes, rode a suíte e gere um quadro de exemplo com hyperframes snapshot.
```

## Prompt: escolher boas buscas

```text
Leia episodios/EP[NN]-[tema]/roteiro.md. Para cada segmento, proponha até 3 termos de
busca em inglês para o Pexels (a busca funciona melhor em inglês) que mostrem a ideia
sem texto na imagem e sem rosto identificável em primeiro plano. Marque os segmentos
em que uma ilustração do motor funciona melhor do que uma foto. Devolva uma tabela
(id, termos, motivo) e espere eu aprovar antes de baixar qualquer arquivo.
```
