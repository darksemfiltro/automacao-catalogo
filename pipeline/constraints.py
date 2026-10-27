# -*- coding: utf-8 -*-
"""
constraints.py — carrega e valida a barra de qualidade do canal.

`sistema/CONSTRAINTS.md` é a fonte única dos limites. O código não repete
número: pede aqui. Passar o valor na mão é o caminho da exceção, e o
`floor_guard.py` acusa a flag.

Fora de contexto interativo (CI, agente autônomo) a ausência do arquivo não
impede o trabalho: aplica-se o Piso declarado no próprio módulo, que é o mesmo
texto do arquivo, e a ausência é reportada em vez de falhar em silêncio.

Uso:
  python pipeline/constraints.py            # valida e imprime a barra
  python pipeline/constraints.py --list     # tabela por chave
  python pipeline/constraints.py --json     # só o bloco canônico
  python pipeline/constraints.py --chave plano.max_gap_s
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "sistema" / "CONSTRAINTS.md"
FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)

SCHEMA_VERSION = 1

# Mesmo texto do bloco `piso` de CONSTRAINTS.md. Só é usado quando o arquivo
# não está disponível; um piso que o agente não consegue ler não é um piso.
FLOOR = (
    "Final somente por pipeline/render_final.py",
    "Nao inventar aprovacao humana",
    "Nao cortar silencio sem remontar e realinhar tempos derivados",
    "Nao copiar voz ou modelo para distribuicao",
    "Nao fixar caminho da maquina do mantenedor",
    "Sem segredo no codigo",
    "Sem TODO, stub que lanca ou except vazio no motor",
    "Editar as fontes, nunca o storyboard derivado",
)


class ConstraintError(ValueError):
    """A barra está ausente, ilegível ou incompleta. Nunca é relaxada em silêncio."""


def extract(text: str) -> dict:
    blocks = FENCE.findall(text)
    for block in blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "schema_version" in value:
            return value
    raise ConstraintError(
        f"{PATH.name} sem bloco json canonico com schema_version; a barra e o arquivo")


def validate(data: dict) -> dict:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ConstraintError(f"schema_version deve ser {SCHEMA_VERSION}")
    if not str(data.get("revisado_em", "")).strip():
        raise ConstraintError("revisado_em obrigatorio: uma barra sem data nao e revisada")
    date.fromisoformat(data["revisado_em"])

    piso = data.get("piso")
    if not isinstance(piso, list) or not piso or not all(isinstance(r, str) and r.strip() for r in piso):
        raise ConstraintError("piso deve ser lista nao vazia de regras textuais")
    for rule in piso:
        if rule not in FLOOR:
            raise ConstraintError(f"regra de piso nao reconhecida: {rule!r}")

    limites = data.get("limites")
    if not isinstance(limites, dict) or not limites:
        raise ConstraintError("limites deve ser objeto nao vazio")
    for chave, item in limites.items():
        if not re.fullmatch(r"[a-z0-9_]+(\.[a-z0-9_]+)+", chave):
            raise ConstraintError(f"chave de limite fora do formato dominio.nome: {chave!r}")
        if not isinstance(item, dict):
            raise ConstraintError(f"{chave}: limite deve ser objeto")
        valor = item.get("valor")
        if not isinstance(valor, (int, float, bool)) or isinstance(valor, str):
            raise ConstraintError(f"{chave}: valor deve ser numerico ou booleano")
        if isinstance(valor, float) and not math.isfinite(valor):
            raise ConstraintError(f"{chave}: valor nao finito")
        for campo in ("unidade", "motivo", "verificado_por", "roda_em"):
            if not str(item.get(campo, "")).strip():
                raise ConstraintError(f"{chave}: {campo} obrigatorio (limite sem comando e aspiracao)")

    for metric in data.get("medido", []):
        for campo in ("metrica", "hoje", "direcao"):
            if campo not in metric:
                raise ConstraintError(f"medido: {campo} obrigatorio em {metric!r}")

    seen = set()
    for exc in data.get("excecoes", []):
        for campo in ("id", "limite", "motivo", "responsavel", "expira"):
            if not str(exc.get(campo, "")).strip():
                raise ConstraintError(f"excecao: {campo} obrigatorio (sem responsavel ou sem prazo nao e excecao)")
        if exc["id"] in seen:
            raise ConstraintError(f"excecao duplicada: {exc['id']}")
        seen.add(exc["id"])
        if exc["limite"] not in limites:
            raise ConstraintError(f"excecao {exc['id']} aponta para limite inexistente: {exc['limite']}")
        date.fromisoformat(exc["expira"])

    for dep in data.get("remoto", []):
        for campo in ("dependencia", "versao", "situacao"):
            if not str(dep.get(campo, "")).strip():
                raise ConstraintError(f"remoto: {campo} obrigatorio")
    return data


def load(path: Path | str | None = None) -> dict:
    path = Path(path) if path else PATH
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "revisado_em": "", "piso": list(FLOOR),
                "limites": {}, "medido": [], "excecoes": [], "remoto": [],
                "_ausente": True}
    return validate(extract(path.read_text(encoding="utf-8")))


def value(chave: str, padrao=None, path: Path | str | None = None):
    """Limite da barra. `padrao` só entra se a chave não existir de fato."""
    data = load(path)
    limites = data.get("limites", {})
    if chave in limites:
        return limites[chave]["valor"]
    if padrao is None:
        raise ConstraintError(
            f"limite {chave!r} ausente em {PATH.name}; defina-o em sistema/CONSTRAINTS.md "
            f"em vez de repetir o numero no codigo")
    return padrao


def floor(path: Path | str | None = None) -> tuple:
    return tuple(load(path).get("piso") or FLOOR)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="tabela por chave")
    ap.add_argument("--json", action="store_true", help="somente o bloco canonico")
    ap.add_argument("--chave", help="valor de um limite especifico")
    a = ap.parse_args()
    try:
        data = load()
    except (ConstraintError, OSError, json.JSONDecodeError) as exc:
        print(f"FALHA: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if data.get("_ausente"):
        print(f"FALHA: {PATH} nao encontrado; a barra nao e opcional", file=sys.stderr)
        raise SystemExit(1)
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if a.chave:
        limites = data["limites"]
        if a.chave not in limites:
            print(f"FALHA: limite {a.chave!r} inexistente", file=sys.stderr)
            raise SystemExit(1)
        print(limites[a.chave]["valor"])
        return
    print(f"CONSTRAINTS.md revisado em {data['revisado_em']} | "
          f"{len(data['limites'])} limites | {len(data['piso'])} regras de piso | "
          f"{len(data['excecoes'])} excecao(oes)")
    if a.list:
        for chave, item in sorted(data["limites"].items()):
            print(f"  {chave:42s} {str(item['valor']):>7s} {item['unidade']:<9s} {item['roda_em']}")
    print("piso:")
    for regra in data["piso"]:
        print(f"  - {regra}")


if __name__ == "__main__":
    main()