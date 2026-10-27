# -*- coding: utf-8 -*-
"""
parse_roteiro.py — roteiro.md -> segments.json (com capítulos).

Formato do roteiro (um arquivo = um episódio):

    # EP05 — Tipos de tempestade

    ## Anã vermelha
    - `av01` [gap:0.00] Anã vermelha.
    - `av02` [gap:0.30] As anãs vermelhas são o tipo de estrela mais comum...

    ## Anã laranja
    - `al01` [gap:0.50] Anã laranja.

Regras:
  - `#`  título do episódio (1 por arquivo).
  - `##` abre um CAPÍTULO (o bloco do catálogo). O heading vira o título breve
         de entrada desse capítulo.
  - `- `  um segmento (uma linha falável). O id entre crases é obrigatório e único;
           `id@N` escolhe outra semente de voz para o mesmo segmento lógico.
         O sufixo opcional `@N` muda só a tentativa de TTS, não o id do segmento.
  - `[gap:X]` pausa ANTES do segmento, em segundos (default 0.18).

Saída: {"episode": str, "chapters": [...], "segments": [...]}

Uso:
  python pipeline/parse_roteiro.py roteiro.md segments.json
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata

LINE = re.compile(r"^\s*-\s*`([^`]+)`\s*(?:\[gap:([\d.]+)\])?\s*(.*)$")
H1 = re.compile(r"^\s*#\s+(.*\S)\s*$")
H2 = re.compile(r"^\s*##\s+(.*\S)\s*$")
NUMBER = re.compile(r"\d")
SEGMENT_ID = re.compile(r"^(?P<id>[^@\s]+)(?:@(?P<attempt>[1-9]\d*))?$")


def slug(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "cap"


def parse(md_path: str) -> dict:
    episode = ""
    chapters: list[dict] = []
    segments: list[dict] = []
    current = None

    with open(md_path, encoding="utf-8") as fh:
        for raw in fh:
            if raw.lstrip().startswith("<!--"):
                continue
            m2 = H2.match(raw)
            if m2:
                label = m2.group(1).strip()
                current = {"id": slug(label), "label": label,
                           "start_index": len(segments)}
                if current["id"] in [c["id"] for c in chapters]:
                    n = 2
                    while f"{current['id']}-{n}" in [c["id"] for c in chapters]:
                        n += 1
                    current["id"] = f"{current['id']}-{n}"
                chapters.append(current)
                continue
            m1 = H1.match(raw)
            if m1:
                if not episode:
                    episode = m1.group(1).strip()
                continue
            m = LINE.match(raw)
            if not m:
                continue
            raw_id, gap, text = m.group(1).strip(), m.group(2), m.group(3).strip()
            if not text:
                continue
            parsed_id = SEGMENT_ID.fullmatch(raw_id)
            if not parsed_id:
                raise ValueError(f"id de segmento inválido: {raw_id!r} (use id ou id@N, N >= 1)")
            sid = parsed_id.group("id")
            segments.append({
                "id": sid,
                "attempt": int(parsed_id.group("attempt") or 1),
                "chapter": current["id"] if current else "intro",
                "text": text,
                "block_gap_before": float(gap) if gap else 0.18,
            })

    for ch in chapters:
        ch["segments"] = [s["id"] for s in segments if s["chapter"] == ch["id"]]
        ch["n_segments"] = len(ch["segments"])

    return {"episode": episode, "chapters": chapters, "segments": segments}


def validate(data: dict) -> list[str]:
    problems: list[str] = []
    ids = [s["id"] for s in data["segments"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"ids duplicados: {', '.join(dupes)}")
    if not data["chapters"]:
        problems.append("nenhum capitulo (use '## Nome do capitulo')")
    for ch in data["chapters"]:
        if not ch["segments"]:
            problems.append(f"capitulo vazio: {ch['label']}")
    for s in data["segments"]:
        if NUMBER.search(s["text"]):
            problems.append(f"{s['id']}: numero cru no texto -> deixe por extenso ou "
                            f"rode o fonetica.py (ex.: '75%' vira 'setenta e cinco por cento' no TTS)")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    md = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    data = parse(md)
    problems = validate(data)
    words = sum(len(s["text"].split()) for s in data["segments"])
    est = round(words / 165 * 60 + sum(s["block_gap_before"] for s in data["segments"]), 1)

    print(f"episodio: {data['episode'] or '(sem titulo)'}")
    print(f"capitulos: {len(data['chapters'])} | segmentos: {len(data['segments'])} | "
          f"palavras: {words} | estimativa: {est:.0f}s (~{est/60:.1f} min)")
    for ch in data["chapters"]:
        print(f"  - {ch['label']:<28} {ch['n_segments']:>3} segmentos")
    if problems:
        print(f"\n>>> {len(problems)} pendencia(s):")
        for p in problems[:30]:
            print("   -", p)
    if out:
        json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
