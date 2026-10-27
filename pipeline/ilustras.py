# -*- coding: utf-8 -*-
"""
ilustras.py — biblioteca de ilustrações SVG no estilo da referência (flat vector
cartoon, contorno grosso, cor saturada, fundo transparente).

Tudo é gerado por código: nada de baixar arte de terceiros. Cada objeto tem um `id`
(ex.: "red_dwarf", "hourglass") e a biblioteca resolve por id ou por sinônimo.

Uso:
  from ilustras import render
  svg = render("red_dwarf", size=720)

  python pipeline/ilustras.py --list
  python pipeline/ilustras.py red_dwarf --out /tmp/a.svg --size 720
"""
from __future__ import annotations

import hashlib
import math
from xml.sax.saxutils import escape

INK = "#0b1420"          # contorno
VB = 400                 # viewBox padrão (quadrado)


def _rng(seed: str):
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    state = h or 1

    def nxt():
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF

    return nxt


def _svg(body: str, w: int = VB, h: int = VB, size: int | None = None) -> str:
    dim = f'width="{size}" height="{size}" ' if size else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" {dim}viewBox="0 0 {w} {h}" '
            f'preserveAspectRatio="xMidYMid meet">{body}</svg>')


def _blob(cx, cy, rx, ry, rot, rnd, wob=0.18):
    pts = []
    steps = 18
    for i in range(steps):
        a = 2 * math.pi * i / steps
        r = 1 + (rnd() - 0.5) * 2 * wob
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, steps + 1):
        p, q = pts[(i - 1) % steps], pts[i % steps]
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        d += f" Q{p[0]:.1f},{p[1]:.1f} {mx:.1f},{my:.1f}"
    return d + " Z"


# --------------------------------------------------------------------------- estrelas

def star_ball(base="#e8402a", mid="#f06a3a", light="#ffb37a", spot="#a81c12",
              glow="#ff6a3c", spikes=0, rays=0, asteroids=0, ring=False,
              seed="s", core=False, size: int | None = None) -> str:
    """Bola estelar cartoon parametrizável (base de quase todos os 'tipos de estrela')."""
    rnd = _rng(seed)
    c, r = 200, 118
    g = [f'<defs>',
         f'<radialGradient id="g_{seed}" cx="38%" cy="34%" r="78%">',
         f'<stop offset="0%" stop-color="{light}"/><stop offset="46%" stop-color="{mid}"/>',
         f'<stop offset="100%" stop-color="{base}"/></radialGradient>',
         f'<radialGradient id="gl_{seed}" cx="50%" cy="50%" r="50%">',
         f'<stop offset="62%" stop-color="{glow}" stop-opacity="0.55"/>',
         f'<stop offset="100%" stop-color="{glow}" stop-opacity="0"/></radialGradient>',
         f'<clipPath id="c_{seed}"><circle cx="{c}" cy="{c}" r="{r}"/></clipPath>',
         '</defs>']

    if spikes:
        pts = []
        for i in range(spikes * 2):
            a = math.pi * i / spikes - math.pi / 2
            rad = r + 76 if i % 2 == 0 else r + 22
            pts.append(f"{c + math.cos(a)*rad:.1f},{c + math.sin(a)*rad:.1f}")
        g.append(f'<polygon points="{" ".join(pts)}" fill="{glow}" opacity="0.30"/>')

    if rays:
        for i in range(rays):
            a = 2 * math.pi * i / rays
            x1, y1 = c + math.cos(a) * (r + 8), c + math.sin(a) * (r + 8)
            x2, y2 = c + math.cos(a) * (r + 62), c + math.sin(a) * (r + 62)
            wd = 10 if i % 2 == 0 else 6
            g.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{glow}" stroke-width="{wd}" stroke-linecap="round" opacity="0.85"/>')

    g.append(f'<circle cx="{c}" cy="{c}" r="{r+30}" fill="url(#gl_{seed})"/>')
    g.append(f'<circle cx="{c}" cy="{c}" r="{r}" fill="url(#g_{seed})" stroke="{INK}" stroke-width="6"/>')

    spots = f'<g clip-path="url(#c_{seed})">'
    counts = 3 if core else 7
    for i in range(counts):
        ax, ay = rnd(), rnd()
        sx = c + (ax - 0.5) * 2 * r * 0.72
        sy = c + (ay - 0.5) * 2 * r * 0.72
        rr = (0.08 + rnd() * 0.16) * r
        spots += f'<path d="{_blob(sx, sy, rr*1.25, rr, 0, rnd, .25)}" fill="{spot}" opacity="0.72"/>'
    spots += '</g>'
    g.append(spots)

    if ring:
        g.append(f'<ellipse cx="{c}" cy="{c}" rx="{r+130}" ry="{r*0.30}" fill="none" '
                 f'stroke="{glow}" stroke-width="10" opacity="0.5" transform="rotate(-16 {c} {c})"/>')
    for _ in range(asteroids):
        ax = c + (rnd() - 0.5) * 660
        ay = c + (rnd() - 0.5) * 660
        s = 6 + rnd() * 9
        g.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="{s:.0f}" fill="{base}" '
                 f'stroke="{INK}" stroke-width="3"/>')
    return _svg("".join(g), size=size)


def _star(name: str, **kw):
    return lambda size=None: star_ball(seed=name, size=size, **kw)


def burst(color="#7fd4ff", n=16, size=None) -> str:
    """Explosão/supernova."""
    rnd = _rng("burst" + color)
    c = 200
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        rad = 195 if i % 2 == 0 else 70 + rnd() * 30
        pts.append(f"{c+math.cos(a)*rad:.1f},{c+math.sin(a)*rad:.1f}")
    body = (f'<polygon points="{" ".join(pts)}" fill="{color}" stroke="{INK}" stroke-width="5"/>'
            f'<circle cx="{c}" cy="{c}" r="46" fill="#fff" opacity=".9"/>')
    return _svg(body, size=size)


# --------------------------------------------------------------------------- props

def _prop(body, w=VB, h=VB, size=None):
    return _svg(body, w, h, size)


def hourglass(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="96" y="46" width="208" height="30" rx="14" fill="#b5763c"/>'
         f'<rect x="96" y="324" width="208" height="30" rx="14" fill="#b5763c"/>'
         f'<rect x="112" y="76" width="18" height="248" fill="#d79a5a"/>'
         f'<rect x="270" y="76" width="18" height="248" fill="#d79a5a"/>'
         f'<path d="M124 88 H276 L210 200 L276 312 H124 L190 200 Z" fill="#eef6fb" opacity=".95"/>'
         f'<path d="M148 300 L252 300 L206 214 Z" fill="#f2c86a"/>'
         f'<path d="M182 190 L218 190 L200 120 Z" fill="#f2c86a"/>'
         f'<line x1="200" y1="206" x2="200" y2="292" stroke="#f2c86a" stroke-width="6"/>'
         f'</g>')
    return _prop(b, size=size)


def spoon(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<ellipse cx="146" cy="250" rx="72" ry="52" fill="#cfd6dd"/>'
         f'<ellipse cx="146" cy="250" rx="52" ry="34" fill="#eef2f6"/>'
         f'<rect x="196" y="228" width="150" height="34" rx="17" fill="#cfd6dd" '
         f'transform="rotate(-18 196 228)"/></g>')
    return _prop(b, size=size)


def scale_balance(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="188" y="120" width="24" height="196" fill="#e8a92c"/>'
         f'<rect x="120" y="316" width="160" height="24" rx="8" fill="#e8a92c"/>'
         f'<rect x="92" y="104" width="216" height="20" rx="8" fill="#e8a92c"/>'
         f'<circle cx="200" cy="100" r="18" fill="#f6c451"/>'
         f'<line x1="112" y1="120" x2="86" y2="196" stroke-linecap="round"/>'
         f'<line x1="112" y1="120" x2="138" y2="196" stroke-linecap="round"/>'
         f'<path d="M74 196 H150 L112 246 Z" fill="#f6c451"/>'
         f'<line x1="288" y1="120" x2="262" y2="196" stroke-linecap="round"/>'
         f'<line x1="288" y1="120" x2="314" y2="196" stroke-linecap="round"/>'
         f'<path d="M250 196 H326 L288 246 Z" fill="#f6c451"/></g>')
    return _prop(b, size=size)


def thermometer(size=None, color="#e8402a"):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="176" y="52" width="48" height="248" rx="24" fill="#eef2f6"/>'
         f'<rect x="190" y="96" width="20" height="180" rx="10" fill="#cfd6dd"/>'
         f'<circle cx="200" cy="322" r="42" fill="#eef2f6"/>'
         f'<circle cx="200" cy="322" r="26" fill="{color}"/>'
         f'<rect x="190" y="150" width="20" height="172" rx="10" fill="{color}"/>'
         f'</g>')
    return _prop(b, size=size)


def canister(size=None, color="#2ea8ff"):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="150" y="96" width="100" height="230" rx="30" fill="#eef2f6"/>'
         f'<rect x="150" y="150" width="100" height="176" rx="26" fill="{color}"/>'
         f'<rect x="178" y="66" width="44" height="36" rx="8" fill="#cfd6dd"/>'
         f'<rect x="168" y="120" width="18" height="150" rx="9" fill="#fff" opacity=".35"/>'
         f'</g>')
    return _prop(b, size=size)


def fuel_gallon(size=None, color="#e8402a"):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="120" y="118" width="150" height="200" rx="18" fill="{color}"/>'
         f'<rect x="150" y="88" width="42" height="36" rx="6" fill="{color}"/>'
         f'<path d="M270 150 h44 v56" fill="none" stroke-linecap="round"/>'
         f'<rect x="146" y="152" width="34" height="120" rx="10" fill="#fff" opacity=".28"/>'
         f'</g>')
    return _prop(b, size=size)


def atom(size=None, color="#3ad07a"):
    b = (f'<g fill="none" stroke="{color}" stroke-width="7">'
         f'<ellipse cx="200" cy="200" rx="150" ry="58"/>'
         f'<ellipse cx="200" cy="200" rx="150" ry="58" transform="rotate(60 200 200)"/>'
         f'<ellipse cx="200" cy="200" rx="150" ry="58" transform="rotate(120 200 200)"/>'
         f'</g><circle cx="200" cy="200" r="34" fill="{color}" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def element_hydrogen(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="112" y="96" width="176" height="220" rx="12" fill="#f7fbff"/>'
         f'<text x="140" y="146" font-family="Arial,Helvetica,sans-serif" font-size="42" '
         f'font-weight="700" fill="{INK}" stroke="none">1</text>'
         f'<text x="212" y="140" font-family="Arial,Helvetica,sans-serif" font-size="26" '
         f'fill="{INK}" stroke="none">1.008</text>'
         f'<text x="200" y="252" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
         f'font-size="130" font-weight="700" fill="{INK}" stroke="none">H</text>'
         f'<text x="200" y="296" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
         f'font-size="26" fill="{INK}" stroke="none">Hydrogen</text></g>')
    flames = ""
    for i, (x, y, s, c) in enumerate([(70, 150, 1.0, "#ff8a2b"), (330, 170, .8, "#ffb02b"),
                                      (300, 320, .9, "#ff8a2b"), (92, 320, .75, "#ffb02b")]):
        flames += (f'<path d="{_blob(x, y, 34*s, 52*s, 0, _rng(f"f{i}"), .22)}" fill="{c}" '
                   f'stroke="{INK}" stroke-width="5" opacity=".95"/>')
    return _prop(flames + b, size=size)


def prism(size=None):
    b = (f'<polygon points="200,80 300,280 100,280" fill="#dfeaf5" stroke="{INK}" stroke-width="7"/>'
         f'<polygon points="200,96 288,272 112,272" fill="#f2f7fc" opacity=".7"/>')
    cols = ["#ff3b30", "#ff9500", "#ffcc00", "#34c759", "#0a84ff", "#5e5ce6"]
    for i, c in enumerate(cols):
        b += (f'<polygon points="252,214 352,{176+i*26} 352,{198+i*26} 268,226" fill="{c}" '
              f'opacity=".92"/>')
    return _prop(b, size=size)


def earth(size=None):
    rnd = _rng("earth")
    land = ""
    for i in range(7):
        x = 200 + (rnd() - .5) * 190
        y = 200 + (rnd() - .5) * 190
        land += f'<path d="{_blob(x, y, 22+rnd()*30, 16+rnd()*22, 0, rnd, .3)}" fill="#4caf50"/>'
    b = (f'<defs><clipPath id="ce"><circle cx="200" cy="200" r="120"/></clipPath></defs>'
         f'<circle cx="200" cy="200" r="120" fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>'
         f'<g clip-path="url(#ce)">{land}'
         f'<ellipse cx="200" cy="200" rx="120" ry="120" fill="#fff" opacity=".10"/></g>')
    return _prop(b, size=size)


def rocket(size=None):
    b = (f'<path d="M200 60 C246 120 252 210 236 286 H164 C148 210 154 120 200 60 Z" '
         f'fill="#f2f6fb" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="168" r="30" fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M164 236 L120 300 L164 288 Z" fill="#e8402a" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M236 236 L280 300 L236 288 Z" fill="#e8402a" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M186 288 h28 l-14 44 Z" fill="#ffb02b" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def telescope(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="120" y="140" width="220" height="66" rx="30" transform="rotate(-22 230 173)" '
         f'fill="#dfeaf5"/>'
         f'<circle cx="312" cy="132" r="30" fill="#2ea8ff" opacity=".85"/>'
         f'<rect x="176" y="196" width="26" height="120" rx="10" fill="#8b97a6"/>'
         f'<line x1="150" y1="330" x2="250" y2="330" stroke-linecap="round"/>'
         f'<line x1="200" y1="240" x2="176" y2="330" stroke-linecap="round"/>'
         f'<line x1="200" y1="240" x2="232" y2="330" stroke-linecap="round"/></g>')
    return _prop(b, size=size)


def lightbulb(size=None):
    b = (f'<path d="M200 60 a92 92 0 0 1 52 168 c-10 8 -14 20 -14 34 h-76 c0-14 -4-26 -14-34 '
         f'A92 92 0 0 1 200 60 Z" fill="#ffe07a" stroke="{INK}" stroke-width="7"/>'
         f'<rect x="164" y="272" width="72" height="26" rx="8" fill="#c9d3dd" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="172" y="300" width="56" height="20" rx="8" fill="#c9d3dd" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M176 210 h48 M180 236 h40" stroke="{INK}" stroke-width="5" fill="none"/>')
    return _prop(b, size=size)


def tape_measure(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<rect x="96" y="150" width="184" height="140" rx="22" fill="#2f3742"/>'
         f'<rect x="120" y="176" width="136" height="88" rx="14" fill="#3d4652"/>'
         f'<rect x="280" y="196" width="180" height="48" rx="10" fill="#ffe07a"/>'
         f'<g stroke="{INK}" stroke-width="4">'
         f'<line x1="312" y1="196" x2="312" y2="222"/><line x1="352" y1="196" x2="352" y2="228"/>'
         f'<line x1="392" y1="196" x2="392" y2="222"/><line x1="432" y1="196" x2="432" y2="228"/>'
         f'</g></g>')
    return _prop(b, size=size)


def arrow_red(size=None):
    b = (f'<path d="M60 200 H280 V150 L360 200 L280 250 V200" fill="#e8402a" '
         f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def check_green(size=None):
    b = (f'<circle cx="200" cy="200" r="128" fill="#2ecc40" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="106" fill="none" stroke="#fff" stroke-width="6" opacity=".85"/>'
         f'<path d="M138 208 L182 252 L266 152" fill="none" stroke="#fff" stroke-width="30" '
         f'stroke-linecap="round" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def cross_red(size=None):
    b = (f'<g stroke="#d81f1f" stroke-width="44" stroke-linecap="round">'
         f'<line x1="120" y1="120" x2="280" y2="280"/><line x1="280" y1="120" x2="120" y2="280"/>'
         f'</g>')
    return _prop(b, size=size)


def thermometer_cold(size=None):
    return thermometer(size=size, color="#2ea8ff")


def gas_giant(size=None):
    rnd = _rng("jupiter")
    bands = ""
    for i, c in enumerate(["#d9b58a", "#c9a06a", "#e8d3ae", "#bf9256", "#e3c79a"]):
        y = 110 + i * 38
        bands += f'<rect x="86" y="{y}" width="228" height="30" fill="{c}"/>'
    b = (f'<defs><clipPath id="cg"><circle cx="200" cy="200" r="114"/></clipPath></defs>'
         f'<circle cx="200" cy="200" r="114" fill="#d9b58a" stroke="{INK}" stroke-width="6"/>'
         f'<g clip-path="url(#cg)">{bands}'
         f'<ellipse cx="160" cy="250" rx="34" ry="20" fill="#b3452e" opacity=".85"/></g>')
    return _prop(b, size=size)


def galaxy(size=None):
    rnd = _rng("galaxy")
    body = ""
    for i in range(4):
        body += (f'<ellipse cx="200" cy="200" rx="{150-i*22}" ry="{54-i*8}" fill="none" '
                 f'stroke="#8f6bff" stroke-width="{7-i}" opacity="{0.5-i*0.08}" '
                 f'transform="rotate({i*30} 200 200)"/>')
    for i in range(60):
        x, y = 200 + (rnd() - .5) * 300, 200 + (rnd() - .5) * 300
        body += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{1.2+rnd()*2:.1f}" fill="#fff" opacity=".8"/>'
    body += f'<circle cx="200" cy="200" r="26" fill="#fff" opacity=".95"/>'
    return _prop(body, size=size)


def nebula(size=None):
    rnd = _rng("nebula")
    body = ""
    for c in ["#ff6ad5", "#7b6bff", "#2ea8ff", "#ff9f4a"]:
        body += f'<path d="{_blob(200+(rnd()-.5)*80, 200+(rnd()-.5)*80, 120+rnd()*40, 90+rnd()*30, 0, rnd, .35)}" fill="{c}" opacity=".38"/>'
    for i in range(40):
        x, y = 200 + (rnd() - .5) * 320, 200 + (rnd() - .5) * 320
        body += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{1+rnd()*2:.1f}" fill="#fff" opacity=".85"/>'
    return _prop(body, size=size)


def moon(size=None):
    rnd = _rng("moon")
    craters = ""
    for i in range(9):
        x, y = 200 + (rnd() - .5) * 170, 200 + (rnd() - .5) * 170
        craters += f'<path d="{_blob(x, y, 10+rnd()*20, 9+rnd()*16, 0, rnd, .3)}" fill="#b9c3cf"/>'
    b = (f'<defs><clipPath id="cm"><circle cx="200" cy="200" r="116"/></clipPath></defs>'
         f'<circle cx="200" cy="200" r="116" fill="#dfe6ee" stroke="{INK}" stroke-width="6"/>'
         f'<g clip-path="url(#cm)">{craters}</g>')
    return _prop(b, size=size)


def mascot(size=None):
    """Polvo astronauta com telescópio — o comentarista do canal (referência)."""
    body = (
        f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
        # tentáculos
        f'<path d="M150 300 C120 360 150 380 176 356 C196 338 190 320 176 316" fill="#7b3fd4"/>'
        f'<path d="M256 302 C292 358 260 384 232 358 C212 340 220 320 236 316" fill="#7b3fd4"/>'
        f'<path d="M200 316 C196 372 224 392 236 366 C244 348 226 334 212 330" fill="#8f52e0"/>'
        # corpo/capacete
        f'<ellipse cx="200" cy="216" rx="86" ry="96" fill="#8f52e0"/>'
        f'<ellipse cx="200" cy="196" rx="66" ry="66" fill="#2a2340"/>'
        f'<ellipse cx="200" cy="200" rx="52" ry="52" fill="#e8d9ff" stroke-width="4"/>'
        f'<circle cx="182" cy="196" r="14" fill="#1b1730" stroke="none"/>'
        f'<circle cx="220" cy="196" r="14" fill="#1b1730" stroke="none"/>'
        f'<circle cx="186" cy="190" r="5" fill="#fff" stroke="none"/>'
        f'<circle cx="224" cy="190" r="5" fill="#fff" stroke="none"/>'
        f'<path d="M186 224 q14 14 28 0" fill="none" stroke-width="5"/>'
        # antena
        f'<line x1="200" y1="112" x2="200" y2="78"/><circle cx="200" cy="72" r="9" fill="#ffb02b"/>'
        # telescópio
        f'<g transform="rotate(-18 300 250)">'
        f'<rect x="252" y="232" width="120" height="40" rx="18" fill="#dfeaf5"/>'
        f'<circle cx="368" cy="252" r="22" fill="#2ea8ff"/></g>'
        f'</g>')
    return _prop(body, size=size)


def badges_scale(size=None):
    return scale_balance(size=size)


# ---------------------------------------------------------------- conceitos
# objetos para MOSTRAR o que é falado (frio, calor, energia, tempo, vida...)

def snowflake(size=None):
    b = (f'<g stroke="#4fb8ff" stroke-width="11" stroke-linecap="round">'
         f'<line x1="200" y1="64" x2="200" y2="336"/>'
         f'<line x1="82" y1="132" x2="318" y2="268"/>'
         f'<line x1="318" y1="132" x2="82" y2="268"/>'
         f'<g stroke-width="8">'
         f'<path d="M200 104 L168 72 M200 104 L232 72 M200 296 L168 328 M200 296 L232 328" fill="none"/>'
         f'<path d="M116 156 L124 112 M116 156 L160 148 M284 244 L276 288 M284 244 L240 252" fill="none"/>'
         f'<path d="M284 156 L276 112 M284 156 L240 148 M116 244 L124 288 M116 244 L160 252" fill="none"/>'
         f'</g></g>'
         f'<circle cx="200" cy="200" r="16" fill="#bfe9ff" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def iceberg(size=None):
    b = (f'<path d="M64 252 L142 138 L204 186 L252 108 L336 252 Z" fill="#eaf6ff" '
         f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M64 252 H336 L304 306 H120 Z" fill="#bfe3ff" stroke="{INK}" '
         f'stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M142 138 L176 206 L204 186 M252 108 L262 200" fill="none" '
         f'stroke="#9fd0ee" stroke-width="5"/>')
    return _prop(b, size=size)


def flame(size=None):
    b = (f'<path d="M200 56 C252 128 302 158 302 230 a102 102 0 0 1 -204 0 '
         f'C98 172 150 150 166 98 C176 140 196 152 200 130 C210 110 205 82 200 56 Z" '
         f'fill="#ff8a2b" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M200 162 C226 202 240 216 240 250 a40 40 0 0 1 -80 0 '
         f'C160 220 182 202 200 162 Z" fill="#ffd84a" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def water_drop(size=None):
    b = (f'<path d="M200 66 C262 168 292 220 292 262 a92 92 0 0 1 -184 0 '
         f'C108 220 138 168 200 66 Z" fill="#3aa8ff" stroke="{INK}" stroke-width="7" '
         f'stroke-linejoin="round"/>'
         f'<ellipse cx="168" cy="252" rx="20" ry="32" fill="#bfe3ff" opacity=".8"/>')
    return _prop(b, size=size)


def lightning(size=None):
    b = (f'<path d="M236 54 L110 224 H186 L150 346 L306 168 H222 L262 54 Z" '
         f'fill="#ffd84a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def cloud(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<circle cx="150" cy="222" r="58" fill="#eef4fa"/><circle cx="232" cy="198" r="78" '
         f'fill="#eef4fa"/><circle cx="300" cy="230" r="50" fill="#eef4fa"/>'
         f'<rect x="92" y="222" width="248" height="58" rx="29" fill="#eef4fa"/></g>')
    return _prop(b, size=size)


def storm(size=None):
    b = (f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
         f'<circle cx="150" cy="182" r="52" fill="#b9c6d6"/><circle cx="228" cy="160" r="70" '
         f'fill="#b9c6d6"/><circle cx="292" cy="188" r="46" fill="#b9c6d6"/>'
         f'<rect x="96" y="182" width="240" height="54" rx="27" fill="#b9c6d6"/></g>'
         f'<path d="M212 232 L150 320 H196 L176 356" fill="none" stroke="#ffd84a" '
         f'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
         f'<line x1="120" y1="250" x2="106" y2="320" stroke="#7fb2ff" stroke-width="9" stroke-linecap="round"/>'
         f'<line x1="276" y1="250" x2="292" y2="322" stroke="#7fb2ff" stroke-width="9" stroke-linecap="round"/>')
    return _prop(b, size=size)


def mountain(size=None):
    b = (f'<path d="M52 304 L172 112 L242 214 L302 132 L352 304 Z" fill="#8fa6b8" '
         f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M172 112 L214 180 L182 174 L160 202 Z" fill="#fff" stroke="{INK}" '
         f'stroke-width="4" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def magnet(size=None):
    b = (f'<path d="M116 84 v118 a84 84 0 0 0 168 0 V84 h-54 v118 a30 30 0 0 1 -60 0 V84 Z" '
         f'fill="#e8402a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<rect x="116" y="62" width="54" height="34" fill="#dfe6ee" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="230" y="62" width="54" height="34" fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def battery(size=None):
    b = (f'<rect x="76" y="138" width="244" height="132" rx="18" fill="#eef2f6" '
         f'stroke="{INK}" stroke-width="7"/>'
         f'<rect x="320" y="180" width="30" height="48" rx="8" fill="#cfd6dd" '
         f'stroke="{INK}" stroke-width="6"/>'
         f'<rect x="98" y="160" width="58" height="88" fill="#2ecc40"/>'
         f'<rect x="166" y="160" width="58" height="88" fill="#2ecc40"/>'
         f'<rect x="234" y="160" width="58" height="88" fill="#d8e0e8"/>')
    return _prop(b, size=size)


def comet(size=None):
    b = (f'<path d="M306 78 C186 122 122 208 66 330" fill="none" stroke="#bfe3ff" '
         f'stroke-width="18" opacity=".55" stroke-linecap="round"/>'
         f'<path d="M306 78 C204 144 162 216 118 330" fill="none" stroke="#7fd4ff" '
         f'stroke-width="8" opacity=".7" stroke-linecap="round"/>'
         f'<circle cx="306" cy="78" r="46" fill="#eaf6ff" stroke="{INK}" stroke-width="7"/>')
    return _prop(b, size=size)


def meteor(size=None):
    rnd = _rng("meteor")
    craters = ""
    for _ in range(7):
        cx = 200 + (rnd() - .5) * 150
        cy = 200 + (rnd() - .5) * 150
        craters += (f'<path d="{_blob(cx, cy, 10+rnd()*20, 9+rnd()*16, 0, rnd, .3)}" '
                    f'fill="#5f4636"/>')
    b = (f'<defs><clipPath id="cmet"><circle cx="200" cy="200" r="92"/></clipPath></defs>'
         f'<circle cx="200" cy="200" r="92" fill="#8b6a52" stroke="{INK}" stroke-width="7"/>'
         f'<g clip-path="url(#cmet)">{craters}</g>'
         f'<path d="M300 120 C260 90 230 70 190 56" fill="none" stroke="#ffb02b" '
         f'stroke-width="10" opacity=".8" stroke-linecap="round"/>')
    return _prop(b, size=size)


def planet_rings(size=None):
    b = (f'<ellipse cx="200" cy="206" rx="172" ry="46" fill="none" stroke="#e8c98a" '
         f'stroke-width="18" transform="rotate(-16 200 206)"/>'
         f'<circle cx="200" cy="200" r="92" fill="#e8c98a" stroke="{INK}" stroke-width="6"/>'
         f'<ellipse cx="200" cy="200" rx="172" ry="46" fill="none" stroke="{INK}" '
         f'stroke-width="4" opacity=".35" transform="rotate(-16 200 200)"/>')
    return _prop(b, size=size)


def volcano(size=None):
    b = (f'<path d="M52 320 L168 150 H232 L348 320 Z" fill="#6b5a52" stroke="{INK}" '
         f'stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M168 150 L200 116 L232 150 Z" fill="#e8402a" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M200 116 C214 86 188 66 200 34" fill="none" stroke="#ff8a2b" '
         f'stroke-width="12" stroke-linecap="round"/>')
    return _prop(b, size=size)


def tree(size=None):
    b = (f'<rect x="184" y="222" width="32" height="110" fill="#8b5a2b" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="200" cy="176" r="90" fill="#3fae5a" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="140" cy="220" r="54" fill="#3fae5a" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="260" cy="220" r="54" fill="#3fae5a" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def brain(size=None):
    b = (f'<path d="M200 88 a60 60 0 0 0 -60 60 a50 50 0 0 0 -18 90 a56 56 0 0 0 78 40 '
         f'a56 56 0 0 0 78 -40 a50 50 0 0 0 -18 -90 a60 60 0 0 0 -60 -60 Z" '
         f'fill="#f2b6c6" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M200 100 V286 M158 158 q32 22 42 0 M242 158 q-32 22 -42 0" fill="none" '
         f'stroke="#c47a90" stroke-width="5"/>')
    return _prop(b, size=size)


def magnifier(size=None):
    b = (f'<circle cx="178" cy="168" r="92" fill="#cfe9ff" opacity=".7" stroke="{INK}" stroke-width="10"/>'
         f'<line x1="246" y1="236" x2="332" y2="322" stroke="{INK}" stroke-width="22" stroke-linecap="round"/>')
    return _prop(b, size=size)


def eye(size=None):
    b = (f'<path d="M64 200 C128 118 272 118 336 200 C272 282 128 282 64 200 Z" '
         f'fill="#eef4fa" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<circle cx="200" cy="200" r="52" fill="#3aa8ff" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="200" cy="200" r="24" fill="#0b1420"/>')
    return _prop(b, size=size)


def gear(size=None):
    teeth = "".join(
        f'<rect x="186" y="48" width="28" height="52" rx="6" fill="#8b97a6" stroke="{INK}" '
        f'stroke-width="4" transform="rotate({i * 36} 200 200)"/>' for i in range(10))
    b = (teeth + f'<circle cx="200" cy="200" r="98" fill="#8b97a6" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="40" fill="#eef2f6" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def crown(size=None):
    b = (f'<path d="M74 282 L98 146 L162 220 L200 124 L238 220 L302 146 L326 282 Z" '
         f'fill="#ffd84a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<rect x="74" y="282" width="252" height="42" rx="10" fill="#f4c11e" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="200" cy="196" r="12" fill="#e8402a"/>')
    return _prop(b, size=size)


def arrow_up(size=None):
    return _prop(f'<path d="M200 66 L306 202 H248 V334 H152 V202 H94 Z" fill="#2ecc40" '
                 f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>', size=size)


def arrow_down(size=None):
    return _prop(f'<path d="M200 334 L94 198 H152 V66 H248 V198 H306 Z" fill="#e8402a" '
                 f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>', size=size)


def sun(size=None):
    rays = "".join(
        f'<line x1="200" y1="36" x2="200" y2="78" stroke="#ffb02b" stroke-width="14" '
        f'stroke-linecap="round" transform="rotate({i * 30} 200 200)"/>' for i in range(12))
    b = (rays + f'<circle cx="200" cy="200" r="96" fill="#ffd84a" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="96" fill="#fff3b0" opacity=".45"/>')
    return _prop(b, size=size)


def question(size=None):
    b = (f'<circle cx="200" cy="200" r="132" fill="#7fd4ff" stroke="{INK}" stroke-width="7"/>'
         f'<text x="200" y="274" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
         f'font-size="210" font-weight="700" fill="{INK}" stroke="none">?</text>')
    return _prop(b, size=size)


# ---------------------------------------------------------------- biblioteca temática
# objetos para QUALQUER vídeo do canal (planetas, desastres, usinas, biomas, vida, mundo)

def _disc(cx, cy, r, base, light, spot, n=6, seed="p", ring=False):
    rnd = _rng(seed)
    b = ""
    if ring:
        b += (f'<ellipse cx="{cx}" cy="{cy + r * .1}" rx="{r * 1.7}" ry="{r * .42}" fill="none" '
              f'stroke="#e8c98a" stroke-width="16" transform="rotate(-16 {cx} {cy})"/>')
    b += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{base}" stroke="{INK}" stroke-width="6"/>'
    for _ in range(n):
        x = cx + (rnd() - .5) * r * 1.3
        y = cy + (rnd() - .5) * r * 1.3
        b += (f'<path d="{_blob(x, y, r * .16 + rnd() * r * .14, r * .12 + rnd() * r * .1, 0, rnd, .3)}" '
              f'fill="{spot}" opacity=".8"/>')
    b += f'<circle cx="{cx - r * .32}" cy="{cy - r * .32}" r="{r * .55}" fill="{light}" opacity=".18"/>'
    return b


def _planet(base, light, spot, ring=False, seed="p"):
    def fn(size=None):
        return _prop(_disc(200, 200, 118, base, light, spot, seed=seed, ring=ring), size=size)
    return fn


mercury = _planet("#9aa0a8", "#c9ced5", "#6f757c", seed="mercury")
venus = _planet("#e6c27a", "#f7e2ad", "#c69a4a", seed="venus")
mars = _planet("#c1502e", "#e58a5a", "#8f3a1e", seed="mars")
neptune = _planet("#2f6fe0", "#6ea4ff", "#1b4bb0", seed="neptune")
uranus = _planet("#5fd0d8", "#aef0f4", "#2f9aa8", seed="uranus")
pluto = _planet("#cfc2a8", "#eadfc9", "#a89878", seed="pluto")


def exoplanet(size=None):
    b = (_disc(230, 200, 96, "#3fae5a", "#8fe0a6", "#2a7d42", seed="exo")
         + f'<circle cx="96" cy="120" r="46" fill="#ffd84a" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def solar_system(size=None):
    b = f'<circle cx="200" cy="200" r="40" fill="#ffd84a" stroke="{INK}" stroke-width="6"/>'
    for i, (rx, col) in enumerate([(80, "#9aa0a8"), (112, "#e6c27a"), (146, "#2f6fe0"),
                                   (176, "#c1502e")]):
        b += (f'<ellipse cx="200" cy="200" rx="{rx}" ry="{rx * .5}" fill="none" '
              f'stroke="#9fb0c0" stroke-width="3" opacity=".5"/>'
              f'<circle cx="{200 + rx}" cy="200" r="{9 + i * 2}" fill="{col}" '
              f'stroke="{INK}" stroke-width="4"/>')
    return _prop(b, size=size)


def satellite(size=None):
    b = (f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
         f'<rect x="150" y="170" width="100" height="70" rx="10" fill="#dfe6ee"/>'
         f'<rect x="60" y="182" width="76" height="46" rx="6" fill="#2f6fe0"/>'
         f'<rect x="264" y="182" width="76" height="46" rx="6" fill="#2f6fe0"/>'
         f'<line x1="200" y1="170" x2="200" y2="140"/>'
         f'<path d="M200 140 l-40 -22 v22 z" fill="#dfe6ee"/></g>'
         f'<circle cx="200" cy="205" r="14" fill="#ffd84a" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def space_station(size=None):
    b = (f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
         f'<rect x="120" y="188" width="160" height="34" rx="16" fill="#dfe6ee"/>'
         f'<circle cx="150" cy="205" r="20" fill="#dfe6ee"/>'
         f'<rect x="40" y="176" width="66" height="58" rx="6" fill="#2f6fe0"/>'
         f'<rect x="294" y="176" width="66" height="58" rx="6" fill="#2f6fe0"/>'
         f'<circle cx="250" cy="205" r="18" fill="#bfe3ff"/></g>')
    return _prop(b, size=size)


def rover(size=None):
    b = (f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
         f'<rect x="96" y="176" width="208" height="70" rx="14" fill="#dfe6ee"/>'
         f'<rect x="130" y="140" width="90" height="40" rx="8" fill="#9aa0a8"/>'
         f'<circle cx="130" cy="266" r="28" fill="#3d4652"/><circle cx="200" cy="266" r="28" fill="#3d4652"/>'
         f'<circle cx="270" cy="266" r="28" fill="#3d4652"/>'
         f'<line x1="220" y1="140" x2="260" y2="96"/></g>'
         f'<circle cx="266" cy="90" r="12" fill="#ffd84a" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def eclipse(size=None):
    b = (f'<circle cx="200" cy="200" r="120" fill="#ffd84a" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="120" fill="#0a0f18" opacity=".96"/>'
         f'<circle cx="200" cy="200" r="120" fill="none" stroke="#fff" stroke-width="6" '
         f'opacity=".9"/>')
    return _prop(b, size=size)


def aurora(size=None):
    b = ""
    for i, c in enumerate(["#3ad07a", "#2ea8ff", "#9a6bff"]):
        b += (f'<path d="M60 {300 - i * 40} C160 {140 - i * 30} 260 {200 - i * 40} '
              f'340 {90 - i * 20}" fill="none" stroke="{c}" stroke-width="22" '
              f'opacity=".55" stroke-linecap="round"/>')
    b += (f'<path d="M0 320 H400 V400 H0 Z" fill="#0a2030"/>'
          f'<path d="M40 320 L120 200 L200 320 Z" fill="#12324a"/>'
          f'<path d="M200 320 L280 180 L360 320 Z" fill="#0f2c42"/>')
    return _prop(b, size=size)


def quasar(size=None):
    b = (f'<ellipse cx="200" cy="200" rx="170" ry="30" fill="#cfe9ff" opacity=".5"/>'
         f'<circle cx="200" cy="200" r="40" fill="#fff" stroke="{INK}" stroke-width="6"/>'
         f'<ellipse cx="200" cy="200" rx="170" ry="30" fill="none" stroke="#7fd4ff" '
         f'stroke-width="10" opacity=".9"/>'
         f'<path d="M200 60 V150 M200 250 V340" stroke="#bfe3ff" stroke-width="14" '
         f'stroke-linecap="round" opacity=".85"/>')
    return _prop(b, size=size)


def star_cluster(size=None):
    rnd = _rng("cluster")
    b = ""
    for _ in range(40):
        x, y = 200 + (rnd() - .5) * 260, 200 + (rnd() - .5) * 260
        b += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{3 + rnd() * 7:.1f}" fill="#fff" '
              f'opacity="{.5 + rnd() * .5:.2f}"/>')
    return _prop(b, size=size)


# ---------------------------------------------------------------- desastres naturais

def tornado(size=None):
    b = (f'<path d="M70 60 H330 L250 130 H150 Z" fill="#9fb0c0" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M150 130 H250 C240 200 210 210 200 250 C190 290 176 300 176 340 '
         f'C176 300 162 290 152 250 C142 210 160 200 150 130 Z" fill="#c3ccd6" '
         f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def hurricane(size=None):
    b = ""
    for i, r in enumerate([150, 110, 70]):
        b += (f'<path d="M200 200 m0 -{r} a{r} {r} 0 1 1 -{r*.5} {r*1.4}" fill="none" '
              f'stroke="#5c8fd6" stroke-width="{16 - i * 4}" stroke-linecap="round" opacity=".9"/>')
    b += f'<circle cx="200" cy="200" r="24" fill="#fff" stroke="{INK}" stroke-width="5"/>'
    return _prop(b, size=size)


def earthquake(size=None):
    b = (f'<path d="M34 210 H165 L183 260 L151 355 H34 Z" fill="#b67d50" '
         f'stroke="{INK}" stroke-width="7"/>'
         f'<path d="M366 210 H235 L217 260 L249 355 H366 Z" fill="#d59a61" '
         f'stroke="{INK}" stroke-width="7"/>'
         '<path d="M165 210 L183 260 L151 355 M235 210 L217 260 L249 355" '
         'fill="none" stroke="#ffcd57" stroke-width="10" stroke-linejoin="round"/>'
         '<path d="M186 30 L169 93 L202 82 L187 151 M258 65 L233 120 L264 122" '
         'fill="none" stroke="#ffcd57" stroke-width="13" stroke-linecap="round" '
         'stroke-linejoin="round"/>')
    return _prop(b, size=size)


def tsunami(size=None):
    b = (f'<path d="M40 320 C60 160 150 120 210 170 C170 190 150 230 170 250 '
         f'C210 220 280 230 300 300 C260 260 210 270 190 320 Z" fill="#2ea8ff" '
         f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M0 320 H400 V360 H0 Z" fill="#1b6fc4"/>')
    return _prop(b, size=size)


def wildfire(size=None):
    b = (f'<path d="M120 300 L160 190 L200 300 Z" fill="#3fae5a" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M220 300 L260 200 L300 300 Z" fill="#3fae5a" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="150" y="300" width="16" height="40" fill="#8b5a2b"/>'
         f'<path d="M200 330 C230 280 250 270 250 240 a50 50 0 0 0 -100 0 '
         f'C150 270 170 280 200 330 Z" fill="#ff8a2b" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M200 320 C216 292 226 288 226 270 a26 26 0 0 0 -52 0 '
         f'C174 288 184 292 200 320 Z" fill="#ffd84a"/>')
    return _prop(b, size=size)


def flood(size=None):
    b = (f'<path d="M120 200 L200 120 L280 200 Z" fill="#e8a92c" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="150" y="200" width="100" height="70" fill="#f2c86a" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M0 270 C60 250 120 290 200 270 C280 250 340 290 400 270 V360 H0 Z" '
         f'fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def drought(size=None):
    b = (f'<circle cx="300" cy="90" r="46" fill="#ffb02b" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M40 340 H360" stroke="{INK}" stroke-width="8"/>'
         f'<path d="M90 340 L120 300 L150 340 M200 340 L230 290 L260 340 M150 340 L180 310 L210 340" '
         f'fill="none" stroke="#a8763c" stroke-width="8" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def blizzard(size=None):
    b = (f'<circle cx="150" cy="150" r="52" fill="#eef4fa" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="230" cy="140" r="66" fill="#eef4fa" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="110" y="150" width="180" height="50" rx="25" fill="#eef4fa" stroke="{INK}" stroke-width="6"/>'
         + "".join(f'<g transform="rotate({i*40} 200 280)"><line x1="200" y1="240" x2="200" y2="320" '
                   f'stroke="#5cc6ff" stroke-width="9" stroke-linecap="round"/>'
                   f'<path d="M200 260 l-20 -16 M200 260 l20 -16" fill="none" stroke="#5cc6ff" '
                   f'stroke-width="7" stroke-linecap="round"/></g>' for i in range(6)))
    return _prop(b, size=size)


# ---------------------------------------------------------------- usinas / energia

def nuclear_plant(size=None):
    b = (f'<path d="M120 320 L150 160 H250 L280 320 Z" fill="#cfd6dd" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<ellipse cx="200" cy="160" rx="50" ry="16" fill="#9fb0c0" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M200 140 C210 110 190 96 200 66" fill="none" stroke="#dfe6ee" stroke-width="14" stroke-linecap="round"/>'
         f'<rect x="60" y="300" width="280" height="30" fill="#8b97a6" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def dam(size=None):
    b = (f'<path d="M120 140 H280 L300 320 H100 Z" fill="#b9c3cf" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M0 240 C80 220 120 250 160 240 V360 H0 Z" fill="#2ea8ff" opacity=".85"/>'
         f'<path d="M200 250 V320 M230 250 V320 M260 250 V320" stroke="#7a8794" stroke-width="6"/>')
    return _prop(b, size=size)


def solar_panel(size=None):
    b = (f'<g stroke="{INK}" stroke-width="5">'
         f'<polygon points="120,300 180,140 340,140 300,300" fill="#2f6fe0"/>'
         f'<line x1="150" y1="200" x2="320" y2="200"/><line x1="165" y1="250" x2="310" y2="250"/>'
         f'<line x1="200" y1="140" x2="230" y2="300"/><line x1="270" y1="140" x2="270" y2="300"/></g>'
         f'<rect x="196" y="300" width="18" height="50" fill="#8b97a6" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def wind_turbine(size=None):
    b = (f'<rect x="192" y="160" width="16" height="180" fill="#eef2f6" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="200" cy="150" r="18" fill="#cfd6dd" stroke="{INK}" stroke-width="6"/>'
         + "".join(f'<path d="M200 150 L200 60" stroke="#eef2f6" stroke-width="16" '
                   f'stroke-linecap="round" transform="rotate({a} 200 150)"/>' for a in (0, 120, 240)))
    return _prop(b, size=size)


def coal_plant(size=None):
    b = (f'<rect x="120" y="200" width="180" height="120" fill="#8b97a6" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="150" y="120" width="40" height="90" fill="#9fb0c0" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="230" y="150" width="40" height="60" fill="#9fb0c0" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="170" cy="100" r="26" fill="#c3ccd6" opacity=".8"/>'
         f'<circle cx="250" cy="120" r="22" fill="#c3ccd6" opacity=".8"/>')
    return _prop(b, size=size)


def geothermal(size=None):
    b = (f'<path d="M40 320 H360 L300 200 H100 Z" fill="#6b5a52" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M180 200 V120 M220 200 V120" stroke="#c3ccd6" stroke-width="14" stroke-linecap="round"/>'
         f'<circle cx="180" cy="100" r="20" fill="#eef4fa" opacity=".85"/>'
         f'<circle cx="220" cy="90" r="16" fill="#eef4fa" opacity=".85"/>')
    return _prop(b, size=size)


def power_grid(size=None):
    b = (f'<path d="M200 60 L120 340 M200 60 L280 340 M140 230 H260 M156 180 H244" '
         f'stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M0 120 C80 90 160 150 200 120 C240 90 320 150 400 120" fill="none" '
         f'stroke="#e8a92c" stroke-width="7"/>')
    return _prop(b, size=size)


# ---------------------------------------------------------------- biomas / natureza

def _tree_at(x, base, scale, trunk="#8b5a2b", leaf="#3fae5a"):
    return (f'<rect x="{x - 8 * scale}" y="{base - 46 * scale}" width="{16 * scale}" '
            f'height="{46 * scale}" fill="{trunk}" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{x}" cy="{base - 78 * scale}" r="{44 * scale}" fill="{leaf}" '
            f'stroke="{INK}" stroke-width="5"/>')


def amazon(size=None):
    b = (f'<path d="M0 320 H400 V360 H0 Z" fill="#2f7d3f"/>'
         + _tree_at(90, 320, 1.1) + _tree_at(200, 320, 1.35) + _tree_at(310, 320, 1.05))
    return _prop(b, size=size)


def cerrado(size=None):
    b = (f'<path d="M0 320 H400 V360 H0 Z" fill="#c8b06a"/>'
         + _tree_at(110, 320, .8, leaf="#7fae3f") + _tree_at(290, 320, .7, leaf="#7fae3f")
         + f'<path d="M40 330 q10 -20 20 0 M180 334 q10 -18 20 0 M340 332 q10 -20 20 0" '
           f'fill="none" stroke="#8a9a3f" stroke-width="5"/>')
    return _prop(b, size=size)


def caatinga(size=None):
    b = (f'<path d="M0 320 H400 V360 H0 Z" fill="#d8b070"/>'
         f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
         f'<rect x="180" y="120" width="34" height="200" rx="16" fill="#3fae5a"/>'
         f'<rect x="140" y="170" width="24" height="90" rx="12" fill="#3fae5a"/>'
         f'<rect x="236" y="150" width="24" height="110" rx="12" fill="#3fae5a"/></g>'
         f'<circle cx="197" cy="118" r="14" fill="#ff6ad5" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def pantanal(size=None):
    b = (f'<path d="M0 250 C80 230 140 270 220 250 C300 230 360 270 400 250 V360 H0 Z" '
         f'fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>'
         + _tree_at(90, 250, .7, leaf="#3fae5a") + _tree_at(310, 250, .65, leaf="#3fae5a")
         + f'<path d="M150 210 q14 -16 28 0 q-14 10 -28 0 M230 200 q14 -16 28 0 q-14 10 -28 0" '
           f'fill="#fff" stroke="{INK}" stroke-width="4"/>')
    return _prop(b, size=size)


def mangrove(size=None):
    b = (f'<path d="M0 300 H400 V360 H0 Z" fill="#2ea8ff" opacity=".85"/>'
         f'<circle cx="200" cy="150" r="80" fill="#3fae5a" stroke="{INK}" stroke-width="6"/>'
         + "".join(f'<path d="M{200 + dx} 220 q{dx * .3} 50 {dx * .6} 80" fill="none" '
                   f'stroke="#8b5a2b" stroke-width="8" stroke-linecap="round"/>'
                   for dx in (-60, -30, 0, 30, 60)))
    return _prop(b, size=size)


def pampa(size=None):
    b = (f'<path d="M0 300 H400 V360 H0 Z" fill="#8fc24f"/>'
         + "".join(f'<path d="M{x} 300 q6 -40 -4 -70 M{x + 14} 300 q10 -34 2 -64" fill="none" '
                   f'stroke="#6fae3f" stroke-width="6" stroke-linecap="round"/>'
                   for x in (40, 110, 180, 250, 320)))
    return _prop(b, size=size)


# ---------------------------------------------------------------- vida / ciência

def microscope(size=None):
    b = (f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round">'
         f'<path d="M170 90 L230 150 L196 184 L136 124 Z" fill="#dfe6ee"/>'
         f'<rect x="150" y="180" width="90" height="20" rx="8" fill="#9fb0c0"/>'
         f'<path d="M180 200 V280 H120" fill="none"/>'
         f'<rect x="120" y="280" width="180" height="22" rx="10" fill="#8b97a6"/></g>'
         f'<circle cx="255" cy="230" r="26" fill="#bfe3ff" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def dna(size=None):
    b = ""
    for i in range(10):
        y = 60 + i * 32
        off = 60 if i % 2 == 0 else -60
        b += (f'<circle cx="{200 + off}" cy="{y}" r="14" fill="#2ea8ff" stroke="{INK}" stroke-width="4"/>'
              f'<circle cx="{200 - off}" cy="{y}" r="14" fill="#e8402a" stroke="{INK}" stroke-width="4"/>'
              f'<line x1="{200 + off}" y1="{y}" x2="{200 - off}" y2="{y}" stroke="{INK}" stroke-width="4" opacity=".5"/>')
    b += (f'<path d="M260 60 C140 140 260 260 140 340" fill="none" stroke="#2ea8ff" stroke-width="7"/>'
          f'<path d="M140 60 C260 140 140 260 260 340" fill="none" stroke="#e8402a" stroke-width="7"/>')
    return _prop(b, size=size)


def virus(size=None):
    b = f'<circle cx="200" cy="200" r="90" fill="#c85ad0" stroke="{INK}" stroke-width="7"/>'
    for i in range(12):
        b += (f'<g transform="rotate({i * 30} 200 200)"><line x1="200" y1="110" x2="200" y2="66" '
              f'stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
              f'<circle cx="200" cy="60" r="12" fill="#e8a92c" stroke="{INK}" stroke-width="4"/></g>')
    b += (f'<circle cx="170" cy="180" r="14" fill="#8f2f96"/><circle cx="230" cy="210" r="18" fill="#8f2f96"/>')
    return _prop(b, size=size)


def cell(size=None):
    b = (f'<circle cx="200" cy="200" r="130" fill="#bfe3ff" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="130" fill="none" stroke="#7fb2d6" stroke-width="4" opacity=".6"/>'
         f'<circle cx="200" cy="200" r="48" fill="#9a6bff" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="130" cy="150" r="20" fill="#3ad07a" stroke="{INK}" stroke-width="5"/>'
         f'<circle cx="270" cy="250" r="16" fill="#ff8a2b" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def heart(size=None):
    b = (f'<path d="M200 320 C90 240 60 160 120 118 C168 86 196 120 200 150 '
         f'C204 120 232 86 280 118 C340 160 310 240 200 320 Z" fill="#e8402a" '
         f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M120 180 h40 l16 -34 l22 70 l18 -36 h48" fill="none" stroke="#fff" '
         f'stroke-width="8" stroke-linejoin="round"/>')
    return _prop(b, size=size)


def leaf(size=None):
    b = (f'<path d="M320 70 C180 70 90 150 90 260 C90 300 110 330 150 330 '
         f'C260 330 340 240 340 100 C340 88 334 78 320 70 Z" fill="#3fae5a" '
         f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M140 300 C180 240 240 180 320 110 M200 220 l-40 -6 M240 180 l-40 -6" '
         f'fill="none" stroke="#2a7d42" stroke-width="6"/>')
    return _prop(b, size=size)


# ---------------------------------------------------------------- mundo

def city(size=None):
    b = (f'<rect x="60" y="180" width="60" height="160" fill="#8b97a6" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="140" y="120" width="70" height="220" fill="#9fb0c0" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="230" y="200" width="60" height="140" fill="#8b97a6" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="300" y="150" width="50" height="190" fill="#9fb0c0" stroke="{INK}" stroke-width="5"/>'
         + "".join(f'<rect x="{x}" y="{y}" width="16" height="16" fill="#ffe07a"/>'
                   for x in (150, 180, 240, 310) for y in (140, 180, 220)))
    return _prop(b, size=size)


def house(size=None):
    b = (f'<path d="M90 200 L200 100 L310 200 Z" fill="#e8402a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<rect x="120" y="200" width="160" height="130" fill="#f2c86a" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="180" y="250" width="50" height="80" fill="#8b5a2b" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="140" y="230" width="34" height="34" fill="#bfe3ff" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def factory(size=None):
    b = (f'<rect x="80" y="200" width="240" height="130" fill="#9fb0c0" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M80 200 L80 150 L140 180 L140 150 L200 180 L200 150 L260 180 L260 200 Z" '
         f'fill="#8b97a6" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<rect x="110" y="250" width="40" height="40" fill="#ffe07a" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="250" y="240" width="40" height="90" fill="#8b97a6" stroke="{INK}" stroke-width="5"/>')
    return _prop(b, size=size)


def car(size=None):
    b = (f'<path d="M60 260 L90 190 H310 L340 260 Z" fill="#2ea8ff" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<rect x="60" y="250" width="280" height="40" rx="14" fill="#2ea8ff" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="120" y="200" width="160" height="44" fill="#bfe3ff" stroke="{INK}" stroke-width="5"/>'
         f'<circle cx="130" cy="300" r="30" fill="#3d4652" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="270" cy="300" r="30" fill="#3d4652" stroke="{INK}" stroke-width="6"/>')
    return _prop(b, size=size)


def plane(size=None):
    b = (f'<path d="M60 200 L340 170 L340 210 L60 220 Z" fill="#eef2f6" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M150 205 L210 110 L250 112 L215 205 Z" fill="#dfe6ee" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M150 215 L200 300 L240 298 L210 215 Z" fill="#dfe6ee" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="330" cy="190" r="10" fill="#2ea8ff"/>')
    return _prop(b, size=size)


def ship(size=None):
    b = (f'<path d="M60 250 H340 L300 320 H100 Z" fill="#3d4652" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<rect x="150" y="180" width="100" height="70" fill="#eef2f6" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="190" y="130" width="30" height="50" fill="#9fb0c0" stroke="{INK}" stroke-width="5"/>'
         f'<path d="M0 320 H400" stroke="#2ea8ff" stroke-width="10"/>')
    return _prop(b, size=size)


def coin(size=None):
    b = (f'<circle cx="200" cy="200" r="120" fill="#ffd84a" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="200" cy="200" r="92" fill="none" stroke="#c78d0c" stroke-width="8"/>'
         f'<text x="200" y="252" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
         f'font-size="130" font-weight="700" fill="#c78d0c" stroke="none">R$</text>')
    return _prop(b, size=size)


def chart(size=None):
    b = (f'<rect x="70" y="80" width="260" height="240" rx="12" fill="#fff" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="110" y="230" width="40" height="60" fill="#2ea8ff"/>'
         f'<rect x="170" y="190" width="40" height="100" fill="#3ad07a"/>'
         f'<rect x="230" y="140" width="40" height="150" fill="#ff8a2b"/>')
    return _prop(b, size=size)


LIB = {
    # estrelas
    "red_dwarf": _star("red_dwarf", base="#e8402a", mid="#f4724a", light="#ffc59a",
                       spot="#9c1a10", glow="#ff5a3c", rays=14),
    "orange_dwarf": _star("orange_dwarf", base="#ef8a1e", mid="#f6ab3c", light="#ffd98a",
                          spot="#b85a0e", glow="#ffb02b", rays=18),
    "yellow_dwarf": _star("yellow_dwarf", base="#f4c11e", mid="#ffd84a", light="#fff0a6",
                          spot="#c78d0c", glow="#ffd84a", rays=22),
    "white_dwarf": _star("white_dwarf", base="#cfe3f5", mid="#eaf4ff", light="#ffffff",
                         spot="#8fb4d6", glow="#bfe3ff", rays=10),
    "blue_dwarf": _star("blue_dwarf", base="#2f8ff0", mid="#5cb4ff", light="#cfe9ff",
                        spot="#1b5fb0", glow="#5cb4ff", rays=12),
    "brown_dwarf": _star("brown_dwarf", base="#7b4a2e", mid="#9c6640", light="#c99566",
                         spot="#5a3320", glow="#c99566", rays=6),
    "subdwarf": _star("subdwarf", base="#8fd0f5", mid="#bfe6ff", light="#ffffff",
                      spot="#5aa8d8", glow="#bfe6ff", spikes=10),
    "blue_giant": _star("blue_giant", base="#2f8ff0", mid="#5cb4ff", light="#dff1ff",
                        spot="#1b5fb0", glow="#5cb4ff", spikes=14),
    "red_giant": _star("red_giant", base="#e04a1e", mid="#f47a34", light="#ffce8a",
                       spot="#a02a0e", glow="#ff7a3c", spikes=12),
    "blue_supergiant": _star("blue_supergiant", base="#3a6bff", mid="#69a8ff", light="#e6f2ff",
                             spot="#2440b0", glow="#69a8ff", spikes=18, ring=True),
    "red_supergiant": _star("red_supergiant", base="#d43a12", mid="#ef7a2a", light="#ffcf8f",
                            spot="#8f1f08", glow="#ff6a2a", spikes=18, ring=True),
    "hypergiant": _star("hypergiant", base="#ff7a2a", mid="#ffb14a", light="#fff0c2",
                        spot="#c2440e", glow="#ffd08a", spikes=22, ring=True, asteroids=6),
    "neutron_star": _star("neutron_star", base="#7fd4ff", mid="#bfeaff", light="#ffffff",
                          spot="#4aa6e0", glow="#bfeaff", spikes=20),
    "pulsar": _star("pulsar", base="#7fd4ff", mid="#cfeaff", light="#ffffff",
                    spot="#4aa6e0", glow="#bfeaff", spikes=16),
    "magnetar": _star("magnetar", base="#9a6bff", mid="#c3a6ff", light="#efe6ff",
                      spot="#6633c4", glow="#c3a6ff", spikes=16),
    "quark_star": _star("quark_star", base="#ff5ad0", mid="#ff9fe4", light="#ffe0f5",
                        spot="#c4288f", glow="#ff9fe4", spikes=16),
    "black_hole": lambda size=None: _prop(
        f'<circle cx="200" cy="200" r="70" fill="#05070c"/>'
        f'<ellipse cx="200" cy="200" rx="168" ry="42" fill="none" stroke="#ff8a2b" '
        f'stroke-width="18" opacity=".92" transform="rotate(-14 200 200)"/>'
        f'<ellipse cx="200" cy="200" rx="120" ry="26" fill="none" stroke="#ffd08a" '
        f'stroke-width="8" opacity=".8" transform="rotate(-14 200 200)"/>'
        f'<circle cx="200" cy="200" r="70" fill="none" stroke="{INK}" stroke-width="6"/>', size=size),
    "star_generic": _star("star_generic", base="#f4c11e", mid="#ffd84a", light="#fff0a6",
                          spot="#c78d0c", glow="#ffd84a", rays=14),
    "supernova": lambda size=None: burst("#ffd08a", 18, size),
    # props
    "hourglass": hourglass,
    "spoon": spoon,
    "scale": scale_balance,
    "thermometer": thermometer,
    "thermometer_cold": thermometer_cold,
    "canister": canister,
    "fuel": fuel_gallon,
    "atom": atom,
    "hydrogen": element_hydrogen,
    "prism": prism,
    "earth": earth,
    "rocket": rocket,
    "telescope": telescope,
    "lightbulb": lightbulb,
    "tape": tape_measure,
    "arrow": arrow_red,
    "check": check_green,
    "cross": cross_red,
    "gas_giant": gas_giant,
    "galaxy": galaxy,
    "nebula": nebula,
    "moon": moon,
    "mascot": mascot,
    # conceitos (mostrar o que é falado)
    "snowflake": snowflake, "iceberg": iceberg, "flame": flame, "water": water_drop,
    "lightning": lightning, "cloud": cloud, "storm": storm, "mountain": mountain,
    "magnet": magnet, "battery": battery, "comet": comet, "meteor": meteor,
    "planet_rings": planet_rings, "volcano": volcano, "tree": tree, "brain": brain,
    "magnifier": magnifier, "eye": eye, "gear": gear, "crown": crown,
    "arrow_up": arrow_up, "arrow_down": arrow_down, "sun": sun, "question": question,
    # sistema solar / espaço
    "mercury": mercury, "venus": venus, "mars": mars, "neptune": neptune, "uranus": uranus,
    "pluto": pluto, "exoplanet": exoplanet, "solar_system": solar_system,
    "satellite": satellite, "space_station": space_station, "rover": rover, "eclipse": eclipse,
    "aurora": aurora, "quasar": quasar, "star_cluster": star_cluster,
    # desastres naturais
    "tornado": tornado, "hurricane": hurricane, "earthquake": earthquake, "tsunami": tsunami,
    "wildfire": wildfire, "flood": flood, "drought": drought, "blizzard": blizzard,
    # usinas / energia
    "nuclear_plant": nuclear_plant, "dam": dam, "solar_panel": solar_panel,
    "wind_turbine": wind_turbine, "coal_plant": coal_plant, "geothermal": geothermal,
    "power_grid": power_grid,
    # biomas
    "amazon": amazon, "cerrado": cerrado, "caatinga": caatinga, "pantanal": pantanal,
    "mangrove": mangrove, "pampa": pampa,
    # vida / ciência
    "microscope": microscope, "dna": dna, "virus": virus, "cell": cell, "heart": heart,
    "leaf": leaf,
    # mundo
    "city": city, "house": house, "factory": factory, "car": car, "plane": plane,
    "ship": ship, "coin": coin, "chart": chart,
}

ALIASES = {
    "ana_vermelha": "red_dwarf", "ana_laranja": "orange_dwarf", "ana_amarela": "yellow_dwarf",
    "ana_branca": "white_dwarf", "ana_azul": "blue_dwarf", "ana_marrom": "brown_dwarf",
    "subana": "subdwarf", "gigante_azul": "blue_giant", "gigante_vermelha": "red_giant",
    "supergigante_azul": "blue_supergiant", "supergigante_vermelha": "red_supergiant",
    "supergigante": "hypergiant", "hipergigante": "hypergiant", "estrela_de_neutrons": "neutron_star",
    "wolf_rayet": "blue_supergiant", "wolf": "blue_supergiant", "raiet": "blue_supergiant",
    "anao_vermelho": "red_dwarf", "anao_laranja": "orange_dwarf", "anao_amarelo": "yellow_dwarf",
    "anao_branco": "white_dwarf", "anao_azul": "blue_dwarf", "anao_marrom": "brown_dwarf",
    "buraco_negro": "black_hole", "escala": "scale", "colher": "spoon", "ampulheta": "hourglass",
    "termometro": "thermometer", "polvo": "mascot", "mascote": "mascot",
    # conceitos
    "frio": "snowflake", "gelo": "iceberg", "calor": "flame", "fogo": "flame",
    "agua": "water", "energia": "lightning", "raio": "lightning", "nuvem": "cloud",
    "tempestade": "storm", "montanha": "mountain", "ima": "magnet", "cometa": "comet",
    "meteoro": "meteor", "asteroide": "meteor", "saturno": "planet_rings",
    "vulcao": "volcano", "vida": "tree", "cerebro": "brain", "ideia": "brain",
    "pesquisa": "magnifier", "olho": "eye", "engrenagem": "gear", "coroa": "crown",
    "sobe": "arrow_up", "desce": "arrow_down", "sol": "sun", "pergunta": "question",
    "duvida": "question", "floco": "snowflake", "neve": "snowflake", "nebulosa": "nebula",
    # sistema solar / espaço
    "mercurio": "mercury", "venus": "venus", "marte": "mars", "netuno": "neptune",
    "urano": "uranus", "plutao": "pluto", "exoplaneta": "exoplanet",
    "sistema_solar": "solar_system", "satelite": "satellite", "estacao_espacial": "space_station",
    "sonda": "rover", "eclipse": "eclipse", "aurora": "aurora", "quasar": "quasar",
    "aglomerado": "star_cluster",
    # desastres
    "tornado": "tornado", "furacao": "hurricane", "terremoto": "earthquake",
    "tsunami": "tsunami", "incendio": "wildfire", "enchente": "flood", "seca": "drought",
    "nevasca": "blizzard",
    # usinas
    "nuclear": "nuclear_plant", "usina_nuclear": "nuclear_plant", "hidreletrica": "dam",
    "barragem": "dam", "painel_solar": "solar_panel", "energia_solar": "solar_panel",
    "turbina": "wind_turbine", "eolica": "wind_turbine", "carvao": "coal_plant",
    "termoeletrica": "coal_plant", "geotermica": "geothermal", "rede_eletrica": "power_grid",
    # biomas
    "amazonia": "amazon", "floresta": "amazon", "cerrado": "cerrado", "caatinga": "caatinga",
    "pantanal": "pantanal", "mangue": "mangrove", "pampa": "pampa",
    # vida / ciência
    "microscopio": "microscope", "adn": "dna", "virus": "virus", "celula": "cell",
    "coracao": "heart", "folha": "leaf",
    # mundo
    "cidade": "city", "casa": "house", "fabrica": "factory", "carro": "car", "aviao": "plane",
    "navio": "ship", "moeda": "coin", "grafico": "chart", "dinheiro": "coin",
}


# categoria temática de cada objeto (para escolher o objeto certo pelo contexto)
CAT: dict[str, str] = {}


def _cat(cat, *ids):
    for i in ids:
        CAT[i] = cat


_cat("astro", "red_dwarf", "orange_dwarf", "yellow_dwarf", "white_dwarf", "blue_dwarf",
     "brown_dwarf", "subdwarf", "blue_giant", "red_giant", "blue_supergiant", "red_supergiant",
     "hypergiant", "neutron_star", "pulsar", "magnetar", "quark_star", "black_hole",
     "star_generic", "supernova", "galaxy", "nebula", "moon", "planet_rings", "gas_giant",
     "earth", "rocket", "telescope", "satellite", "space_station", "rover", "eclipse",
     "aurora", "quasar", "star_cluster", "solar_system", "exoplanet", "mercury", "venus",
     "mars", "neptune", "uranus", "pluto", "sun", "comet", "meteor")
_cat("concept", "atom", "hydrogen", "prism", "hourglass", "scale", "thermometer",
     "thermometer_cold", "tape", "lightbulb", "spoon", "canister", "fuel", "magnet")
_cat("nature", "tornado", "hurricane", "earthquake", "tsunami", "wildfire", "flood",
     "drought", "blizzard", "volcano", "mountain", "cloud", "storm", "water", "iceberg",
     "snowflake", "tree", "leaf")
_cat("energy", "nuclear_plant", "dam", "solar_panel", "wind_turbine", "coal_plant",
     "geothermal", "power_grid", "battery", "lightning")
_cat("biome", "amazon", "cerrado", "caatinga", "pantanal", "mangrove", "pampa")
_cat("life", "microscope", "dna", "virus", "cell", "heart", "brain", "eye")
_cat("world", "city", "house", "factory", "car", "plane", "ship", "coin", "chart", "crown",
     "question", "gear", "arrow_up", "arrow_down", "magnifier")

# objetos que SOMEM/ficam ilegíveis em fundo branco (só aparecem bem no escuro)
DARK = {"galaxy", "nebula", "aurora", "star_cluster", "quasar", "comet", "moon", "pluto",
        "mercury", "sun", "lightbulb", "solar_system", "eclipse", "neutron_star", "pulsar"}


def category(concept: str) -> str:
    return CAT.get(resolve(concept), "concept")


def needs_dark(concept: str) -> bool:
    return resolve(concept) in DARK


def resolve(concept: str) -> str:
    """id ou sinônimo -> id canônico da biblioteca."""
    key = (concept or "").strip().lower().replace("-", "_").replace(" ", "_")
    if key in LIB:
        return key
    if key in ALIASES:
        return ALIASES[key]
    return ""


def render(concept: str, size: int | None = None) -> str:
    key = resolve(concept)
    if not key:
        return ""
    return LIB[key](size=size)


def has(concept: str) -> bool:
    return bool(resolve(concept))


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--size", type=int, default=720)
    a = ap.parse_args()
    if a.list or not a.name:
        print(f"{len(LIB)} ilustrações: " + ", ".join(sorted(LIB)))
        return
    svg = render(a.name, size=a.size)
    if not svg:
        raise SystemExit(f"ilustração desconhecida: {a.name}")
    if a.out:
        open(a.out, "w", encoding="utf-8").write(svg)
        print("->", a.out)
    else:
        print(svg)


if __name__ == "__main__":
    main()
