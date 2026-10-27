# -*- coding: utf-8 -*-
"""
floor_guard.py — vigia o diff para que afrouxar a barra seja barulhento.

Um gate que ninguém desligou ainda é só uma porta. O risco real é o oposto: o
limite baixo, o teste pulado, o `except` que engole a falha, o stub no lugar da
implementação. Este script lê o diff e accuses cinco movimentos:

  1. LIMITE_ALTERADO      o número em `sistema/CONSTRAINTS.md` mudou
  2. LIMITE_NA_MAO        alguém passou `--max-gap`/`--max` na linha de comando
  3. TESTE_PULADO         teste pulado, apagado ou marcado como esperado falhar
  4. VERIFICADOR_CALADO   exceção engolida, `check=False` em gate, `sys.exit(0)`
  5. TRABALHO_INACABADO   TODO, stub ou `NotImplementedError` no motor

Aferição em relação a `CONSTRAINTS.md`: o diff é a evidência, o arquivo é a
barra. Ele não julga intenção — julga que a mudança é visível.

Códigos de saída: 0 nada a relatar · 1 achado(s) · 2 erro de uso/ambiente.

Uso:
  python pipeline/floor_guard.py                      # compara com HEAD
  python pipeline/floor_guard.py --base origin/main   # em CI
  python pipeline/floor_guard.py --staged             # só o index
  python pipeline/floor_guard.py --stdin < diff.txt   # fora do git
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

from constraints import PATH as CONSTRAINTS_PATH

CATEGORIAS = ("LIMITE_ALTERADO", "LIMITE_NA_MAO", "TESTE_PULADO",
              "VERIFICADOR_CALADO", "TRABALHO_INACABADO")

ADDED = {"limite": re.compile(r'^\s*"valor"\s*:\s*(-?[\d.]+|true|false)'),
         "excecao": re.compile(r'^\s*"id"\s*:\s*"\w+"\s*,'),
         "flag": re.compile(r"--max-gap\b|--max\s+\d|--min-z\s+\d"),
         "skip": re.compile(r"unittest\.skip|skipTest|pytest\.mark\.(skip|xfail)"
                            r"|\.skip\(\)|xfail|@skip"),
         "silence": re.compile(r"except[^:]*:\s*(pass|\.\.\.)\s*$|check\s*=\s*False"
                               r"|sys\.exit\(0\)|filterwarnings|simplefilter\("),
         "stub": re.compile(r"\bTODO\b|\bFIXME\b|NotImplementedError|raise NotImplementedError")}
REMOVED = {"teste": re.compile(r"def test_")}


def _files(diff):
    """Arquivo -> (novas, removidas). Linhas com número do hunk."""
    changed, current, novo, antigo = {}, None, [], []
    number = 0
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if current:
                changed[current] = (novo, antigo)
            current = line.split(" b/")[-1].strip()
            novo, antigo, number = [], [], 0
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            number = int(match.group(1)) - 1 if match else 0
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+"):
            number += 1
            if current:
                novo.append((number, line[1:]))
        elif line.startswith("-"):
            if current:
                antigo.append(line[1:].strip())
        else:
            number += 1
    if current:
        changed[current] = (novo, antigo)
    return changed


def scan(diff: str) -> list[dict]:
    achados = []
    for arquivo, (novas, removidas) in _files(diff).items():
        motor = arquivo.startswith("pipeline/") or arquivo.startswith("vendor/")
        for numero, texto in novas:
            if arquivo == f"sistema/{CONSTRAINTS_PATH.name}":
                if ADDED["limite"].match(texto):
                    achados.append(("LIMITE_ALTERADO", arquivo, numero,
                                    f"limite alterado: {texto.strip()}; a decisao fica registrada "
                                    f"aqui e nao em um numero solto no codigo"))
                elif ADDED["excecao"].match(texto):
                    achados.append(("LIMITE_ALTERADO", arquivo, numero,
                                    f"excecao nova: {texto.strip()}; excecao precisa de responsavel e data"))
            if ADDED["flag"].search(texto):
                achados.append(("LIMITE_NA_MAO", arquivo, numero,
                                f"limite passado na mao: {texto.strip()}; a barra vive em CONSTRAINTS.md"))
            if ADDED["skip"].search(texto):
                achados.append(("TESTE_PULADO", arquivo, numero, f"teste pulado: {texto.strip()}"))
            if ADDED["silence"].search(texto):
                achados.append(("VERIFICADOR_CALADO", arquivo, numero,
                                f"falha pode estar sendo engolida: {texto.strip()}"))
            if motor and ADDED["stub"].search(texto):
                achados.append(("TRABALHO_INACABADO", arquivo, numero,
                                f"codigo inacabado no motor: {texto.strip()}"))
        if arquivo.startswith("pipeline/test_"):
            for linha in removidas:
                if REMOVED["teste"].match(linha):
                    achados.append(("TESTE_PULADO", arquivo, 0,
                                    f"teste removido: {linha}; apagar verificacao nao e afrouxar a barra"))
    return [{"categoria": c, "arquivo": f, "linha": n, "detalhe": d}
            for c, f, n, d in achados]


def _git(args) -> str | None:
    try:
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="HEAD", help="referencia do diff (padrao HEAD)")
    ap.add_argument("--staged", action="store_true", help="compara apenas o index com HEAD")
    ap.add_argument("--stdin", action="store_true", help="le o diff da entrada padrao")
    a = ap.parse_args()
    if a.stdin:
        diff = sys.stdin.read()
    else:
        args = ["diff", "--unified=0"] + (["--cached"] if a.staged else [f"{a.base}..."])
        diff = _git(args)
        if diff is None:
            print(f"floor_guard: nao consegui ler o diff contra {a.base}; "
                  f"rode dentro de um repositorio git ou use --stdin", file=sys.stderr)
            raise SystemExit(2)
    achados = scan(diff)
    for item in achados:
        print(f"  [{item['categoria']}] {item['arquivo']}:{item['linha']}  {item['detalhe']}")
    if not achados:
        print("floor_guard: barra intacta no diff")
        raise SystemExit(0)
    print(f"floor_guard: {len(achados)} achado(s). Barra afrouxada precisa de decisao "
          f"explicita, nao de numero editado.", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()