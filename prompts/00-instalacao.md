# 00 · Instalação

Use quando você acabou de baixar o repositório, ou quando a instalação deu erro.

## Primeiro tente o script

Windows (PowerShell, na pasta do projeto):

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

Linux ou macOS:

```bash
bash instalar.sh
```

O script confere Python 3.10+, Node 22+ e FFmpeg, cria o ambiente `.venv`, roda
`npm ci`, confere os hashes das dependências e gera e valida uma composição de
teste. Ele não instala pacotes no sistema: o ambiente fica em `.venv` e `node_modules`. Os caches do pip e do npm e o Chromium do HyperFrames ficam nas pastas de cache do seu usuário.

Opções:

| Opção (Windows / Linux e macOS) | O que faz |
| --- | --- |
| `-Alinhamento` / `--alinhamento` | Instala torch (CPU), torchaudio e uroman, para alinhar as palavras com a voz. Cerca de 300 MB. |
| `-Transcricao` / `--transcricao` | Instala o faster-whisper, para transcrever gravações suas. |
| `-Pular verificacao` / `--pular verificacao` | Não gera a composição de teste. |

## Prompt: instalar com ajuda da IA

```text
Você está ajudando a instalar um projeto aberto chamado Catálogo (pipeline de vídeos
explicativos em português com HyperFrames). Leia README.md, instalar.ps1, instalar.sh
e sistema/CONSTRAINTS.md antes de começar.

Meu sistema: [Windows 11 / Ubuntu 24.04 / macOS 15 ...].
O que já tenho instalado: [Python 3.x? Node? FFmpeg? Não sei].

Tarefa:
1. Confira o que falta (Python 3.10 ou superior, Node 22 ou superior, FFmpeg e FFprobe)
   e me diga como instalar cada item que faltar, com o comando certo para o meu sistema.
   Se for preciso instalar algo, peça minha confirmação antes.
2. Rode o script de instalação do meu sistema e acompanhe a saída.
3. Se algum passo falhar, explique o motivo em português simples, proponha a correção
   mais simples e só então tente de novo.
4. No fim, rode: python -m unittest discover -s pipeline -p "test_*.py"
   e mostre quantos testes passaram.
5. Termine me dizendo, em até 5 linhas, o que ficou instalado e o próximo passo.

Regras: instale só dentro da pasta do projeto (use o .venv), não use sudo nem
administrador sem me perguntar, não apague arquivos, não grave caminhos da minha
máquina nem chaves de API em nenhum arquivo do projeto.
```

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
