# -*- coding: utf-8 -*-
"""
mg.py — biblioteca de MOTION GRAPHICS vetorial do Catálogo.

Substitui o objeto cartoon (`ilustras`) por cenas e widgets ANIMADOS, 100% vetoriais,
pensados para fundo ESCURO. Nada de tela branca.

Duas famílias:
  - CENAS (`mode="full"`): quadros 1920x1080 que cobrem a tela inteira com movimento
    (vórtice de tornado, espiral de furacão, sismógrafo, onda de tsunami, linha de
    fogo, nível d'água subindo, seca rachando o solo, nevasca, corte de vulcão,
    campo de vento, corte do oceano, globo, warp). O texto (título/callout) vive
    por cima.
  - WIDGETS (`mode="panel"`): cartões escuros de dados com animação (velocímetro,
    escala de magnitude, termômetro, anel de %, contador de área, régua de distância,
    barra de duração).

Contrato com o gen_comp:
  build(recipe, uid, params) -> {
      "vb": (w, h),              # viewBox do svg
      "mode": "full" | "panel",
      "inner": "<...svg children...>",
      "anims": [ {sel, kind, delay, from, to, cycle, ease, yoyo, origin, dur, ...} ],
  }
  kind in {"mg_loop", "mg_once", "mg_draw", "mg_count"}.

Nada aqui depende de rede: só SVG + classes; a animação é aplicada pelo timeline
único e pausado do gen_comp (seek-safe).
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------- paleta
CYAN = "#56ccff"
BLUE = "#2b6fbf"
DEEP = "#0d2b4a"
AMBER = "#ffb02b"
ORANGE = "#ff7a3c"
RED = "#ff4a3c"
VIOLET = "#9a6bff"
GREEN = "#39d98a"
WHITE = "#eaf6ff"
INK = "#dbe9fb"

FULL = (1920, 1080)


def _A(sel, kind, delay=0.0, **kw):
    d = {"sel": sel, "kind": kind, "delay": delay}
    d.update(kw)
    return d


def _wave(y, amp, wl, phase, x0=-260, x1=2180, step=22):
    pts, x = [], x0
    while x <= x1:
        pts.append(f"{x:.0f},{y + amp * math.sin(x / wl + phase):.1f}")
        x += step
    return "M" + " L".join(pts)


def _spiral(cx, cy, r0, r1, steps, a0, twist):
    pts = []
    for k in range(steps + 1):
        t = k / steps
        r = r0 + (r1 - r0) * t
        a = a0 + twist * t
        pts.append(f"{cx + math.cos(a) * r:.1f},{cy + math.sin(a) * r:.1f}")
    return "M" + " L".join(pts)


def _cracks(uid, seed=1):
    """Rede de rachaduras do solo seco (linhas para desenhar com mg_draw)."""
    st = seed
    def rnd():
        nonlocal st
        st = (1103515245 * st + 12345) & 0x7FFFFFFF
        return st / 0x7FFFFFFF
    paths = []
    for i in range(9):
        x = 120 + i * 200 + rnd() * 80
        y = 860
        d = [f"M{x:.0f},{y:.0f}"]
        for k in range(6):
            x += (rnd() - 0.5) * 130
            y += 18 + rnd() * 26
            d.append(f"L{x:.0f},{y:.0f}")
            if k == 2:
                bx, by = x, y
                d.append(f"M{bx:.0f},{by:.0f}")
                for j in range(3):
                    bx += (rnd() - 0.5) * 120
                    by += 14 + rnd() * 20
                    d.append(f"L{bx:.0f},{by:.0f}")
                d.append(f"M{x:.0f},{y:.0f}")
        paths.append(f'<path class="d-crack" d="{" ".join(d)}" fill="none" '
                     f'stroke="{INK}" stroke-width="3" opacity="0.5" pathLength="1" '
                     f'style="stroke-dasharray:1;stroke-dashoffset:1"/>')
    return "".join(paths)


def _flame(cx, base, h, fill, w=46):
    top = base - h
    return (f'<path d="M{cx},{base} C{cx - w},{base - h * 0.42} {cx - w * 0.35},{top + h * 0.22} '
            f'{cx},{top} C{cx + w * 0.35},{top + h * 0.22} {cx + w},{base - h * 0.42} '
            f'{cx},{base} Z" fill="{fill}" opacity="0.92"/>')


# ================================================================ CENAS (full)

def scene_vortex(uid, p):
    """Tornado: funil de anéis girando + detritos subindo + rajadas."""
    rings, debris, streaks = [], [], []
    n = 20
    for i in range(n):
        t = i / (n - 1)
        cy = 90 + t * 800
        rx = 34 + 340 * (1 - t) ** 1.05
        ry = 12 + 12 * (1 - t)
        op = 0.08 + 0.40 * (1 - t)
        rings.append(f'<ellipse class="v-r" cx="960" cy="{cy:.0f}" rx="{rx:.0f}" '
                     f'ry="{ry:.0f}" fill="none" stroke="{CYAN}" '
                     f'stroke-width="{5 - 2.4 * t:.1f}" opacity="{op:.2f}"/>')
    for i in range(16):
        t = i / 15
        cx = 960 + math.sin(i * 2.1) * (60 + 180 * (1 - t))
        cy = 780 - t * 620
        debris.append(f'<circle class="v-d" cx="{cx:.0f}" cy="{cy:.0f}" '
                      f'r="{2 + (1 - t) * 4:.1f}" fill="{INK}" opacity="0"/>')
    for i in range(5):
        y = 120 + i * 90
        streaks.append(f'<line class="v-s" x1="-240" y1="{y}" x2="120" y2="{y}" '
                       f'stroke="{WHITE}" stroke-width="3" opacity="0.0" '
                       f'stroke-linecap="round"/>')
    inner = (
        f'<g class="v-fun">{"".join(rings)}</g>'
        f'<g class="v-deb">{"".join(debris)}</g>'
        f'<g class="v-streak">{"".join(streaks)}</g>'
        f'<line x1="0" y1="906" x2="1920" y2="906" stroke="{INK}" stroke-width="4" '
        f'opacity="0.35"/>'
        f'<ellipse cx="960" cy="906" rx="420" ry="26" fill="none" stroke="{CYAN}" '
        f'stroke-width="3" opacity="0.25"/>')
    anims = []
    for i in range(n):
        anims.append(_A(f".v-r:nth-child({i + 1})", "mg_loop", delay=(i * 0.05) % 0.9,
                        frm={"scaleX": 1}, to={"scaleX": 0.52},
                        cycle=0.9 + i * 0.02, ease="sine.inOut", yoyo=True))
    for i in range(16):
        anims.append(_A(f".v-d:nth-child({i + 1})", "mg_loop", delay=(i * 0.12) % 1.2,
                        frm={"y": 0, "opacity": 0}, to={"y": -260, "opacity": 1},
                        cycle=1.2, ease="none", yoyo=False))
    for i in range(5):
        anims.append(_A(f".v-s:nth-child({i + 1})", "mg_loop", delay=(i * 0.35) % 1.6,
                        frm={"x": 0, "opacity": 0.0}, to={"x": 2000, "opacity": 0.7},
                        cycle=1.6, ease="sine.inOut", yoyo=False))
    anims.append(_A(".v-fun", "mg_loop", frm={"rotate": -5}, to={"rotate": 5},
                    cycle=2.0, ease="sine.inOut", yoyo=True, origin="960 500"))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_spiral_storm(uid, p):
    """Furacão visto de cima: braços em espiral girando + olho pulsante + bandas."""
    arms, dots = [], []
    for a in range(5):
        a0 = 2 * math.pi * a / 5
        arms.append(f'<path d="{_spiral(960, 540, 40, 470, 46, a0, 2.1)}" fill="none" '
                    f'stroke="{CYAN}" stroke-width="14" opacity="0.42" '
                    f'stroke-linecap="round"/>')
        arms.append(f'<path d="{_spiral(960, 540, 70, 430, 40, a0 + 0.35, 2.0)}" fill="none" '
                    f'stroke="{WHITE}" stroke-width="5" opacity="0.28" stroke-linecap="round"/>')
    bands = []
    for i, r in enumerate((300, 380, 460, 540)):
        bands.append(f'<circle cx="960" cy="540" r="{r}" fill="none" stroke="{BLUE}" '
                     f'stroke-width="{6 - i}" stroke-dasharray="14 22" opacity="0.35"/>')
    for i in range(26):
        rr = 160 + (i * 137) % 620
        ang = i * 2.4
        dots.append(f'<circle class="s-p" cx="{960 + math.cos(ang) * rr:.0f}" '
                    f'cy="{540 + math.sin(ang) * rr:.0f}" r="3" fill="{WHITE}" opacity="0"/>')
    inner = (
        f'<g class="s-arms">{"".join(arms)}</g>'
        f'<g class="s-band">{"".join(bands)}</g>'
        f'<g class="s-parts">{"".join(dots)}</g>'
        f'<circle cx="960" cy="540" r="44" fill="#031422" stroke="{WHITE}" '
        f'stroke-width="5" opacity="0.9"/>'
        f'<circle cx="960" cy="540" r="16" fill="{WHITE}" opacity="0.85"/>')
    anims = [
        _A(".s-arms", "mg_loop", frm={"rotate": 0}, to={"rotate": 360}, cycle=8.5,
           ease="none", yoyo=False, origin="960 540"),
        _A(".s-arms", "mg_loop", frm={"scale": 0.95}, to={"scale": 1.06}, cycle=4.5,
           ease="sine.inOut", yoyo=True, origin="960 540"),
        _A(".s-band", "mg_loop", frm={"rotate": 0}, to={"rotate": -360}, cycle=14,
           ease="none", yoyo=False, origin="960 540"),
        _A("> circle:first-of-type", "mg_loop", frm={"scale": 1}, to={"scale": 1.22},
           cycle=1.5, ease="sine.inOut", yoyo=True, origin="960 540"),
    ]
    for i in range(26):
        anims.append(_A(f".s-p:nth-child({i + 1})", "mg_loop", delay=(i * 0.09) % 1.7,
                        frm={"opacity": 0, "scale": 0.6}, to={"opacity": 0.8, "scale": 1.4},
                        cycle=1.7, ease="sine.inOut", yoyo=True))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_seismic(uid, p):
    """Terremoto: falha, epicentro pulsando e traço de sismógrafo."""
    grid = []
    for x in range(0, 1921, 160):
        grid.append(f'<line x1="{x}" y1="0" x2="{x}" y2="1080" stroke="{BLUE}" '
                    f'stroke-width="1.5" opacity="0.16"/>')
    for y in range(0, 1081, 120):
        grid.append(f'<line x1="0" y1="{y}" x2="1920" y2="{y}" stroke="{BLUE}" '
                    f'stroke-width="1.5" opacity="0.16"/>')
    peaks = []
    x = -40
    yy = 300
    peaks.append(f"M{x},{yy}")
    i = 0
    while x < 1960:
        x += 26
        amp = 0 if i % 4 else (60 if i % 8 == 3 else 26)
        yy = 300 + (amp if i % 2 else -amp)
        peaks.append(f"L{x},{yy}")
        i += 1
    trace = " ".join(peaks)
    inner = (
        f'<g class="e-shake">'
        f'{"".join(grid)}'
        f'<line x1="0" y1="748" x2="1920" y2="748" stroke="{INK}" stroke-width="4" '
        f'opacity="0.35"/>'
        f'<path d="M760,748 L840,700 L900,748 L980,690 L1040,748 L1120,712 L1180,748" '
        f'fill="none" stroke="{RED}" stroke-width="5" opacity="0.8"/>'
        f'<g class="e-rings" transform="translate(960,748)">'
        f'<ellipse class="e-ring" rx="60" ry="16" fill="none" stroke="{AMBER}" '
        f'stroke-width="4" opacity="0.9"/>'
        f'<ellipse class="e-ring" rx="60" ry="16" fill="none" stroke="{AMBER}" '
        f'stroke-width="3" opacity="0.7"/>'
        f'<ellipse class="e-ring" rx="60" ry="16" fill="none" stroke="{AMBER}" '
        f'stroke-width="2" opacity="0.5"/></g>'
        f'<circle cx="960" cy="748" r="12" fill="{RED}"/>'
        f'<path class="e-trace" d="{trace}" fill="none" stroke="{CYAN}" stroke-width="4" '
        f'opacity="0.85" pathLength="1" style="stroke-dasharray:1;stroke-dashoffset:1"/>'
        f'<g class="e-live">'
        f'<path d="{trace}" transform="translate(0,300)" fill="none" stroke="{CYAN}" '
        f'stroke-width="3" opacity="0.45"/>'
        f'<path d="{trace}" transform="translate(1920,300)" fill="none" stroke="{CYAN}" '
        f'stroke-width="3" opacity="0.45"/></g></g>')
    anims = [
        _A(".e-trace", "mg_draw", dur=2.6, ease="power1.inOut"),
        # tremor contínuo: a cena treme (é um terremoto, afinal)
        _A(".e-shake", "mg_loop", frm={"x": 0, "y": 0}, to={"x": 4, "y": -6},
           cycle=0.16, ease="sine.inOut", yoyo=True),
        _A(".e-live", "mg_loop", frm={"x": 0}, to={"x": -1920},
           cycle=3.2, ease="none", yoyo=False),
    ]
    for i in range(3):
        anims.append(_A(f".e-ring:nth-child({i + 1})", "mg_loop", delay=i * 0.4,
                        frm={"scale": 0.3, "opacity": 0.9}, to={"scale": 3.6, "opacity": 0},
                        cycle=1.2, ease="power1.out", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_wave_stack(uid, p):
    """Tsunami: mar em camadas rolando + onda grande subindo + cidade na base."""
    waves = []
    for i, (y, amp, wl, col, op, cyc) in enumerate([
            (770, 14, 260, BLUE, 0.5, 3.2), (806, 20, 200, CYAN, 0.4, 2.6),
            (846, 26, 170, CYAN, 0.34, 2.2), (890, 32, 140, WHITE, 0.22, 1.8)]):
        waves.append((f'<path class="w-v w-v{i}" d="{_wave(y, amp, wl, i)}" fill="none" '
                      f'stroke="{col}" stroke-width="6" opacity="{op}"/>', cyc))
    inner_w = "".join(w[0] for w in waves)
    city = []
    for i, h in enumerate((70, 110, 90, 140, 80, 120, 60)):
        x = 120 + i * 90
        city.append(f'<rect x="{x}" y="{880 - h}" width="58" height="{h}" fill="#0a1a2e" '
                    f'stroke="{BLUE}" stroke-width="2" opacity="0.9"/>')
    big = (f'<path class="w-big" d="M1250,900 C1320,760 1400,700 1510,660 '
           f'C1440,700 1400,760 1420,900 Z" fill="url(#{uid}_sea)" opacity="0.9"/>')
    spray = []
    for i in range(14):
        spray.append(f'<circle class="w-sp" cx="{1510 + (i - 7) * 26}" cy="660" r="4" '
                     f'fill="{WHITE}" opacity="0"/>')
    inner = (
        f'<defs><linearGradient id="{uid}_sea" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{DEEP}"/>'
        f'</linearGradient></defs>'
        f'<rect x="0" y="760" width="1920" height="320" fill="{DEEP}" opacity="0.55"/>'
        f'{inner_w}{big}{"".join(city)}<g class="w-spray">{"".join(spray)}</g>'
        f'<line x1="0" y1="900" x2="1920" y2="900" stroke="{INK}" stroke-width="3" '
        f'opacity="0.25"/>')
    anims = []
    for i, (_, cyc) in enumerate(waves):
        anims.append(_A(f".w-v{i}", "mg_loop", delay=i * 0.25,
                        frm={"x": 0}, to={"x": -460}, cycle=cyc, ease="none", yoyo=False))
    anims.append(_A(".w-big", "mg_once", delay=0.5, frm={"y": 130, "opacity": 0},
                    to={"y": 0, "opacity": 0.95}, dur=1.5, ease="power2.out"))
    anims.append(_A(".w-big", "mg_loop", delay=1.6, frm={"y": 0}, to={"y": -22},
                    cycle=2.2, ease="sine.inOut", yoyo=True))
    for i in range(14):
        anims.append(_A(f".w-sp:nth-child({i + 1})", "mg_loop", delay=0.6 + (i * 0.07) % 0.9,
                        frm={"y": 0, "opacity": 0}, to={"y": -160, "opacity": 1},
                        cycle=0.9, ease="none", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_wildfire(uid, p):
    """Incêndio: linha de fogo tremulando + brasas subindo + fumaça."""
    flames = []
    xs = list(range(180, 1760, 110))
    for i, cx in enumerate(xs):
        h = 150 + (i * 53) % 140
        flames.append(f'<g class="f-f">{_flame(cx, 820, h, f"url(#{uid}f)")}</g>')
    embers = []
    for i in range(22):
        x = 160 + (i * 149) % 1600
        embers.append(f'<circle class="f-e" cx="{x}" cy="800" r="{2 + i % 3}" '
                      f'fill="{AMBER}" opacity="0"/>')
    smoke = []
    for i in range(6):
        x = 300 + i * 280
        smoke.append(f'<circle class="f-s" cx="{x}" cy="720" r="{90 + i * 12}" '
                     f'fill="#12233a" opacity="0"/>')
    inner = (
        f'<defs><linearGradient id="{uid}f" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{ORANGE}"/><stop offset="1" stop-color="{AMBER}"/>'
        f'</linearGradient></defs>'
        f'<g class="f-smoke">{"".join(smoke)}</g>'
        f'<g class="f-flames">{"".join(flames)}</g>'
        f'<g class="f-embers">{"".join(embers)}</g>'
        f'<line x1="0" y1="820" x2="1920" y2="820" stroke="{INK}" stroke-width="4" '
        f'opacity="0.35"/>')
    anims = []
    for i in range(len(xs)):
        anims.append(_A(f".f-f:nth-child({i + 1})", "mg_loop", delay=(i * 0.07) % 0.4,
                        frm={"scaleY": 0.78, "scaleX": 0.92}, to={"scaleY": 1.2, "scaleX": 1.08},
                        cycle=0.4 + (i % 4) * 0.06, ease="sine.inOut", yoyo=True,
                        origin=f"{xs[i]} 820"))
    for i in range(22):
        anims.append(_A(f".f-e:nth-child({i + 1})", "mg_loop", delay=(i * 0.12) % 1.3,
                        frm={"y": 0, "opacity": 0}, to={"y": -340, "opacity": 1},
                        cycle=1.3, ease="none", yoyo=False))
    for i in range(6):
        anims.append(_A(f".f-s:nth-child({i + 1})", "mg_loop", delay=(i * 0.4) % 2.6,
                        frm={"y": 40, "x": 0, "opacity": 0}, to={"y": -300, "x": 60, "opacity": 0.3},
                        cycle=2.6, ease="none", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_water_rise(uid, p):
    """Enchente: chuva, nível d'água subindo e casa sendo invadida."""
    rain = []
    for g in range(6):
        lines = []
        for k in range(4):
            x = 80 + g * 320 + k * 70
            lines.append(f'<line x1="{x}" y1="0" x2="{x - 26}" y2="70" stroke="{CYAN}" '
                         f'stroke-width="3" opacity="0.55"/>')
        rain.append(f'<g class="w-rain">{lines and "".join(lines)}</g>')
    house = (f'<g><rect x="230" y="620" width="240" height="180" fill="#0a1a2e" '
             f'stroke="{BLUE}" stroke-width="3"/><path d="M215,620 L350,520 L485,620 Z" '
             f'fill="#0a1a2e" stroke="{BLUE}" stroke-width="3"/></g>')
    inner = (
        f'<rect x="0" y="0" width="1920" height="1080" fill="#04070e" opacity="0.5"/>'
        f'<g class="w-rainwrap">{"".join(rain)}</g>{house}'
        f'<g class="w-body">'
        f'<rect x="-200" y="600" width="2320" height="480" fill="{DEEP}" opacity="0.92"/>'
        f'<path d="{_wave(600, 12, 220, 0)} L2180,1080 L-260,1080 Z" fill="{CYAN}" '
        f'opacity="0.62"/>'
        f'<g class="w-tex">'
        f'<path d="{_wave(680, 9, 240, 1)}" fill="none" stroke="{WHITE}" stroke-width="4" '
        f'opacity="0.35"/>'
        f'<path d="{_wave(790, 11, 200, 2)}" fill="none" stroke="{WHITE}" stroke-width="4" '
        f'opacity="0.28"/>'
        f'<path d="{_wave(910, 13, 260, 3)}" fill="none" stroke="{WHITE}" stroke-width="4" '
        f'opacity="0.22"/></g>'
        f'<g class="w-rips">'
        f'<ellipse class="w-rip" cx="700" cy="600" rx="30" ry="9" fill="none" '
        f'stroke="{WHITE}" stroke-width="3" opacity="0.8"/>'
        f'<ellipse class="w-rip" cx="1200" cy="600" rx="30" ry="9" fill="none" '
        f'stroke="{WHITE}" stroke-width="3" opacity="0.8"/></g></g>'
        f'<line x1="0" y1="800" x2="1920" y2="800" stroke="{INK}" stroke-width="3" '
        f'opacity="0.2"/>')
    anims = []
    for g in range(6):
        anims.append(_A(f".w-rain:nth-child({g + 1})", "mg_loop", delay=(g * 0.1) % 0.6,
                        frm={"y": -120}, to={"y": 1240}, cycle=0.6, ease="none", yoyo=False))
    anims.append(_A(".w-body", "mg_once", delay=0.6, frm={"y": 0}, to={"y": -430},
                    dur=2.2, ease="power1.inOut"))
    anims.append(_A(".w-body > path", "mg_loop", frm={"x": 0}, to={"x": -220},
                    cycle=2.0, ease="none", yoyo=False))
    for i in range(3):
        anims.append(_A(f".w-tex path:nth-child({i + 1})", "mg_loop",
                        frm={"x": 0}, to={"x": -260}, cycle=1.5 + i * 0.4,
                        ease="none", yoyo=False))
    for i in range(2):
        anims.append(_A(f".w-rip:nth-child({i + 1})", "mg_loop", delay=i * 0.5,
                        frm={"scale": 0.4, "opacity": 0.9}, to={"scale": 3.0, "opacity": 0},
                        cycle=1.1, ease="power1.out", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_drought(uid, p):
    """Seca: solo rachando, sol forte e poeira."""
    rays = []
    for i in range(12):
        a = 2 * math.pi * i / 12
        rays.append(f'<line x1="{1470 + math.cos(a) * 120:.0f}" '
                    f'y1="{240 + math.sin(a) * 120:.0f}" '
                    f'x2="{1470 + math.cos(a) * 200:.0f}" '
                    f'y2="{240 + math.sin(a) * 200:.0f}" stroke="{AMBER}" '
                    f'stroke-width="6" stroke-linecap="round" opacity="0.7"/>')
    dust = []
    for i in range(16):
        y = 300 + (i * 71) % 460
        dust.append(f'<circle class="d-d" cx="{-40 - i * 40}" cy="{y}" r="{2 + i % 3}" '
                    f'fill="{INK}" opacity="0.5"/>')
    heat = []
    for i in range(6):
        heat.append(f'<path class="d-h" d="{_wave(700 + i * 26, 6, 190, i)}" fill="none" '
                    f'stroke="{AMBER}" stroke-width="3" opacity="0.25"/>')
    inner = (
        f'<g class="d-sun">{"".join(rays)}</g>'
        f'<circle cx="1470" cy="240" r="96" fill="{AMBER}" opacity="0.28"/>'
        f'<circle cx="1470" cy="240" r="66" fill="{AMBER}" opacity="0.85"/>'
        f'<rect x="0" y="852" width="1920" height="228" fill="#1b1407" opacity="0.7"/>'
        f'{_cracks(uid, seed=7)}'
        f'<g class="d-heat">{"".join(heat)}</g>'
        f'<g class="d-dust">{"".join(dust)}</g>'
        f'<line x1="0" y1="852" x2="1920" y2="852" stroke="{AMBER}" stroke-width="4" '
        f'opacity="0.4"/>')
    anims = [_A(".d-sun", "mg_loop", frm={"rotate": 0}, to={"rotate": 360}, cycle=13,
                ease="none", yoyo=False, origin="1470 240")]
    for i in range(6):
        anims.append(_A(f".d-h:nth-child({i + 1})", "mg_loop", delay=(i * 0.2) % 1.2,
                        frm={"y": 0, "opacity": 0}, to={"y": -170, "opacity": 0.4},
                        cycle=1.2, ease="none", yoyo=False))
    ncr = inner.count('class="d-crack"')
    for i in range(ncr):
        anims.append(_A(f".d-crack:nth-of-type({i + 1})", "mg_draw",
                        delay=i * 0.22, dur=1.1, ease="power1.out"))
    for i in range(16):
        anims.append(_A(f".d-d:nth-child({i + 1})", "mg_loop", delay=(i * 0.2) % 2.2,
                        frm={"x": 0, "opacity": 0.0}, to={"x": 2100, "opacity": 0.6},
                        cycle=2.2, ease="none", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_snowstorm(uid, p):
    """Nevasca: neve caindo com vento, rajadas e monte acumulando."""
    groups = []
    for g in range(7):
        flakes = []
        for k in range(11):
            x = 40 + g * 280 + (k * 71) % 280
            y = (k * 96 + g * 40) % 1080
            r = 3 + (k + g) % 4
            flakes.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{WHITE}" opacity="0.95"/>')
        groups.append(f'<g class="s-snow">{"".join(flakes)}</g>')
    gusts = []
    for i in range(6):
        y = 110 + i * 150
        gusts.append(f'<line class="s-g" x1="-300" y1="{y}" x2="60" y2="{y - 100}" '
                     f'stroke="{WHITE}" stroke-width="4" stroke-linecap="round" opacity="0"/>')
    drift = (f'<path class="s-drift" d="M-100,1080 C300,930 700,1000 1100,910 '
             f'C1450,840 1750,950 2020,870 L2020,1080 Z" fill="#16263f" opacity="1"/>')
    inner = (
        f'<rect x="0" y="0" width="1920" height="1080" fill="#050a14" opacity="0.15"/>'
        f'<g class="s-snows">{"".join(groups)}</g>'
        f'<g class="s-gusts">{"".join(gusts)}</g>{drift}'
        f'<path d="{_wave(875, 10, 300, 0)}" fill="none" stroke="{WHITE}" stroke-width="5" '
        f'opacity="0.5"/>')
    anims = []
    for g in range(7):
        anims.append(_A(f".s-snow:nth-child({g + 1})", "mg_loop", delay=(g * 0.3) % 2.0,
                        frm={"y": -180, "x": 0}, to={"y": 1240, "x": 150},
                        cycle=2.0 + g * 0.25, ease="none", yoyo=False))
    for i in range(6):
        anims.append(_A(f".s-g:nth-child({i + 1})", "mg_loop", delay=(i * 0.45) % 1.8,
                        frm={"x": 0, "opacity": 0}, to={"x": 2200, "opacity": 0.8},
                        cycle=1.8, ease="sine.inOut", yoyo=False))
    anims.append(_A(".s-drift", "mg_once", delay=0.4, frm={"y": 90, "opacity": 0},
                    to={"y": 0, "opacity": 1}, dur=1.6, ease="power2.out"))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_volcano(uid, p):
    """Vulcão em corte: câmara magmática, chaminé e erupção."""
    ash = []
    for i in range(26):
        x = 700 + (i * 97) % 520
        ash.append(f'<circle class="l-a" cx="{x}" cy="300" r="{2 + i % 3}" fill="#9aa7bd" '
                   f'opacity="0"/>')
    lava = []
    for i in range(16):
        lava.append(f'<circle class="l-p" cx="{960 + (i - 8) * 6}" cy="330" r="5" '
                    f'fill="{ORANGE}" opacity="0"/>')
    inner = (
        f'<defs><linearGradient id="{uid}m" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{RED}"/><stop offset="1" stop-color="{AMBER}"/>'
        f'</linearGradient></defs>'
        f'<path d="M0,1080 L0,760 L620,760 L880,420 L1040,420 L1300,760 L1920,760 '
        f'L1920,1080 Z" fill="#0a1424" stroke="{BLUE}" stroke-width="3" opacity="0.95"/>'
        f'<ellipse class="l-cr" cx="960" cy="420" rx="120" ry="34" fill="#050a14" '
        f'stroke="{ORANGE}" stroke-width="5"/>'
        f'<path class="l-conduit" d="M960,420 L960,860" stroke="url(#{uid}m)" '
        f'stroke-width="26" opacity="0.85" pathLength="1" stroke-dasharray="0.16 0.84" '
        f'style="stroke-dashoffset:0"/>'
        f'<ellipse class="l-ch" cx="960" cy="920" rx="200" ry="90" fill="url(#{uid}m)" '
        f'opacity="0.9"/>'
        f'<g class="l-parts">{"".join(lava)}</g>'
        f'<path class="l-flow" d="M1040,420 C1120,560 1080,700 1200,860" fill="none" '
        f'stroke="{ORANGE}" stroke-width="16" stroke-linecap="round" opacity="0.9" '
        f'pathLength="1" style="stroke-dasharray:1;stroke-dashoffset:1"/>'
        f'<g class="l-ash">{"".join(ash)}</g>'
        f'<ellipse cx="960" cy="360" rx="180" ry="70" fill="{ORANGE}" opacity="0.12"/>')
    anims = [
        _A(".l-ch", "mg_loop", frm={"scale": 0.92, "opacity": 0.7},
           to={"scale": 1.14, "opacity": 1}, cycle=1.0, ease="sine.inOut", yoyo=True,
           origin="960 920"),
        _A(".l-cr", "mg_loop", frm={"scale": 0.9, "opacity": 0.7},
           to={"scale": 1.15, "opacity": 1}, cycle=0.8, ease="sine.inOut", yoyo=True,
           origin="960 420"),
        _A(".l-conduit", "mg_loop", frm={"strokeDashoffset": 1}, to={"strokeDashoffset": 0},
           cycle=0.7, ease="none", yoyo=False),
        _A(".l-flow", "mg_draw", delay=0.4, dur=1.4, ease="power1.inOut"),
    ]
    for i in range(16):
        anims.append(_A(f".l-p:nth-child({i + 1})", "mg_loop", delay=(i * 0.08) % 0.9,
                        frm={"y": 40, "opacity": 0}, to={"y": -560, "opacity": 1},
                        cycle=0.9, ease="none", yoyo=False))
    for i in range(26):
        anims.append(_A(f".l-a:nth-child({i + 1})", "mg_loop", delay=(i * 0.14) % 2.4,
                        frm={"y": -60, "opacity": 0}, to={"y": 560, "opacity": 0.7},
                        cycle=2.4, ease="none", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_wind_field(uid, p):
    """Campo de vento: linhas de fluxo varrendo a tela."""
    streams, dust = [], []
    for i in range(9):
        y = 130 + i * 100
        d = (f"M-300,{y} C300,{y - 60} 700,{y + 60} 1200,{y} "
             f"C1600,{y - 50} 1900,{y + 40} 2300,{y - 10}")
        streams.append(f'<path class="wd-s" d="{d}" fill="none" stroke="{CYAN}" '
                       f'stroke-width="{5 if i % 2 else 7}" opacity="0.4" '
                       f'stroke-linecap="round"/>')
    for i in range(10):
        y = 170 + i * 90
        dust.append(f'<circle class="wd-d" cx="-60" cy="{y}" r="3" fill="{WHITE}" opacity="0.5"/>')
    arrows = []
    for i in range(7):
        x = 280 + (i % 4) * 420
        y = 250 + (i // 4) * 410 + (i % 2) * 70
        arrows.append(f'<path class="wd-a" d="M{x - 70},{y - 28} L{x},{y} '
                      f'L{x - 70},{y + 28}" fill="none" stroke="{CYAN}" '
                      f'stroke-width="13" stroke-linecap="round" stroke-linejoin="round" '
                      f'opacity="0.65"/>')
    inner = (f'<g class="wd-streams">{"".join(streams)}</g>'
             f'<g class="wd-arrows">{"".join(arrows)}</g>'
             f'<g class="wd-dust">{"".join(dust)}</g>')
    anims = []
    for i in range(9):
        anims.append(_A(f".wd-s:nth-child({i + 1})", "mg_loop", delay=(i * 0.4) % 3.0,
                        frm={"x": 0, "opacity": 0.2}, to={"x": 340, "opacity": 0.55},
                        cycle=3.0 + i * 0.2, ease="sine.inOut", yoyo=True))
    for i in range(10):
        anims.append(_A(f".wd-d:nth-child({i + 1})", "mg_loop", delay=(i * 0.3) % 3.4,
                        frm={"x": 0, "opacity": 0}, to={"x": 2100, "opacity": 0.6},
                        cycle=3.4, ease="none", yoyo=False))
    for i in range(7):
        anims.append(_A(f".wd-a:nth-child({i + 1})", "mg_loop", delay=(i * 0.17) % 0.8,
                        frm={"x": -120, "opacity": 0.15}, to={"x": 200, "opacity": 0.8},
                        cycle=2.2, ease="power1.inOut", yoyo=True))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_ocean_depth(uid, p):
    """Corte do oceano: superfície, falha no fundo e a onda nascendo."""
    ticks = []
    for i in range(11):
        y = 240 + i * 76
        ticks.append(f'<line x1="60" y1="{y}" x2="{120 if i % 5 else 170}" y2="{y}" '
                     f'stroke="{INK}" stroke-width="2" opacity="0.5"/>')
        ticks.append(f'<text x="185" y="{y + 7}" fill="{INK}" font-size="24" '
                     f'font-family="Nunito,sans-serif" opacity="0.55">{i * 1000}</text>')
    inner = (
        f'<rect x="0" y="220" width="1920" height="860" fill="#061423" opacity="0.7"/>'
        f'<path d="{_wave(220, 16, 240, 0)} L2180,0 L-260,0 Z" fill="#082033" '
        f'opacity="0.9"/>'
        f'<path class="o-s" d="{_wave(240, 10, 200, 1)}" fill="none" stroke="{CYAN}" '
        f'stroke-width="4" opacity="0.6"/>'
        f'<line x1="0" y1="980" x2="1920" y2="980" stroke="{INK}" stroke-width="6" '
        f'opacity="0.4"/>'
        f'<path d="M760,980 L860,930 L940,980 L1040,910 L1140,980 L1240,940 L1320,980" '
        f'fill="none" stroke="{RED}" stroke-width="5" opacity="0.8"/>'
        f'<g transform="translate(1040,955)">'
        f'<ellipse class="o-r" rx="50" ry="14" fill="none" stroke="{AMBER}" stroke-width="4"/>'
        f'<ellipse class="o-r" rx="50" ry="14" fill="none" stroke="{AMBER}" stroke-width="3"/>'
        f'<ellipse class="o-r" rx="50" ry="14" fill="none" stroke="{AMBER}" stroke-width="2"/></g>'
        f'<path class="o-col" d="M1040,955 L1040,250" stroke="{AMBER}" stroke-width="8" '
        f'opacity="0.5"/>'
        f'{"".join(ticks)}')
    anims = [
        _A(".o-s", "mg_loop", frm={"x": 0}, to={"x": -240}, cycle=5.0, ease="none", yoyo=False),
        _A(".o-col", "mg_loop", frm={"scaleY": 0.2, "opacity": 0.15},
           to={"scaleY": 1, "opacity": 0.6}, cycle=2.0, ease="sine.inOut", yoyo=True,
           origin="1040 955"),
    ]
    for i in range(3):
        anims.append(_A(f".o-r:nth-child({i + 1})", "mg_loop", delay=i * 0.6,
                        frm={"scale": 0.3, "opacity": 0.9}, to={"scale": 3, "opacity": 0},
                        cycle=1.9, ease="power1.out", yoyo=False))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_globe_grid(uid, p):
    """Globo wireframe girando (abertura / genérico)."""
    lats = [(-0.62, 300), (-0.32, 420), (0.0, 470), (0.32, 420), (0.62, 300)]
    lat_svg = "".join(
        f'<ellipse cx="960" cy="{540 + f * 470:.0f}" rx="{rx}" ry="26" fill="none" '
        f'stroke="{CYAN}" stroke-width="2.5" opacity="0.4"/>' for f, rx in lats)
    longs = []
    for i in range(6):
        longs.append(f'<ellipse class="g-l" cx="960" cy="540" rx="{[470,380,230,60][i % 4] if i < 4 else 330}" '
                     f'ry="470" fill="none" stroke="{CYAN}" stroke-width="2.5" opacity="0.4"/>')
    dots = []
    for i in range(16):
        a = i * 1.7
        r = 120 + (i * 89) % 330
        dots.append(f'<circle class="g-d" cx="{960 + math.cos(a) * r:.0f}" '
                    f'cy="{540 + math.sin(a) * r * 0.9:.0f}" r="4" fill="{WHITE}" opacity="0.6"/>')
    inner = (
        f'<circle cx="960" cy="540" r="470" fill="#05101f" stroke="{BLUE}" '
        f'stroke-width="4" opacity="0.9"/>'
        f'{lat_svg}<g class="g-longs">{"".join(longs)}</g>'
        f'<g class="g-dots">{"".join(dots)}</g>')
    anims = []
    for i in range(6):
        anims.append(_A(f".g-l:nth-child({i + 1})", "mg_loop",
                        frm={"scaleX": 1}, to={"scaleX": -1},
                        cycle=5.0, ease="sine.inOut", yoyo=False, origin="960 540"))
    for i in range(16):
        anims.append(_A(f".g-d:nth-child({i + 1})", "mg_loop", delay=(i * 0.25) % 1.8,
                        frm={"opacity": 0.2}, to={"opacity": 1},
                        cycle=1.8, ease="sine.inOut", yoyo=True))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_star_glow(uid, p):
    """Estrela em movimento: núcleo pulsante, coroa, granulada e corpos orbitando."""
    cor = p.get("cor") or "#ffd84a"
    cx, cy, R = 960, 520, 250
    gran = []
    for i in range(22):
        a = i * 2.399
        rr = (i * 53) % int(R * 0.8)
        gx = cx + math.cos(a) * rr
        gy = cy + math.sin(a) * rr
        gran.append(f'<circle class="sg-g" cx="{gx:.0f}" cy="{gy:.0f}" '
                    f'r="{8 + i % 14}" fill="#ffffff" opacity="0.14"/>')
    orbit = []
    for i in range(3):
        orbit.append(f'<circle class="sg-o" cx="{cx + 360 + i * 70}" cy="{cy}" r="{5 + i * 2}" '
                     f'fill="{WHITE}" opacity="0.9"/>')
    rays = []
    for i in range(16):
        a = 2 * math.pi * i / 16
        rays.append(f'<line class="sg-ray" x1="{cx + math.cos(a) * (R + 40):.0f}" '
                    f'y1="{cy + math.sin(a) * (R + 40):.0f}" '
                    f'x2="{cx + math.cos(a) * (R + 130):.0f}" '
                    f'y2="{cy + math.sin(a) * (R + 130):.0f}" stroke="{cor}" '
                    f'stroke-width="5" stroke-linecap="round" opacity="0.4"/>')
    inner = (
        f'<defs><radialGradient id="{uid}sg" cx="42%" cy="38%" r="72%">'
        f'<stop offset="0" stop-color="#ffffff"/><stop offset="0.5" stop-color="{cor}"/>'
        f'<stop offset="1" stop-color="{cor}" stop-opacity="0.7"/></radialGradient>'
        f'<radialGradient id="{uid}co" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0.55" stop-color="{cor}" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="{cor}" stop-opacity="0"/></radialGradient></defs>'
        f'<g class="sg-rays">{"".join(rays)}</g>'
        f'<circle class="sg-co" cx="{cx}" cy="{cy}" r="{R + 170}" fill="url(#{uid}co)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#{uid}sg)"/>'
        f'<g class="sg-gran">{"" .join(gran)}</g>'
        f'<g class="sg-orbit">{"".join(orbit)}</g>')
    anims = [
        _A(".sg-co", "mg_loop", frm={"scale": 0.92, "opacity": 0.65},
           to={"scale": 1.12, "opacity": 1}, cycle=1.5, ease="sine.inOut", yoyo=True,
           origin=f"{cx} {cy}"),
        _A(".sg-rays", "mg_loop", frm={"rotate": 0}, to={"rotate": 360}, cycle=20,
           ease="none", yoyo=False, origin=f"{cx} {cy}"),
        _A(".sg-orbit", "mg_loop", frm={"rotate": 0}, to={"rotate": 360}, cycle=8,
           ease="none", yoyo=False, origin=f"{cx} {cy}"),
    ]
    for i in range(22):
        anims.append(_A(f".sg-g:nth-child({i + 1})", "mg_loop", delay=(i * 0.1) % 1.4,
                        frm={"opacity": 0.05}, to={"opacity": 0.32},
                        cycle=1.4, ease="sine.inOut", yoyo=True))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_hr_diagram(uid, p):
    """Diagrama HR: estrelas quentes/luminosas à esquerda e frias/tênues à direita."""
    x0, x1, y0, y1 = 260, 1700, 180, 900
    dots = []
    sequence_colors = ("#69b7ff", "#eaf4ff", "#ffe277", "#ffa94f", "#ee6755")
    for i in range(46):
        t = i / 45
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * (0.15 + 0.75 * t) + (i % 5 - 2) * 16
        color = sequence_colors[min(len(sequence_colors) - 1, int(t * len(sequence_colors)))]
        dots.append(f'<circle class="hr-d" cx="{x:.0f}" cy="{y:.0f}" r="{5 + i % 4}" '
                    f'fill="{color}" opacity="0.75"/>')
    giants = []
    for i in range(10):
        x = x0 + (x1 - x0) * (0.35 + 0.06 * i)
        y = y0 + 90 + (i % 3) * 40
        giants.append(f'<circle class="hr-g" cx="{x:.0f}" cy="{y:.0f}" r="{8 + i % 5}" '
                      f'fill="{AMBER}" opacity="0.85"/>')
    dwarfs = []
    for i in range(10):
        x = x0 + (x1 - x0) * (0.2 + 0.05 * i)
        y = y1 - 60 - (i % 3) * 30
        dwarfs.append(f'<circle class="hr-w" cx="{x:.0f}" cy="{y:.0f}" r="{4 + i % 3}" '
                      f'fill="{WHITE}" opacity="0.85"/>')
    inner = (
        f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{INK}" stroke-width="4" '
        f'opacity="0.6"/>'
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{INK}" stroke-width="4" '
        f'opacity="0.6"/>'
        f'<text x="{(x0 + x1) / 2:.0f}" y="990" text-anchor="middle" fill="{INK}" '
        f'font-family="Nunito,sans-serif" font-size="30" opacity="0.7">'
        f'QUENTE  ←   TEMPERATURA   →  FRIO</text>'
        f'<text x="{x0 - 40}" y="{(y0 + y1) / 2:.0f}" text-anchor="middle" fill="{INK}" '
        f'font-family="Nunito,sans-serif" font-size="30" opacity="0.7" '
        f'transform="rotate(-90 {x0 - 40} {(y0 + y1) / 2:.0f})">LUMINOSIDADE</text>'
        f'<path class="hr-ms" d="M{x0 + 60},{y0 + 120} L{x1 - 200},{y1 - 40}" fill="none" '
        f'stroke="{CYAN}" stroke-width="6" opacity="0.35" stroke-linecap="round"/>'
        f'<g class="hr-dots">{"".join(dots)}</g>'
        f'<g class="hr-giants">{"".join(giants)}</g>'
        f'<g class="hr-dwarfs">{"".join(dwarfs)}</g>')
    anims = [_A(".hr-ms", "mg_loop", frm={"opacity": 0.2}, to={"opacity": 0.55},
                cycle=1.6, ease="sine.inOut", yoyo=True)]
    for i in range(46):
        anims.append(_A(f".hr-d:nth-child({i + 1})", "mg_loop", delay=(i * 0.08) % 1.6,
                        frm={"opacity": 0.3, "scale": 0.6}, to={"opacity": 1, "scale": 1.5},
                        cycle=1.6, ease="sine.inOut", yoyo=True))
    for i in range(10):
        anims.append(_A(f".hr-g:nth-child({i + 1})", "mg_loop", delay=(i * 0.12) % 1.3,
                        frm={"opacity": 0.5, "scale": 0.7}, to={"opacity": 1, "scale": 1.35},
                        cycle=1.3, ease="sine.inOut", yoyo=True))
    for i in range(10):
        anims.append(_A(f".hr-w:nth-child({i + 1})", "mg_loop", delay=(i * 0.14) % 1.5,
                        frm={"opacity": 0.4, "scale": 0.7}, to={"opacity": 1, "scale": 1.35},
                        cycle=1.5, ease="sine.inOut", yoyo=True))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


def scene_star_warp(uid, p):
    """Warp de estrelas (genérico astro)."""
    rays = []
    n = 48
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 960 + math.cos(a) * 60
        y = 540 + math.sin(a) * 60
        x2 = 960 + math.cos(a) * 90
        y2 = 540 + math.sin(a) * 90
        rays.append(f'<line class="p-w" x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" '
                    f'y2="{y2:.0f}" stroke="{WHITE}" stroke-width="4" stroke-linecap="round" '
                    f'opacity="0"/>')
    inner = (f'<g class="p-all">{"".join(rays)}</g>'
             f'<circle cx="960" cy="540" r="26" fill="{WHITE}" opacity="0.5"/>')
    anims = []
    for i in range(n):
        anims.append(_A(f".p-w:nth-child({i + 1})", "mg_loop", delay=(i * 0.05) % 1.4,
                        frm={"scale": 0.6, "opacity": 0}, to={"scale": 11, "opacity": 0.9},
                        cycle=1.4, ease="power1.in", yoyo=False, origin="960 540"))
    return {"vb": FULL, "mode": "full", "inner": inner, "anims": anims}


# ================================================================ WIDGETS (panel)

def w_speed_gauge(uid, p):
    """Velocímetro com ponteiro e número (km/h)."""
    val = float(p.get("valor", 300))
    maxv = float(p.get("max", 400))
    unit = p.get("unidade", "km/h")
    cx, cy, R = 450, 420, 300
    a0, a1 = 210, -30
    ticks = []
    for i in range(0, 11):
        t = i / 10
        a = math.radians(a0 + (a1 - a0) * t)
        r1, r2 = R - 34, R
        ticks.append(f'<line x1="{cx + math.cos(a) * r1:.0f}" y1="{cy - math.sin(a) * r1:.0f}" '
                     f'x2="{cx + math.cos(a) * r2:.0f}" y2="{cy - math.sin(a) * r2:.0f}" '
                     f'stroke="{INK}" stroke-width="4" opacity="0.6"/>')
    arc = (f'M{cx + math.cos(math.radians(a0)) * R:.0f},'
           f'{cy - math.sin(math.radians(a0)) * R:.0f} '
           f'A{R},{R} 0 1 1 {cx + math.cos(math.radians(a1)) * R:.0f},'
           f'{cy - math.sin(math.radians(a1)) * R:.0f}')
    # a agulha aponta para CIMA em rotate(0); o ângulo do mostrador é θ (a partir de +x,
    # com y para baixo) e a rotação correspondente é (90 - θ)
    rot0 = 90 - a0
    rotv = 90 - (a0 + (a1 - a0) * min(1.0, val / maxv))
    inner = (
        f'<path d="{arc}" fill="none" stroke="{DEEP}" stroke-width="30"/>'
        f'<path d="{arc}" fill="none" stroke="{CYAN}" stroke-width="8" opacity="0.5"/>'
        f'{"".join(ticks)}'
        f'<g class="sp-n" transform="rotate({rot0} {cx} {cy})">'
        f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - R + 20}" stroke="{AMBER}" '
        f'stroke-width="10" stroke-linecap="round"/></g>'
        f'<circle cx="{cx}" cy="{cy}" r="22" fill="{INK}"/>'
        f'<text class="sp-v" x="{cx}" y="{cy + 115}" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="120" font-weight="800">0</text>'
        f'<text x="{cx}" y="{cy + 175}" text-anchor="middle" fill="{CYAN}" '
        f'font-family="Nunito,sans-serif" font-size="46" font-weight="800">{unit}</text>')
    anims = [
        _A(".sp-n", "mg_turn", delay=0.15, frm={"rotate": rot0}, to={"rotate": rotv},
           dur=1.1, ease="power2.out", origin=f"{cx} {cy}"),
        _A(".sp-v", "mg_count", delay=0.15, to=val, dur=1.1),
    ]
    return {"vb": (900, 620), "mode": "panel", "inner": inner, "anims": anims}


def w_magnitude(uid, p):
    """Escala de magnitude horizontal com marcador."""
    val = float(p.get("valor", 7))
    maxv = float(p.get("max", 10))
    unit = p.get("unidade", "")
    w, h = 1500, 420
    x0, x1, y = 150, 1350, 210
    zones = [(0, 2, "#2b6fbf"), (2, 4, "#39d98a"), (4, 6, AMBER), (6, 8, ORANGE), (8, 10, RED)]
    segs = []
    for a, b, col in zones:
        xa = x0 + (x1 - x0) * a / maxv
        xb = x0 + (x1 - x0) * b / maxv
        segs.append(f'<rect x="{xa:.0f}" y="{y}" width="{xb - xa:.0f}" height="40" '
                    f'fill="{col}" opacity="0.55"/>')
    ticks = []
    step = max(1, int(math.ceil(maxv / 10.0)))
    for i in range(0, int(maxv) + 1, step):
        x = x0 + (x1 - x0) * i / maxv
        ticks.append(f'<line x1="{x:.0f}" y1="{y + 40}" x2="{x:.0f}" y2="{y + 66}" '
                     f'stroke="{INK}" stroke-width="3" opacity="0.6"/>'
                     f'<text x="{x:.0f}" y="{y + 106}" text-anchor="middle" fill="{INK}" '
                     f'font-family="Nunito,sans-serif" font-size="30" opacity="0.75">{i}</text>')
    mx = x0 + (x1 - x0) * min(1.0, val / maxv)
    inner = (
        f'{"".join(segs)}'
        f'<line x1="{x0}" y1="{y + 20}" x2="{x1}" y2="{y + 20}" stroke="{INK}" '
        f'stroke-width="2" opacity="0.4"/>'
        f'{"".join(ticks)}'
        f'<g class="mg-mk" transform="translate({mx:.0f},0)">'
        f'<path d="M-22,{y - 40} L22,{y - 40} L0,{y - 4} Z" fill="{AMBER}"/>'
        f'<line x1="0" y1="{y - 40}" x2="0" y2="{y + 40}" stroke="{AMBER}" '
        f'stroke-width="6"/></g>'
        f'<text class="mg-v" x="750" y="120" text-anchor="middle" fill="{AMBER}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="110" font-weight="800">0</text>')
    anims = [
        _A(".mg-mk", "mg_once", delay=0.15, frm={"x": 0}, to={"x": mx - x0},
           dur=1.0, ease="power2.out"),
        _A(".mg-v", "mg_count", delay=0.15, to=val, dur=1.0),
    ]
    return {"vb": (w, h), "mode": "panel", "inner": inner, "anims": anims}


def w_thermometer(uid, p):
    """Termômetro vertical com preenchimento e valor (graus)."""
    val = float(p.get("valor", 1000))
    maxv = float(p.get("max", 1500))
    unit = p.get("unidade", "graus")
    w, h = 520, 900
    tx, ty0, ty1, tw = 220, 120, 740, 62
    pct = min(1.0, val / maxv)
    fy = ty1 - (ty1 - ty0) * pct
    ticks = []
    for i in range(0, 6):
        yy = ty1 - (ty1 - ty0) * i / 5
        ticks.append(f'<line x1="{tx + tw + 16}" y1="{yy:.0f}" x2="{tx + tw + 70}" '
                     f'y2="{yy:.0f}" stroke="{INK}" stroke-width="3" opacity="0.6"/>')
        ticks.append(f'<text x="{tx + tw + 84}" y="{yy + 8:.0f}" fill="{INK}" '
                     f'font-size="26" font-family="Nunito,sans-serif" opacity="0.7">'
                     f'{int(maxv * i / 5)}</text>')
    inner = (
        f'<rect x="{tx}" y="{ty0}" width="{tw}" height="{ty1 - ty0}" rx="{tw // 2}" '
        f'fill="#0a1a2e" stroke="{BLUE}" stroke-width="4"/>'
        f'<rect class="th-f" x="{tx + 8}" y="{ty0 + 8}" width="{tw - 16}" '
        f'height="{ty1 - ty0 - 16}" rx="{tw // 2}" fill="url(#{uid}th)"/>'
        f'<circle cx="{tx + tw // 2}" cy="{ty1 + 60}" r="70" fill="#0a1a2e" '
        f'stroke="{BLUE}" stroke-width="4"/>'
        f'<circle cx="{tx + tw // 2}" cy="{ty1 + 60}" r="50" fill="url(#{uid}th)"/>'
        f'{"".join(ticks)}'
        f'<defs><linearGradient id="{uid}th" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{RED}"/><stop offset="0.6" stop-color="{ORANGE}"/>'
        f'<stop offset="1" stop-color="{AMBER}"/></linearGradient></defs>'
        f'<text class="th-v" x="{tx - 120}" y="240" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="96" font-weight="800">0</text>'
        f'<text x="{tx - 120}" y="300" text-anchor="middle" fill="{AMBER}" '
        f'font-family="Nunito,sans-serif" font-size="40" font-weight="800">{unit}</text>')
    anims = [
        _A(".th-f", "mg_grow_y", delay=0.15, frm={"scaleY": 0}, to={"scaleY": 1},
           dur=1.2, ease="power2.out", origin=f"{tx + tw // 2} {ty1}"),
        _A(".th-v", "mg_count", delay=0.15, to=val, dur=1.2),
    ]
    return {"vb": (w, h), "mode": "panel", "inner": inner, "anims": anims}


def w_pct_ring(uid, p):
    """Anel de porcentagem com número no centro."""
    val = float(p.get("valor", 90))
    R = 200
    circ = 2 * math.pi * R
    inner = (
        f'<g transform="translate(280,270) rotate(-90)">'
        f'<circle r="{R}" fill="none" stroke="{DEEP}" stroke-width="42"/>'
        f'<circle class="pc-f" r="{R}" fill="none" stroke="{CYAN}" stroke-width="42" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" '
        f'stroke-dashoffset="{circ:.1f}"/></g>'
        f'<text class="pc-v" x="280" y="290" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="130" font-weight="800">0%</text>')
    anims = [
        _A(".pc-f", "mg_once", delay=0.15, frm={"strokeDashoffset": circ},
           to={"strokeDashoffset": circ * (1 - min(1.0, val / 100))}, dur=1.2,
           ease="power2.out"),
        _A(".pc-v", "mg_count", delay=0.15, to=val, dur=1.2, suffix="%"),
    ]
    return {"vb": (560, 560), "mode": "panel", "inner": inner, "anims": anims}


def w_area(uid, p):
    """Contador de área (hectares): grade que preenche + número."""
    val = float(p.get("valor", 5000))
    cols, rows, s, gap = 12, 6, 84, 14
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append(f'<rect class="ac-c" x="{40 + c * (s + gap)}" y="{90 + r * (s + gap)}" '
                         f'width="{s}" height="{s}" rx="8" fill="{AMBER}" opacity="0"/>')
    inner = (
        f'{"".join(cells)}'
        f'<text class="ac-v" x="40" y="70" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="64" font-weight="800">0</text>'
        f'<text x="360" y="70" fill="{AMBER}" font-family="Nunito,sans-serif" '
        f'font-size="40" font-weight="800">hectares</text>')
    anims = [_A(".ac-v", "mg_count", delay=0.1, to=val, dur=1.1, prefix="")]
    step = 0.9 / (cols * rows)
    for i in range(cols * rows):
        anims.append(_A(f".ac-c:nth-child({i + 1})", "mg_once", delay=0.1 + i * step,
                        frm={"opacity": 0, "scale": 0.4}, to={"opacity": 0.9, "scale": 1},
                        dur=0.25, ease="back.out(2)"))
    return {"vb": (1240, 700), "mode": "panel", "inner": inner, "anims": anims}


def w_distance(uid, p):
    """Régua de distância entre dois pontos (km)."""
    val = p.get("texto", "")
    inner = (
        f'<line class="ds-l" x1="120" y1="220" x2="1380" y2="220" stroke="{CYAN}" '
        f'stroke-width="6" stroke-linecap="round" pathLength="1" '
        f'style="stroke-dasharray:1;stroke-dashoffset:1"/>'
        f'<circle cx="120" cy="220" r="18" fill="{CYAN}"/>'
        f'<circle cx="1380" cy="220" r="18" fill="{AMBER}"/>'
        f'<line x1="120" y1="160" x2="120" y2="280" stroke="{INK}" stroke-width="4" opacity="0.6"/>'
        f'<line x1="1380" y1="160" x2="1380" y2="280" stroke="{INK}" stroke-width="4" opacity="0.6"/>'
        f'<path class="ds-a" d="M700,110 L740,80 L780,110 Z" fill="{AMBER}" opacity="0"/>'
        f'<text class="ds-v" x="750" y="360" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="96" font-weight="800">'
        f'{val}</text>')
    anims = [
        _A(".ds-l", "mg_draw", delay=0.1, dur=1.0, ease="power2.out"),
        _A(".ds-a", "mg_once", delay=0.9, frm={"opacity": 0, "y": 20},
           to={"opacity": 1, "y": 0}, dur=0.3, ease="back.out(2)"),
        _A(".ds-v", "mg_once", delay=0.9, frm={"opacity": 0, "y": 20},
           to={"opacity": 1, "y": 0}, dur=0.35, ease="power2.out"),
    ]
    return {"vb": (1500, 420), "mode": "panel", "inner": inner, "anims": anims}


def w_size_compare(uid, p):
    """Comparação de tamanho: círculos em escala relativa (sem objetos cartoon)."""
    itens = p.get("itens") or []
    if not itens:
        itens = [{"rotulo": "menor", "escala": 0.3, "cor": CYAN},
                 {"rotulo": "maior", "escala": 1.0, "cor": AMBER}]
    base = 320.0
    base_y = 620.0
    gap = 60
    cell = max(base * float(it.get("escala", 1)) for it in itens)
    n = len(itens)
    total_w = n * cell + (n - 1) * gap
    x0 = 40.0  # margem do viewBox; total_w/2 deslocava metade do gráfico para fora
    circles, labels = [], []
    for i, it in enumerate(itens):
        r = base * float(it.get("escala", 1)) / 2
        cx = x0 + i * (cell + gap) + cell / 2
        col = it.get("cor") or CYAN
        circles.append(f'<circle class="sc-c" cx="{cx:.0f}" cy="{base_y - r:.0f}" r="{r:.0f}" '
                       f'fill="url(#{uid}sc)" stroke="{col}" stroke-width="4"/>')
        labels.append(f'<text x="{cx:.0f}" y="{base_y + 54:.0f}" text-anchor="middle" '
                      f'fill="{WHITE}" font-family="Baloo 2,Nunito,sans-serif" '
                      f'font-size="34" font-weight="800">{it.get("rotulo", "")}</text>')
    inner = (
        f'<defs><radialGradient id="{uid}sc" cx="40%" cy="36%" r="72%">'
        f'<stop offset="0" stop-color="{WHITE}"/><stop offset="1" stop-color="{BLUE}"/>'
        f'</radialGradient></defs>'
        f'<g class="sc-circles">{"".join(circles)}</g>{"".join(labels)}')
    anims = []
    for i, it in enumerate(itens):
        anims.append(_A(f".sc-c:nth-child({i + 1})", "mg_once", delay=0.15 + i * 0.22,
                        frm={"scale": 0.12, "opacity": 0}, to={"scale": 1, "opacity": 1},
                        dur=0.5, ease="back.out(1.5)"))
    return {"vb": (int(total_w) + 80, 760), "mode": "panel", "inner": inner, "anims": anims}


def w_k_scale(uid, p):
    """Escala de temperatura em Kelvin com marcador."""
    val = float(p.get("valor", 3000))
    minv = float(p.get("min", 0))
    maxv = float(p.get("max", 50000))
    x0, x1, y = 140, 1360, 200
    pct = max(0.0, min(1.0, (val - minv) / max((maxv - minv), 1)))
    mx = x0 + (x1 - x0) * pct
    ticks = []
    for i in range(6):
        xv = x0 + (x1 - x0) * i / 5
        lab = f"{int(minv + (maxv - minv) * i / 5):,}".replace(",", ".")
        ticks.append(f'<line x1="{xv:.0f}" y1="{y + 44}" x2="{xv:.0f}" y2="{y + 70}" '
                     f'stroke="{INK}" stroke-width="3" opacity="0.6"/>')
        ticks.append(f'<text x="{xv:.0f}" y="{y + 110}" text-anchor="middle" fill="{INK}" '
                     f'font-size="28" font-family="Nunito,sans-serif" opacity="0.7">'
                     f'{lab}</text>')
    inner = (
        f'<defs><linearGradient id="{uid}ks" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{RED}"/><stop offset="0.3" stop-color="{AMBER}"/>'
        f'<stop offset="0.55" stop-color="#fff3c0"/><stop offset="0.75" stop-color="#dbe9fb"/>'
        f'<stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>'
        f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="44" rx="22" '
        f'fill="url(#{uid}ks)" opacity="0.85"/>'
        f'{"".join(ticks)}'
        f'<g class="ks-mk" transform="translate({mx:.0f},0)">'
        f'<path d="M-20,{y - 34} L20,{y - 34} L0,{y - 2} Z" fill="{WHITE}"/>'
        f'<line x1="0" y1="{y - 34}" x2="0" y2="{y + 44}" stroke="{WHITE}" stroke-width="6"/>'
        f'</g>'
        f'<text class="ks-v" x="750" y="120" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="104" font-weight="800">0</text>'
        f'<text x="960" y="120" text-anchor="middle" fill="{CYAN}" '
        f'font-family="Nunito,sans-serif" font-size="48" font-weight="800">K</text>')
    anims = [
        _A(".ks-mk", "mg_once", delay=0.15, frm={"x": 0}, to={"x": mx - x0},
           dur=1.0, ease="power2.out"),
        _A(".ks-v", "mg_count", delay=0.15, to=val, dur=1.0),
    ]
    return {"vb": (1500, 420), "mode": "panel", "inner": inner, "anims": anims}


def w_duration(uid, p):
    """Barra de duração com marcos (minutos / semanas)."""
    val = p.get("texto", "")
    inner = (
        f'<rect x="120" y="190" width="1260" height="60" rx="30" fill="{DEEP}"/>'
        f'<rect class="du-f" x="120" y="190" width="1260" height="60" rx="30" '
        f'fill="{CYAN}" style="transform-origin:120px 220px"/>'
        f'<text class="du-v" x="750" y="150" text-anchor="middle" fill="{WHITE}" '
        f'font-family="Baloo 2,Nunito,sans-serif" font-size="90" font-weight="800">'
        f'{val}</text>')
    anims = [_A(".du-f", "mg_bar", delay=0.1, dur=1.1, ease="power2.out")]
    return {"vb": (1500, 300), "mode": "panel", "inner": inner, "anims": anims}


# ================================================================ registro

RECIPES = {
    # cenas
    "vortex": scene_vortex, "spiral_storm": scene_spiral_storm, "seismic": scene_seismic,
    "wave_stack": scene_wave_stack, "wildfire": scene_wildfire, "water_rise": scene_water_rise,
    "drought": scene_drought, "snowstorm": scene_snowstorm, "volcano": scene_volcano,
    "wind_field": scene_wind_field, "ocean_depth": scene_ocean_depth,
    "globe_grid": scene_globe_grid, "star_warp": scene_star_warp,
    "star_glow": scene_star_glow, "hr_diagram": scene_hr_diagram,
    # widgets
    "speed_gauge": w_speed_gauge, "magnitude_scale": w_magnitude, "thermometer": w_thermometer,
    "pct_ring": w_pct_ring, "area_counter": w_area, "distance_ruler": w_distance,
    "duration_bar": w_duration, "size_compare": w_size_compare, "k_scale": w_k_scale,
}


def has(recipe: str) -> bool:
    return recipe in RECIPES


def is_full(recipe: str) -> bool:
    return recipe in RECIPES and RECIPES[recipe].__name__.startswith("scene_")


def build(recipe: str, uid: str, params: dict | None = None) -> dict:
    fn = RECIPES.get(recipe)
    if not fn:
        return {}
    return fn(uid, params or {})


def catalog() -> str:
    scenes = [k for k in RECIPES if is_full(k)]
    widgets = [k for k in RECIPES if not is_full(k)]
    return (f"{len(scenes)} cenas: " + ", ".join(sorted(scenes)) +
            f"\n{len(widgets)} widgets: " + ", ".join(sorted(widgets)))


if __name__ == "__main__":
    print(catalog())
