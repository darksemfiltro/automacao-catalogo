# -*- coding: utf-8 -*-
"""
checa_densidade.py — gate de densidade da edição.

Lê a composição gerada (index.html) e mede os trechos sem conteúdo em cena
(considerando cards, overlays, mídia; ignorando fundo e o rótulo de bloco).
Falha se existir algum buraco maior que o limite — o vídeo não pode ter fundo parado.

Uso:
  python pipeline/checa_densidade.py hyperframes/index.html

O maior buraco tolerado vem de `sistema/CONSTRAINTS.md` (`montagem.max_buraco_s`).
Passar `--max` na mão é caminho de exceção e o `floor_guard.py` acusa a flag.
"""
from __future__ import annotations

import argparse
import re
import sys

from constraints import value as limite

CLIP = re.compile(r'<(?:div|img|video|span|svg)\b[^>]*id="e\d+"[^>]*>')
START = re.compile(r'data-start="([0-9.]+)"')
DUR = re.compile(r'data-duration="([0-9.]+)"')
Z = re.compile(r'data-track-index="(\d+)"')


def intervals(html, min_z=5):
    out = []
    for m in CLIP.finditer(html):
        tag = m.group(0)
        s, d, z = START.search(tag), DUR.search(tag), Z.search(tag)
        if not (s and d):
            continue
        if "letter-spacing:.22em" in tag:  # rótulo de bloco (eyebrow) não conta
            continue
        if z and int(z.group(1)) < min_z:
            continue
        a = float(s.group(1))
        out.append((a, a + float(d.group(1))))
    return sorted(out)


def gaps(intervals, total):
    merged = []
    for a, b in intervals:
        if merged and a <= merged[-1][1] + 0.001:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    result, cur = [], 0.0
    for a, b in merged:
        if a - cur > 0.05:
            result.append((cur, a, a - cur))
        cur = max(cur, b)
    if total - cur > 0.05:
        result.append((cur, total, total - cur))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--max", type=float, default=None,
                    help="maior buraco tolerado; padrao vem de CONSTRAINTS.md")
    ap.add_argument("--min-z", type=int, default=None,
                    help="z-index inicial de conteudo; padrao vem de CONSTRAINTS.md")
    a = ap.parse_args()
    max_gap = limite("montagem.max_buraco_s") if a.max is None else a.max
    min_z = limite("montagem.min_z") if a.min_z is None else a.min_z
    html = open(a.html, encoding="utf-8").read()
    root = re.search(r'id="root"[^>]*data-duration="([0-9.]+)"', html)
    total = float(root.group(1)) if root else max(b for _, b in intervals(html))
    iv = intervals(html, min_z)
    gs = [g for g in gaps(iv, total) if g[2] > 0.6]
    worst = max(gs, key=lambda g: g[2]) if gs else None
    print(f"limite: {max_gap}s (CONSTRAINTS.md montagem.max_buraco_s)"
          + ("" if a.max is None else " — valor passado na mão, registrado como exceção"))
    print(f"clipes: {len(iv)} | duracao: {total:.2f}s | buracos >0.6s: {len(gs)}")
    for s, e, d in gs:
        flag = "  <-- ACIMA DO LIMITE" if d > max_gap else ""
        print(f"  {s:7.2f} -> {e:7.2f}  ({d:4.2f}s){flag}")
    if worst and worst[2] > max_gap:
        print(f"FALHA: buraco de {worst[2]:.2f}s em {worst[0]:.2f}s (max {max_gap}s)")
        sys.exit(1)
    print(f"OK: maior buraco = {worst[2]:.2f}s" if worst else "OK: sem buracos")


if __name__ == "__main__":
    main()
