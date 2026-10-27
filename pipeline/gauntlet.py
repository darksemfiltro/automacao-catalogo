# -*- coding: utf-8 -*-
"""
gauntlet.py — avaliação automática do plano de cenas (o "gauntlet" do episódio).

Roda DEPOIS do build_cenas e ANTES de renderizar: lê `episode.json` e reprova a saída
quando ela repetiria os erros que a gente já viu —

  1. OBJETO SOBREPOSTO   — dois objetos grandes ocupando a mesma área ao mesmo tempo
  2. OBJETO INVISÍVEL    — objeto que só aparece no escuro sobre fundo branco (galáxia…)
  3. TEXTO SOBRE OBJETO  — palavra/callout/frase caindo em cima de um objeto ou motion
  4. OBJETO REPETIDO     — o mesmo objeto em beats seguidos (parece "não mudou")
  5. RITMO PARADO        — trecho sem NENHUM conteúdo por mais de `--max-gap` (ritmo)
  6. OBJETO FORA DO TEMA — objeto de categoria distinta do tema do capítulo

Com `--fix`, corrige o que dá (corta fundo branco onde o objeto sumiria, separa objetos
sobrepostos e EMPURRA o texto para o lado livre) e regrava o `episode.json`. Use em loop:
build -> gauntlet --fix.

Uso:
  python pipeline/gauntlet.py episode.json [--fix] [--strict]

O ritmo vem de `sistema/CONSTRAINTS.md` (`plano.max_gap_s`). Passar `--max-gap`
na mão é caminho de exceção e o `floor_guard.py` acusa a flag.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import ilustras
import mg
from constraints import value as limite

POS = {"centro": (960, 560), "centro_alto": (960, 490), "centro_baixo": (960, 700),
       "esquerda": (520, 560), "direita": (1400, 560), "canto_bd": (1500, 800)}

# tipos que ocupam área (objetos/mídia/telas de dados)
VIS = ("ilustra", "imagens", "foto", "video", "grafico", "barra", "medidor", "comparacao")
# tipos de texto
TXT = ("callout", "frase", "palavra", "lista_item")
COVERS = ("heroi", "textao")
CALL = {"baixo": (960, 870), "acima": (960, 400), "esq": (470, 700), "dir": (1450, 700),
        "centro": (960, 560), "topo": (960, 380), "legenda": (960, 1000)}


def _box(e):
    t = e["tipo"]
    if t == "mg":
        if mg.is_full(str(e.get("id") or "")):     # cena de tela cheia (fundo animado)
            return (0, 0, 1920, 1080)
        w = int(e.get("w") or 1180)
        cx, cy = POS.get(e.get("pos", "centro_alto"), POS["centro_alto"])
        return (cx - w / 2, cy - 330, cx + w / 2, cy + 330)
    # fração VISÍVEL da arte dentro do SVG (o viewBox é quadrado, o desenho é menor)
    vis = 1.0
    if t == "imagens":
        n = max(1, len(e.get("ids", [])))
        size = min(int(e.get("size") or 500), 500)
        w = n * size + (n - 1) * 44
        h = int(size * 1.12)
        vis = 0.66
    elif t == "comparacao":
        base = int(e.get("size") or 620)
        itens = e.get("itens") or []
        gap = 40
        cell = max([int(base * float(it.get("escala", 1))) for it in itens] or [base])
        w = len(itens) * cell + (len(itens) - 1) * gap
        h = base + 90
        vis = 0.82
    elif t in ("grafico", "barra", "medidor"):
        w = int(e.get("w") or 1500)
        n = len(e.get("itens") or []) or (2 if t == "grafico" else 1)
        h = 140 + n * 74 if t == "grafico" else 300
    elif t in ("ilustra", "mascote"):
        w = h = int((e.get("size") or 780) * 1.25)
        vis = 0.66
    else:
        w = h = int((e.get("size") or 780) * 1.25)
    w, h = w * vis, h * vis
    pos = e.get("move_to") or e.get("pos", "centro")
    cx, cy = POS.get(pos, POS["centro"])
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def _push_text(e, side):
    """Manda o texto para o lado indicado (callout/frase têm variantes laterais)."""
    if e["tipo"] == "callout":
        e["pos"] = "dir" if side == "dir" else "esq"
    elif e["tipo"] == "frase":
        e["pos"] = "direita" if side == "dir" else "esquerda"
    elif e["tipo"] == "lista_item":
        e["pos"] = "dir" if side == "dir" else "esq"
    elif e["tipo"] == "palavra":
        e["tipo"] = "callout"
        e["pos"] = "dir" if side == "dir" else "esq"


def _text_box(e):
    t = e["tipo"]
    if t in ("callout", "palavra"):
        pos = e.get("pos", "baixo")
        cx, cy = CALL.get(pos, CALL["baixo"])
        if t == "callout":
            cy -= int(e.get("slot", 0)) * int(212)
        if pos in ("esq", "esquerda"):
            return (60, cy - 190, 880, cy + 150)
        if pos in ("dir", "direita"):
            return (1040, cy - 190, 1860, cy + 150)
        return (120, cy - 160, 1800, cy + 130)
    if t == "frase":
        p = str(e.get("pos") or "centro")
        if p in ("baixo", "legenda"):
            return (140, 872, 1780, 1030)      # legenda abaixo dos objetos
        if p.startswith("esq"):
            return (70, 330, 920, 770)
        if p.startswith("dir"):
            return (1000, 330, 1850, 770)
        return (120, 400, 1800, 900)
    if t == "lista_item":
        left = 1010 if e.get("pos", "dir") in ("dir", "direita") else 150
        top = 300 + int(e.get("indice", 0)) * 119
        return (left, top, left + 800, top + 96)
    return None


def _inter(a, b):
    x = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return x * y


def _area(a):
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def _shrink(b, f=0.16):
    w, h = b[2] - b[0], b[3] - b[1]
    return (b[0] + w * f, b[1] + h * f, b[2] - w * f, b[3] - h * f)


def _obj_id(e):
    if e["tipo"] in ("ilustra", "mg"):
        return e.get("id")
    if e["tipo"] == "imagens":
        return (e.get("ids") or [None])[0]
    return e["tipo"]


def _covering(seq, t):
    return [e for e in seq if e["start"] <= t < e["start"] + e["dur"]]


def check(ep, max_gap=0.9, step=0.4):
    els = ep["elements"]
    total = ep.get("total", 0.0)
    # cenas `mg` de TELA CHEIA são fundo animado (não contam como objeto que ocupa área);
    # widgets `mg` (painel) contam como conteúdo/objeto.
    vis = [e for e in els if e["tipo"] in VIS
           or (e["tipo"] == "mg" and not mg.is_full(str(e.get("id") or "")))]
    covers = [e for e in els if e["tipo"] in COVERS]
    whites = [e for e in els if e["tipo"] in ("fundo", "fundo_seg") and e.get("fundo") == "white"]
    texts = [e for e in els if e["tipo"] in TXT]
    graphics = [e for e in els if e["tipo"] in ("grafico", "barra", "medidor", "comparacao")]
    findings = []

    t = 0.0
    while t < total:
        if not _covering(covers, t):
            act = _covering(vis, t)
            boxes = [(_obj_id(e), _box(e)) for e in act]
            # 1) objeto sobre objeto
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    (ia, ba), (ib, bb) = boxes[i], boxes[j]
                    if _inter(_shrink(ba), _shrink(bb)) > 0.18 * min(_area(ba), _area(bb)):
                        findings.append(("overlap", t, f"{ia} sobre {ib}"))
            # 2) objeto invisível no branco
            if _covering(whites, t):
                for oid, _b in boxes:
                    if oid and oid not in ("grafico", "barra", "medidor", "comparacao") \
                            and ilustras.needs_dark(oid):
                        findings.append(("invisivel", t, f"{oid} em fundo branco"))
            # 3) texto sobre objeto/motion (ignora sobreposição de raspão < 0.35 s)
            for te in _covering(texts, t):
                tb = _text_box(te)
                if not tb:
                    continue
                hit = None
                for oe, (oid, ob) in zip(act, boxes):
                    if min(te["start"] + te["dur"], oe["start"] + oe["dur"]) - \
                            max(te["start"], oe["start"]) < 0.35:
                        continue
                    if _inter(_shrink(tb, 0.12), _shrink(ob, 0.12)) > 0.12 * min(_area(tb), _area(ob)):
                        hit = oid
                        break
                if hit:
                    findings.append(("texto_obj", t,
                                     f"{te['tipo']}({te.get('pos')}) sobre {hit}"))
        t += step

    # 4) repetição de objeto em beats seguidos
    order = sorted(vis, key=lambda e: e["start"])
    for a, b in zip(order, order[1:]):
        if _obj_id(a) in ("grafico", "barra", "medidor", "comparacao"):
            continue
        if a.get("tipo") == "mg" and b.get("tipo") == "mg":   # widgets de dados: ok repetir
            continue
        if _obj_id(a) and _obj_id(a) == _obj_id(b):
            findings.append(("repetido", b["start"], _obj_id(a)))

    # 5) ritmo: cobertura real de conteúdo ao longo do tempo
    # O diagrama de tela cheia Ã© pano de fundo, nÃ£o prova de que exista um
    # objeto/cena de primeiro plano ligado Ã  narraÃ§Ã£o.
    seq = [e for e in els if e["tipo"] in VIS + TXT + COVERS + ("mascote",)
           or (e["tipo"] == "mg" and not mg.is_full(str(e.get("id") or "")))]
    iv = sorted((e["start"], e["start"] + e["dur"]) for e in seq)
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + 0.001:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    cur = 0.0
    for a, b in merged:
        if a - cur > max_gap:
            findings.append(("parado", cur, f"{a - cur:.1f}s sem conteúdo"))
        cur = max(cur, b)
    if total - cur > max_gap:
        findings.append(("parado", cur, f"{total - cur:.1f}s final sem conteúdo"))

    shots = ep.get("scene_plan", [])
    for a, b in zip(shots, shots[1:]):
        if a.get("tipo") == b.get("tipo"):
            findings.append(("plano_repetido", b["start"], "Tipos de cena consecutivos iguais"))
        if a.get("entrada") == b.get("entrada"):
            findings.append(("plano_repetido", b["start"], "Entradas consecutivas iguais"))
        if abs(a["start"] + a["dur"] - b["start"]) > 0.01:
            findings.append(("plano_intervalo", b["start"], "Lacuna ou sobreposição entre cenas"))
    if shots and (abs(shots[0]["start"]) > 0.01 or
                  abs(shots[-1]["start"] + shots[-1]["dur"] - total) > 0.01):
        findings.append(("plano_intervalo", 0, "Plano não cobre a duração do episódio"))
    return findings


def fix(ep):
    """Correções automáticas: tira objeto do branco, separa sobrepostos e move texto
    que caiu em cima de um objeto para o lado livre."""
    els = ep["elements"]
    changed = 0

    # fundo branco onde o objeto sumiria
    whites = [e for e in els if e["tipo"] in ("fundo", "fundo_seg") and e.get("fundo") == "white"]
    for e in [x for x in els if x["tipo"] in ("ilustra", "imagens", "foto", "video")]:
        oid = _obj_id(e)
        if not oid or not ilustras.needs_dark(oid):
            continue
        s0, s1 = e["start"], e["start"] + e["dur"]
        for w in whites:
            w0, w1 = w["start"], w["start"] + w["dur"]
            if w0 < s1 and s0 < w1:
                if w0 >= s0 - 0.05:
                    w["start"] = round(max(w["start"], s1), 3)
                    w["dur"] = round(max(0.0, w1 - w["start"]), 3)
                else:
                    w["dur"] = round(max(0.0, s0 - w0), 3)
                changed += 1

    # objetos sobrepostos: manda o 2º para o lado oposto
    order = sorted([e for e in els if e["tipo"] in VIS], key=lambda e: e["start"])
    for i, e in enumerate(order):
        for f in order[i + 1:]:
            if f["start"] >= e["start"] + e["dur"]:
                break
            if _inter(_shrink(_box(e)), _shrink(_box(f))) > 0.18 * min(_area(_box(e)), _area(_box(f))):
                f["pos"] = "direita" if e.get("pos") != "direita" else "esquerda"
                changed += 1

    # texto sobre objeto: se o objeto está CENTRALIZADO, abre TELA DIVIDIDA (objeto
    # para um lado, texto para o outro); senão empurra o texto para o lado livre.
    for t in [e for e in els if e["tipo"] in TXT]:
        tb = _text_box(t)
        if not tb:
            continue
        for o in [e for e in els if e["tipo"] in VIS]:
            if min(t["start"] + t["dur"], o["start"] + o["dur"]) - \
                    max(t["start"], o["start"]) < 0.35:
                continue
            ob = _box(o)
            if _inter(_shrink(tb, 0.12), _shrink(ob, 0.12)) <= 0.12 * min(_area(tb), _area(ob)):
                continue
            ocx = (ob[0] + ob[2]) / 2
            if abs(ocx - 960) < 280 and o.get("pos", "centro") in (
                    "centro", "centro_alto", "centro_baixo"):
                o["pos"] = "esquerda"
                o.pop("move_to", None)
                _push_text(t, "dir")
            else:
                _push_text(t, "dir" if ocx < 960 else "esq")
            changed += 1
            tb = _text_box(t)
            break

    ep["elements"] = [x for x in els if not (x["tipo"] in ("fundo", "fundo_seg")
                                             and x.get("dur", 0) <= 0.05)]
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?", default="episode.json")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--max-gap", type=float, default=None,
                    help="sobraposicao de CONSTRAINTS.md; passar na mao e caminho de excecao")
    ap.add_argument("--strict", action="store_true",
                    help="também falha por ritmo (parado) e repetição")
    a = ap.parse_args()
    max_gap = limite("plano.max_gap_s") if a.max_gap is None else a.max_gap
    ep = json.load(open(a.episode, encoding="utf-8"))

    if a.fix:
        total = 0
        for _ in range(4):                 # itera: mover um texto pode liberar o próximo
            n = fix(ep)
            total += n
            if n == 0:
                break
        json.dump(ep, open(a.episode, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"gauntlet --fix: {total} correção(ões) aplicada(s)")

    print(f"gauntlet: max-gap {max_gap}s (CONSTRAINTS.md plano.max_gap_s)"
          + ("" if a.max_gap is None else " — valor pasado na mão, registrado como exceção"))
    f = check(ep, max_gap=max_gap)
    by = {}
    for code, t, msg in f:
        by.setdefault(code, []).append((t, msg))
    for code in ("invisivel", "overlap", "texto_obj", "parado", "repetido", "plano_repetido", "plano_intervalo"):
        for t, msg in by.get(code, [])[:12]:
            print(f"  [{code}] {t:7.1f}s  {msg}")
    print(f"gauntlet: {len(f)} achado(s) | " +
          " ".join(f"{k}:{len(v)}" for k, v in sorted(by.items())))
    critical = ("invisivel", "overlap", "texto_obj", "plano_intervalo", "plano_repetido")
    if a.strict:
        critical = critical + ("parado", "repetido")
    sys.exit(1 if any(c in by for c in critical) else 0)


if __name__ == "__main__":
    main()
