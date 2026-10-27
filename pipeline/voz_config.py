"""Configuração de voz: sistema/voz.json com sobreposição local opcional.

`sistema/voz.json` é público e vale para todo mundo. Quem precisa de um caminho
ou de um provedor só da própria máquina cria `sistema/voz.local.json`, que o git
ignora, e escreve só as chaves que quer trocar. Chaves aninhadas (`api`,
`comando`) são mescladas, não substituídas.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "sistema" / "voz.json"


def _merge(base, extra):
    out = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _read(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def carregar(path=CONFIG_PATH):
    """Lê voz.json e, só para o arquivo padrão, aplica voz.local.json por cima."""
    config = _read(path)
    if Path(path).resolve() == CONFIG_PATH.resolve():
        config = _merge(config, _read(CONFIG_PATH.with_name("voz.local.json")))
    return config


def carregar_env(path=None):
    """Lê o arquivo de variáveis da raiz (CHAVE=valor) sem sobrescrever o ambiente.

    Ele guarda chaves de API e caminhos locais. O git ignora o arquivo; o modelo
    para copiar é o `.env.example`. Variáveis já definidas no sistema vencem.
    Devolve os nomes das variáveis que carregou.
    """
    path = Path(path) if path else ROOT / ".env"
    if not path.is_file():
        return []
    carregadas = []
    for linha in path.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
        if chave and valor and chave not in os.environ:
            os.environ[chave] = valor
            carregadas.append(chave)
    return carregadas
