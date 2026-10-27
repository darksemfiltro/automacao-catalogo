#!/usr/bin/env bash
# Instala tudo que o Catálogo precisa no Linux ou no macOS e confere o resultado.
#
# Cria o ambiente Python do projeto em .venv, instala as dependências Node
# (HyperFrames, versão fixada no package-lock.json), confere o ffmpeg e as
# dependências fixadas e gera uma composição de teste.
# Não instala pacotes no sistema e não usa sudo. Os caches do pip e do npm e o
# Chromium do HyperFrames ficam nas pastas de cache do seu usuário.
#
# Uso:
#   bash instalar.sh
#   bash instalar.sh --alinhamento     # torch CPU, torchaudio e uroman (~300 MB)
#   bash instalar.sh --transcricao     # faster-whisper
#   bash instalar.sh --pular python,verificacao   # etapas: python, node, verificacao
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
RAIZ="$(pwd)"
ALINHAMENTO=0
TRANSCRICAO=0
PULAR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --alinhamento) ALINHAMENTO=1 ;;
    --transcricao) TRANSCRICAO=1 ;;
    --pular)
      [ $# -ge 2 ] || { echo "--pular precisa de um valor (python, node ou verificacao)" >&2; exit 2; }
      PULAR="${PULAR} ${2//,/ }"; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

passo() { printf '\n== %s\n' "$1"; }
ok()    { printf '   ok  %s\n' "$1"; }
falha() { printf '   xx  %s\n' "$1" >&2; exit 1; }
pula()  { case " $PULAR " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

TESTE="$RAIZ/.instalacao-teste"
trap 'rm -rf "$TESTE"' EXIT

passo "Conferindo o que já existe no computador"

PYTHON=""
for candidato in python3 python; do
  if command -v "$candidato" >/dev/null 2>&1 &&
     "$candidato" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PYTHON="$candidato"; break
  fi
done
[ -n "$PYTHON" ] || falha "Python 3.10 ou superior não encontrado (instale python3 e python3-venv)."
ok "Python $("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"

command -v node >/dev/null 2>&1 || falha "Node.js 22 ou superior não encontrado: https://nodejs.org/"
NODE_MAJOR="$(node --version | sed -E 's/^v([0-9]+)\..*/\1/')"
[ "$NODE_MAJOR" -ge 22 ] || falha "Node.js $NODE_MAJOR encontrado; o projeto exige 22 ou superior."
ok "Node $(node --version)"

for programa in ffmpeg ffprobe; do
  command -v "$programa" >/dev/null 2>&1 || falha "$programa não encontrado. Instale o FFmpeg (apt install ffmpeg, brew install ffmpeg)."
done
ok "FFmpeg e FFprobe"

if pula python; then
  if [ -x .venv/bin/python ]; then PY="$RAIZ/.venv/bin/python"; else PY="$PYTHON"; fi
else
  passo "Ambiente Python do projeto (.venv)"
  [ -x .venv/bin/python ] || "$PYTHON" -m venv .venv || falha "Não consegui criar o .venv (no Debian/Ubuntu: apt install python3-venv)."
  PY="$RAIZ/.venv/bin/python"
  "$PY" -m pip install --quiet --upgrade pip || echo "   !!  não consegui atualizar o pip; sigo com a versão atual"
  "$PY" -m pip install --quiet -r requirements.txt || falha "pip falhou ao instalar requirements.txt"
  ok "numpy e soundfile"

  if [ "$ALINHAMENTO" = 1 ]; then
    passo "Alinhamento de palavras (torch CPU, torchaudio, uroman)"
    "$PY" -m pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu \
      || falha "Não consegui instalar torch e torchaudio"
    "$PY" -m pip install --quiet -r requirements-align.txt || falha "pip falhou ao instalar requirements-align.txt"
    ok "torch, torchaudio e uroman. Use --device cpu no align_mms.py."
  fi
  if [ "$TRANSCRICAO" = 1 ]; then
    passo "Transcrição (faster-whisper)"
    "$PY" -m pip install --quiet -r requirements-transcribe.txt || falha "pip falhou ao instalar requirements-transcribe.txt"
    ok "faster-whisper"
  fi
fi

if ! pula node; then
  passo "HyperFrames (npm ci)"
  npm ci --no-audit --no-fund || falha "npm ci falhou"
  ok "HyperFrames instalado na versão do package-lock.json"
fi

if ! pula verificacao; then
  passo "Conferindo o projeto"
  "$PY" pipeline/vendor.py | tail -n 1 || falha "Dependências fixadas divergem do hash. Rode: git checkout -- vendor"
  ok "GSAP e fontes conferidos por sha256"

  mkdir -p "$TESTE"
  cp episodios/EP05-tipos-de-tempestade/producao/episode.json "$TESTE/episode.json"
  "$PY" pipeline/gen_comp.py "$TESTE" --spec episode.json --theme cartoon | tail -n 1 || falha "gen_comp.py falhou"
  "$PY" pipeline/checa_densidade.py "$TESTE/hyperframes/index.html" | tail -n 1 || falha "A composição de teste tem buracos"
  npx --no-install hyperframes check "$TESTE/hyperframes" --at "5,25,45" --timeout 90000 \
    || falha "hyperframes check falhou. Rode: npx --no-install hyperframes doctor"
  ok "Composição de teste gerada e aprovada"
fi

cat <<'FIM'

Pronto.

Próximos passos:
  1. Use sempre o Python do projeto:  .venv/bin/python pipeline/...
     (ou ative com: source .venv/bin/activate  e escreva só: python pipeline/...)
  2. Escolha a voz da narração:  prompts/02-voz-local.md  ou  prompts/03-voz-api.md
  3. Veja o vídeo de exemplo:  demonstracao/
  4. Crie o seu episódio:  prompts/04-novo-episodio.md

Se algo falhar, cole a mensagem de erro em prompts/00-instalacao.md.
FIM
