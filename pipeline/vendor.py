# -*- coding: utf-8 -*-
"""
vendor.py — dependências externas fixadas por versão e hash.

Os hashes do `workflow.fingerprint` cobrem arquivos locais; uma dependência
buscada por CDN não é coberta por nenhum deles. Resultado: dois renders do
mesmo `episode.json` podiam divergir porque o CDN mudou, e o primeiro render
exigia internet. Vendorizar o arquivo resolve as duas coisas — a cópia local
entra em `assets/vendor/` e passa a ser contada em `build.json`.

A versão e o sha256 ficam em `vendor/PINS.json`. Divergência é erro: quem
atualiza a dependência atualiza o pin no mesmo passo, com a versão nova
visível no diff.

Uso:
  python pipeline/vendor.py            # confere hash e versão
  python pipeline/vendor.py --install <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "vendor" / "PINS.json"
DEST = "assets/vendor"
FONTE_DEST = f"{DEST}/fonts"
CSS_DEST = f"{DEST}/fonts.css"
CDN = "https://cdn.jsdelivr.net/npm/gsap@{versao}/dist/{arquivo}"


def digest(path) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def pins() -> dict:
    if not PINS.is_file():
        raise FileNotFoundError(f"{PINS} ausente: as dependencias fixadas nao sao opcionais")
    data = json.loads(PINS.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Versão de PINS.json desconhecida")
    return data


def _local(entrada: dict, arquivo: str) -> Path:
    return ROOT / "vendor" / entrada.get("pasta", "") / arquivo


def available() -> bool:
    return PINS.is_file()


def pin(arquivo: str, grupo: str = "arquivos") -> dict:
    entrada = pins().get(grupo, {}).get(arquivo)
    if not entrada:
        raise KeyError(f"{arquivo} não está fixado em vendor/PINS.json")
    for campo in ("versao", "sha256", "origem", "licenca"):
        if not str(entrada.get(campo, "")).strip():
            raise ValueError(f"{arquivo}: {campo} obrigatório no pin")
    return entrada


def source(arquivo: str, grupo: str = "arquivos") -> tuple[Path, dict]:
    """Caminho local válido + pin. Recusa conteúdo que não bate com o hash."""
    entrada = pin(arquivo, grupo)
    path = _local(entrada, arquivo)
    if not path.is_file():
        raise FileNotFoundError(f"vendor/{entrada.get('pasta', '')}/{arquivo} ausente; "
                                f"baixe da origem {entrada['origem']}")
    actual = digest(path)
    if actual != entrada["sha256"]:
        raise ValueError(f"vendor/{arquivo} divergente: sha256 {actual} != pin {entrada['sha256']}")
    return path, entrada


def script_tag(arquivo: str) -> str:
    """URL da dependência. Local quando há pin válido; CDN declarada caso contrário."""
    try:
        source(arquivo)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        entry = None
        try:
            entry = pin(arquivo)
        except (KeyError, ValueError, FileNotFoundError):
            pass
        if entry is None:
            raise
        url = CDN.format(versao=entry["versao"], arquivo=arquivo)
        print(f"AVISO: {exc}; usando CDN {url} (render passa a depender de rede)", file=sys.stderr)
        return url
    return f"{DEST}/{arquivo}"


def install(dest, arquivo: str, grupo: str = "arquivos") -> str:
    path, entrada = source(arquivo, grupo)
    prefixo = f"{DEST}/{entrada['pasta']}" if entrada.get("pasta") else DEST
    target = Path(dest) / prefixo / arquivo
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return f"{prefixo}/{arquivo}"


def tem_fontes() -> bool:
    return bool(pins().get("fontes"))


def css_fontes() -> str:
    """@font-face local a partir dos pinos. Sem CDN e sem acesso à rede."""
    faces = []
    for arquivo, entrada in sorted(pins().get("fontes", {}).items()):
        faces.append(
            "@font-face{"
            f"font-family:'{entrada['familia']}';"
            f"font-style:{entrada.get('estilo', 'normal')};"
            f"font-weight:{entrada['peso']};"
            "font-display:block;"
            f"src:url('fonts/{arquivo}') format('woff2')"
            "}")
    return "\n".join(faces)


def install_fontes(dest) -> str:
    """Copia as woff2 e escreve o CSS na composição. Devolve o caminho do CSS."""
    css = css_fontes()
    if not css:
        raise ValueError("vendor/PINS.json sem fontes")
    base = Path(dest) / DEST
    (base / "fonts").mkdir(parents=True, exist_ok=True)
    for arquivo in sorted(pins()["fontes"]):
        install(dest, arquivo, "fontes")
    (base / "fonts.css").write_text(
        "/* Fontes locais: vendor/PINS.json fixa versao e sha256. Sem esta rede. */\n" + css + "\n",
        encoding="utf-8")
    return CSS_DEST


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", metavar="DIR", help="composição que recebe assets/vendor/")
    ap.add_argument("--html", action="store_true", help="mostra o que entraria no index.html")
    a = ap.parse_args()
    data = pins()
    falhas = 0
    for grupo in ("arquivos", "fontes"):
        for arquivo in sorted(data.get(grupo, {})):
            try:
                path, entry = source(arquivo, grupo)
                pasta = f"{entry['pasta']}/" if entry.get("pasta") else ""
                print(f"ok  vendor/{pasta}{arquivo} {entry['versao']} "
                      f"sha256 conferido ({path.stat().st_size} bytes)")
            except (FileNotFoundError, ValueError) as exc:
                print(f"FALHA {arquivo}: {exc}", file=sys.stderr)
                falhas += 1
    if falhas:
        raise SystemExit(1)
    if a.install:
        for arquivo in sorted(data.get("arquivos", {})):
            print("copiado:", install(a.install, arquivo))
        if data.get("fontes"):
            print("copiado:", install_fontes(a.install), f"({len(data['fontes'])} fontes)")
    if a.html:
        for arquivo in sorted(data.get("arquivos", {})):
            print(f"{arquivo} -> {script_tag(arquivo)}")
        print(f"fontes -> {CSS_DEST} ({len(data.get('fontes', {}))} familias/pesos)")


if __name__ == "__main__":
    main()