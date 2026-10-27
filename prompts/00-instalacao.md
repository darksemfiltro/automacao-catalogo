# 00 · Instalação

Você tem dois caminhos. O principal é pedir para uma IA instalar tudo. O manual,
com script, fica mais abaixo para quem prefere fazer sozinho.

## Caminho principal: peça para a IA instalar

Você precisa de três coisas:

1. **Uma ferramenta de IA que lê a pasta e roda comandos no seu computador.**
   Exemplos: Claude Code, Codex, OpenCode, Cursor, Continue. O modelo pode ser da
   nuvem ou local (Ollama, LM Studio). Modelos pequenos erram mais: se travar, peça um
   passo de cada vez.
2. **O projeto baixado.** Na página do repositório, clique em **Code → Download ZIP** e
   extraia, ou use `git clone https://github.com/darksemfiltro/automacao-catalogo.git`.
3. **A pasta do projeto aberta na ferramenta de IA.**

Depois, cole o prompt do seu perfil. Os dois fazem a mesma instalação, mas conversam de
jeito diferente.

### Prompt para quem cria conteúdo (não programa)

Use se você é criador de vídeos e quer o resultado sem mexer em código. A IA explica em
linguagem simples, faz o trabalho técnico e pede o seu OK antes de instalar algo.

```text
Oi! Sou criador de conteúdo e NÃO programo. Quero instalar neste computador o projeto
Catálogo (vídeos explicativos em português). Você faz o trabalho técnico e eu só decido
e confirmo.

Como falar comigo: frases curtas e sem jargão. Quando usar um termo técnico, explique em
uma linha. Não me mostre código nem listas enormes de mensagens: resuma o que aconteceu.
Diga em que passo estamos ("passo 2 de 6").

O que fazer:
1. Leia README.md, instalar.ps1, instalar.sh e prompts/00-instalacao.md. Descubra o meu
   sistema (Windows, macOS ou Linux).
2. Veja o que eu já tenho instalado: Python 3.10 ou superior, Node.js 22 ou superior e
   FFmpeg. Liste o que falta e explique, em uma linha cada, para que serve e como instalar.
   Peça o meu OK antes de instalar qualquer programa.
3. Rode o instalador do meu sistema e acompanhe até o fim.
4. Se der erro, explique em uma frase o que houve, corrija da forma mais simples e tente de
   novo. Se não resolver em 3 tentativas, pare e me diga o que você precisa de mim.
5. Quando terminar, rode os testes e abra a composição do episódio de exemplo (EP05) para
   eu ver funcionando. Me diga como abrir e fechar.
6. Termine com um resumo de 5 linhas: o que ficou instalado e os 3 próximos passos para o
   meu primeiro vídeo (escolher a voz, escrever o roteiro, produzir). Pergunte qual voz eu
   quero: a minha própria voz clonada, uma voz gratuita no meu computador ou uma API.

Regras: instale só dentro da pasta do projeto, exceto os programas do passo 2, com o meu OK.
Não use administrador sem me avisar. Não apague nada. Não peça nem grave senhas ou chaves:
se algum serviço pedir uma chave, me ensine a colocar no arquivo .env (modelo em .env.example).
```

### Prompt para quem desenvolve

Use se você programa e quer controle: a IA fala direto, mostra comandos e decisões e
deixa o ambiente reproduzível.

```text
Instale o projeto Catálogo (pipeline Python + HyperFrames/Node para vídeos explicativos
em português) neste checkout. Seja direto: comandos, saídas relevantes e decisões, sem
tutorial.

1. Leia README.md, AGENTS.md, sistema/CONSTRAINTS.md, instalar.ps1, instalar.sh,
   requirements*.txt e package.json. Detecte SO, Python (>=3.10), Node (>=22), ffmpeg e
   ffprobe, e GPU (nvidia-smi).
2. Liste o que falta e peça confirmação antes de instalar qualquer coisa fora do repositório.
3. Rode instalar.ps1 (Windows) ou instalar.sh (Linux/macOS). Se eu usar GPU ou quiser
   alinhamento: --alinhamento / -Alinhamento (torch CPU; align_mms.py com --device cpu).
4. Valide: python -m unittest discover -s pipeline -p "test_*.py", python pipeline/verifica.py,
   npx --no-install hyperframes doctor. Mostre as contagens e qualquer aviso.
5. Gere a composição do EP05 sem áudio e rode gauntlet --strict, checa_densidade.py e
   hyperframes check.
6. Pergunte qual provedor de voz usar (omnivoice, openai ou comando) e prepare
   sistema/voz.local.json, sem tocar em sistema/voz.json. Chaves só em variável de ambiente
   ou no .env (modelo em .env.example).

Restrições: mudanças só no repositório (.venv, node_modules, caches) e nada de sudo sem
perguntar. Não afrouxe nenhum limite de CONSTRAINTS.md, não grave caminhos da máquina nem
segredos em arquivo versionado, e não apague arquivos. Se um passo falhar, diagnostique a
causa raiz antes de repetir. Ao final, liste o que instalou e onde, e o que ficou pendente.
```

### Depois de instalar

| Você quer | Próximo prompt |
| --- | --- |
| Escolher a voz | [02 · voz local](02-voz-local.md) ou [03 · voz por API](03-voz-api.md) |
| Fazer o seu primeiro vídeo | [04 · novo episódio](04-novo-episodio.md) |
| Entender o projeto antes | [01 · tour guiado](01-entender-o-projeto.md) |
| Ensinar objetos e cenas novos | [05 · adaptar tema](05-adaptar-tema.md) |

Em qualquer prompt, você pode abrir com o seu perfil. Veja
[Dois jeitos de falar com a IA](README.md#dois-jeitos-de-falar-com-a-ia).

## Caminho manual: com o script

Se você prefere rodar sozinho, use o script do seu sistema, na pasta do projeto.

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

Linux ou macOS:

```bash
bash instalar.sh
```

Antes, instale [Python 3.10+](https://www.python.org/downloads/),
[Node.js 22+](https://nodejs.org/) e o [FFmpeg](https://ffmpeg.org/download.html).

O script confere esses três programas, cria o ambiente `.venv`, roda `npm ci`, confere os
hashes das dependências e gera e valida uma composição de teste. Ele não instala pacotes
no sistema: o ambiente fica em `.venv` e `node_modules`. Os caches do pip e do npm e o
Chromium do HyperFrames ficam nas pastas de cache do seu usuário.

Opções:

| Opção (Windows / Linux e macOS) | O que faz |
| --- | --- |
| `-Alinhamento` / `--alinhamento` | Instala torch (CPU), torchaudio e uroman, para alinhar as palavras com a voz. Cerca de 300 MB. |
| `-Transcricao` / `--transcricao` | Instala o faster-whisper, para transcrever gravações suas. |
| `-Pular verificacao` / `--pular verificacao` | Não gera a composição de teste. |

## Prompt: instalar o alinhamento de palavras

```text
Leia README.md e requirements-align.txt. Preciso do alinhamento de palavras
(pipeline/align_mms.py) funcionando no meu computador, que [tem / não tem] placa de
vídeo NVIDIA.

Instale torch e torchaudio na versão certa para o meu caso dentro do .venv do projeto
(sem placa NVIDIA, use a versão CPU) e depois requirements-align.txt. Em seguida
rode o alinhamento num exemplo pequeno e confirme que o resultado não vem com 0%.
Se aparecer o erro "torchaudio::forced_align ... CUDA", rode de novo com --device cpu.
Não instale nada fora do .venv.
```

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| `python` não é reconhecido | Python fora do PATH | Reinstale marcando "Add to PATH" ou use `py` |
| `divergente: sha256` em `vendor/gsap.min.js` | O git converteu quebras de linha | `git checkout -- vendor` e confira `.gitattributes` |
| `hyperframes check` demora ou falha na primeira vez | Baixando o Chromium | Espere e rode `npx --no-install hyperframes doctor` |
| `Low memory` no doctor | Menos de 2 GB de RAM livre | Feche outros programas e renderize com `--workers 1` |
| Alinhamento termina com 0% | `forced_align` não existe em CUDA | Use `--device cpu` |

Outro erro? Use o [prompt 10](10-resolver-erros.md).
