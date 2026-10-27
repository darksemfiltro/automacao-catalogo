# 09 · Base para qualquer automação nova

O Catálogo é um pipeline de etapas pequenas: cada script lê arquivos de uma pasta
de episódio e grava outros. Isso o torna uma boa base para automações novas. Os
prompts 07 e 08 (Pexels e Pixabay) são exemplos do padrão.

## O padrão

| Peça | Regra |
| --- | --- |
| Entrada e saída | Arquivos na pasta do episódio. Nada de estado escondido. |
| Segredos | Chave de API só em variável de ambiente. Nunca em arquivo, log ou teste. |
| Rede | Isolada em uma função pequena, com tentativas só para erro temporário. Os testes usam um servidor simulado. |
| Origem | Todo arquivo de terceiros ganha registro de autor, link, licença e data. |
| Revisão | Quem decide é uma pessoa. A IA propõe, você revisa quadros e áudio. |
| Barra | `sistema/CONSTRAINTS.md` não se afrouxa. A automação passa nos mesmos gates. |
| Licença | Código e documentação derivados ficam gratuitos e sob a [licença do projeto](../LICENSE). |

## Onde plugar

| Você quer | Ponto de encaixe |
| --- | --- |
| Mudar o texto antes da voz | `pipeline/fonetica.py`, `pipeline/parse_roteiro.py` |
| Outra voz ou outro serviço de voz | `pipeline/tts.py` (prompts 02 e 03) |
| Mídia de apoio (vídeo, foto) | elementos `foto` e `video` em `pipeline/gen_comp.py` (prompts 07 e 08) |
| Cenas e objetos novos | `pipeline/ilustras.py`, `pipeline/mg.py` (prompt 05) |
| Trilha e efeitos sonoros | `assets/sfx` e `assets/music` do episódio, mixagem em `pipeline/assemble.py` |
| Legendas em movimento | uma etapa depois de `alignment_v1.json`, que tem o tempo de cada palavra |
| Thumbnails | HTML com as ilustrações de `ilustras.render()` e captura com o Chromium do HyperFrames |
| Título, descrição e capítulos | uma etapa depois de `episode.json`, que tem o início de cada capítulo |
| Várias plataformas (Shorts, Reels, TikTok) | outro `--theme` ou tamanho em `gen_comp.py`, com renders separados |

## Prompt: modelo para criar uma automação

```text
Você está ajudando num projeto aberto chamado Catálogo (vídeos explicativos em
português, com HyperFrames). Leia AGENTS.md, sistema/CONSTRAINTS.md,
sistema/FLUXO-NIVEL-1.md, prompts/09-outras-automacoes.md e um script do pipeline que
seja parecido com o que eu quero (por exemplo pipeline/build_tts_manifest.py).

Quero uma automação que [descreva em uma frase o que entra e o que sai].
Exemplo: "a partir de alignment_v1.json, gerar um arquivo de legendas palavra a palavra".

Tarefa:
1. Antes de codar, devolva um plano de 10 linhas: arquivo de entrada, arquivo de
   saída, em que ponto do fluxo entra, quais dependências usa (prefira a biblioteca
   padrão), se usa rede ou chave e quais riscos de licença existem.
2. Espere minha aprovação. Depois crie pipeline/[nome].py com uma função principal
   testável e uma linha de comando com --help em português, e pipeline/test_[nome].py.
3. Se usar um serviço externo: chave só por variável de ambiente, nenhum teste chama a
   rede, e os termos de uso do serviço são resumidos no cabeçalho do módulo.
4. Se baixar ou gerar arquivos de terceiros: registrar origem e licença, e acrescentar a
   pasta ao .gitignore.
5. Rode python -m unittest discover -s pipeline -p "test_*.py" e python pipeline/verifica.py.
   Mostre o resultado.
6. Documente em README.md (uma linha na tabela de scripts) e crie um prompt em prompts/
   para outras pessoas repetirem o uso.
Não afrouxe nenhum limite, não grave caminhos da minha máquina nem segredos.
```

## Ideias para começar

- Legendas em movimento no estilo do canal, a partir do tempo de cada palavra.
- Trilha sonora sob a narração, em −30 LUFS (a barra já tem esse alvo).
- Gerador de capítulos e descrição para o YouTube a partir do `episode.json`.
- Versão vertical do mesmo episódio para Shorts.
- Gerador de thumbnails com as ilustrações do episódio.
- Checagem de fatos: lista os números do roteiro e cobra a fonte de cada um.
