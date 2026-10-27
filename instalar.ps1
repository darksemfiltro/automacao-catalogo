<#
.SYNOPSIS
  Instala tudo que o Catálogo precisa no Windows e confere o resultado.

.DESCRIPTION
  Cria o ambiente Python do projeto em .venv, instala as dependências Node
  (HyperFrames, versão fixada no package-lock.json), confere o ffmpeg, as
  dependências fixadas e gera uma composição de teste.
  Não instala pacotes no sistema e não pede administrador. Os caches do pip e do npm e o
  Chromium do HyperFrames ficam nas pastas de cache do seu usuário.

.PARAMETER Alinhamento
  Instala também torch, torchaudio e uroman (versão CPU) para o alinhamento
  das palavras com o narrador (align_mms.py). Baixa cerca de 300 MB.

.PARAMETER Transcricao
  Instala também o faster-whisper, para transcrever gravações suas.

.PARAMETER Pular
  Lista de etapas a pular: python, node, verificacao.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\instalar.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\instalar.ps1 -Alinhamento
#>
param(
  [switch]$Alinhamento,
  [switch]$Transcricao,
  [string[]]$Pular = @()
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz

function Passo($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Ok($texto)    { Write-Host "   ok  $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "   !!  $texto" -ForegroundColor Yellow }
function Falha($texto) {
  Write-Host "   xx  $texto" -ForegroundColor Red
  if (Test-Path (Join-Path $raiz '.instalacao-teste')) { Remove-Item -Recurse -Force (Join-Path $raiz '.instalacao-teste') }
  exit 1
}

function Versao($comando, $argumentos) {
  try { return (& $comando @argumentos 2>&1 | Out-String).Trim() } catch { return $null }
}

Passo 'Conferindo o que já existe no computador'

$pythonExe = $null
foreach ($candidato in @('python', 'py')) {
  if (Get-Command $candidato -ErrorAction SilentlyContinue) {
    $saida = Versao $candidato @('-c', 'import sys;print(sys.version_info[0], sys.version_info[1])')
    if ($saida -match '^(\d+) (\d+)$' -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10))) {
      $pythonExe = $candidato; Ok "Python $($Matches[1]).$($Matches[2])"; break
    }
  }
}
if (-not $pythonExe) { Falha 'Python 3.10 ou superior não encontrado. Instale em https://www.python.org/downloads/ e marque "Add to PATH".' }

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Falha 'Node.js 22 ou superior não encontrado. Instale em https://nodejs.org/' }
$nodeMajor = [int]((node --version) -replace '^v(\d+)\..*', '$1')
if ($nodeMajor -lt 22) { Falha "Node.js $nodeMajor encontrado; o projeto exige 22 ou superior." }
Ok "Node $(node --version)"

foreach ($programa in @('ffmpeg', 'ffprobe')) {
  if (-not (Get-Command $programa -ErrorAction SilentlyContinue)) {
    Falha "$programa não encontrado no PATH. Instale o FFmpeg: https://ffmpeg.org/download.html (ou: winget install Gyan.FFmpeg)."
  }
}
Ok 'FFmpeg e FFprobe'

if ($Pular -notcontains 'python') {
  Passo 'Ambiente Python do projeto (.venv)'
  if (-not (Test-Path '.venv\Scripts\python.exe')) { & $pythonExe -m venv .venv; if ($LASTEXITCODE) { Falha 'Não consegui criar o .venv' } }
  $py = Join-Path $raiz '.venv\Scripts\python.exe'
  & $py -m pip install --quiet --upgrade pip
  & $py -m pip install --quiet -r requirements.txt
  if ($LASTEXITCODE) { Falha 'pip falhou ao instalar requirements.txt' }
  Ok 'numpy e soundfile'

  if ($Alinhamento) {
    Passo 'Alinhamento de palavras (torch CPU, torchaudio, uroman)'
    & $py -m pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE) { Falha 'Não consegui instalar torch e torchaudio' }
    & $py -m pip install --quiet -r requirements-align.txt
    if ($LASTEXITCODE) { Falha 'pip falhou ao instalar requirements-align.txt' }
    Ok 'torch, torchaudio e uroman. Use --device cpu no align_mms.py.'
  }
  if ($Transcricao) {
    Passo 'Transcrição (faster-whisper)'
    & $py -m pip install --quiet -r requirements-transcribe.txt
    if ($LASTEXITCODE) { Falha 'pip falhou ao instalar requirements-transcribe.txt' }
    Ok 'faster-whisper'
  }
} else {
  $py = if (Test-Path '.venv\Scripts\python.exe') { Join-Path $raiz '.venv\Scripts\python.exe' } else { $pythonExe }
}

if ($Pular -notcontains 'node') {
  Passo 'HyperFrames (npm ci)'
  npm ci --no-audit --no-fund
  if ($LASTEXITCODE) { Falha 'npm ci falhou' }
  Ok 'HyperFrames instalado na versão do package-lock.json'
}

if ($Pular -notcontains 'verificacao') {
  Passo 'Conferindo o projeto'
  & $py pipeline/vendor.py | Select-Object -Last 1
  if ($LASTEXITCODE) { Falha 'Dependências fixadas divergem do hash. Rode: git checkout -- vendor' }
  Ok 'GSAP e fontes conferidos por sha256'

  $teste = Join-Path $raiz '.instalacao-teste'
  New-Item -ItemType Directory -Force $teste | Out-Null
  Copy-Item 'episodios\EP05-tipos-de-tempestade\producao\episode.json' (Join-Path $teste 'episode.json') -Force
  & $py pipeline/gen_comp.py $teste --spec episode.json --theme cartoon | Select-Object -Last 1
  if ($LASTEXITCODE) { Falha 'gen_comp.py falhou' }
  & $py pipeline/checa_densidade.py (Join-Path $teste 'hyperframes\index.html') | Select-Object -Last 1
  if ($LASTEXITCODE) { Falha 'A composição de teste tem buracos' }
  npx --no-install hyperframes check (Join-Path $teste 'hyperframes') --at '5,25,45' --timeout 90000
  if ($LASTEXITCODE) { Falha 'hyperframes check falhou. Rode: npx --no-install hyperframes doctor' }
  Remove-Item -Recurse -Force $teste
  Ok 'Composição de teste gerada e aprovada'
}

Write-Host "`nPronto." -ForegroundColor Green
Write-Host @"

Próximos passos:
  1. Use sempre o Python do projeto:  .\.venv\Scripts\python.exe pipeline\...
     (ou ative com: .\.venv\Scripts\Activate.ps1  e escreva só: python pipeline\...)
  2. Escolha a voz da narração:  prompts\02-voz-local.md  ou  prompts\03-voz-api.md
  3. Veja o vídeo de exemplo:  demonstracao\
  4. Crie o seu episódio:  prompts\04-novo-episodio.md

Se algo falhar, cole a mensagem de erro em prompts\00-instalacao.md.
"@
