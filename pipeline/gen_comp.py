# -*- coding: utf-8 -*-
"""
gen_comp.py — gera a composição HyperFrames (index.html + motion) a partir do episode.json.

Dois temas sobre fundo espacial escuro:
  - "cartoon": texto azul grosso com contorno e glow; ilustrações vetoriais grandes.
  - "doodle": título em fonte de mão sobre faixa escura. O tema não traduz o roteiro.

Uso:
  python pipeline/gen_comp.py <proj> --spec episode.json [--theme cartoon]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import shutil
from html import escape

import ilustras
import mg
import vendor

W, H = 1920, 1080
MOTION_SAMPLE_CAP = 300  # HyperFrames 0.8.79, motion pass do `check`


def motion_static_limit(total: float) -> float:
    """Set the motion gate just above the checker's minimum sample interval."""
    sample_gap = float(total) / (MOTION_SAMPLE_CAP - 1)
    return max(2.5, math.ceil((sample_gap + 0.01) * 1000) / 1000)


def _num(v) -> str:
    """Número em pt-BR, sem casas decimais quando inteiro (2500 -> 2.500)."""
    f = float(v)
    if abs(f - round(f)) < 1e-9:
        return f"{int(round(f)):,}".replace(",", ".")
    s = f"{f:,.2f}".rstrip("0").rstrip(".")
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ---------------------------------------------------------------- temas

THEMES = {
    "cartoon": {
        "fonts": ("https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&"
                  "family=Nunito:wght@700;800&display=swap"),
        "title_font": "'Baloo 2', 'Nunito', sans-serif",
        "body_font": "'Nunito', sans-serif",
        "title_size": 112,
        "callout_size": 132,
        "list_size": 70,
        "frase_size": 138,
        "title_color": "#2ba6ff",
        "callout_color": "#2ba6ff",
        "list_color": "#2ba6ff",
        "frase_color": "#2ba6ff",
        "title_top": 26,
        "comic": True,
    },
    "doodle": {
        "fonts": ("https://fonts.googleapis.com/css2?family=Patrick+Hand&"
                  "family=Caveat:wght@600;700&display=swap"),
        "title_font": "'Patrick Hand', cursive",
        "body_font": "'Patrick Hand', cursive",
        "title_size": 78,
        "callout_size": 92,
        "list_size": 60,
        "frase_size": 118,
        "title_color": "#eaf6ff",
        "callout_color": "#ffd84a",
        "list_color": "#eaf6ff",
        "frase_color": "#eaf6ff",
        "title_top": 0,
        "comic": False,
    },
}


# fundo do espaço: camadas com overscan (2200x1280) para o parallax nunca abrir borda
BG_W, BG_H, BG_OX, BG_OY = 2200, 1280, 140, 100

# Sangria e amplitude do parallax ambiente por cena. O zoom precisa cobrir o
# drift: 6% de 1920 = 115 px na horizontal e 6% de 1080 = 65 px na vertical,
# contra um drift de 28/16 px.
BG_ZOOM = 1.06
BG_DRIFT = (28.0, 16.0)

STAR_PALETTE = ["#ffffff", "#ffffff", "#ffffff", "#f4f9ff", "#dfeaff", "#cfe0ff", "#ffe9cf"]


def _stars_svg(seed, n, smin, smax, glow=False) -> str:
    """Campo de estrelas redondas, com halo suave nas maiores (sem losangos duros)."""
    rnd = random.Random(seed)
    parts = []
    for _ in range(n):
        x, y = rnd.random() * BG_W - BG_OX, rnd.random() * BG_H - BG_OY
        r = rnd.uniform(smin, smax)
        o = rnd.uniform(0.22, 0.95)
        c = rnd.choice(STAR_PALETTE)
        if glow and r > (smin + smax) / 2:
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 3.4:.1f}" '
                         f'fill="{c}" opacity="{o * 0.12:.3f}"/>')
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.2f}" fill="{c}" '
                     f'opacity="{o:.2f}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{BG_W}" height="{BG_H}" '
            f'viewBox="0 0 {BG_W} {BG_H}" preserveAspectRatio="xMidYMid slice">'
            f'{"".join(parts)}</svg>')


def _twinkle_html(seed, n=14) -> str:
    """Poucas estrelas cintilantes (divs com id) que o GSAP pulsa no ritmo do vídeo."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x, y = rnd.randint(0, 1920), rnd.randint(0, 1080)
        s = rnd.choice([6, 8, 10, 12, 16])
        out.append(f'<div id="tw{i}" class="tw" style="left:{x}px;top:{y}px;'
                   f'width:{s}px;height:{s}px;margin-left:-{s // 2}px;margin-top:-{s // 2}px"></div>')
    return "".join(out)


def space_bg(total) -> tuple[str, list]:
    """HTML interno + animações do fundo (nebulosa, 2 camadas em parallax, cintilação)."""
    html = (
        '<div style="position:absolute;inset:0;background:'
        'radial-gradient(1500px 1000px at 68% 16%, #0a1731 0%, #050a16 46%, #02040a 100%)"></div>'
        '<div id="bg-neb" style="position:absolute;left:-8%;top:-8%;width:116%;height:116%;'
        'opacity:.95;background:'
        'radial-gradient(620px 420px at 22% 78%, rgba(64,120,255,.17), transparent 70%),'
        'radial-gradient(760px 520px at 82% 24%, rgba(150,86,255,.14), transparent 72%),'
        'radial-gradient(560px 560px at 56% 112%, rgba(0,190,255,.10), transparent 70%)"></div>'
        f'<div id="bg-far" class="star-layer">{_stars_svg(11, 220, 0.7, 1.7)}</div>'
        f'<div id="bg-near" class="star-layer">{_stars_svg(23, 80, 1.4, 2.7, glow=True)}</div>'
        f'<div id="bg-twk" class="star-layer">{_twinkle_html(31)}</div>'
    )
    anim = [
        ("#bg-far", "drift", 0.0, total, (-28, -16)),
        ("#bg-near", "drift", 0.0, total, (-64, -38)),
        ("#bg-neb", "drift", 0.0, total, (26, 16)),
    ]
    return html, anim


# ---------------------------------------------------------------- html

def el_attrs(eid, start, dur, track):
    return (f'id="{eid}" class="clip" data-layout-allow-overlap="true" '
            f'data-layout-allow-occlusion="true" data-start="{start:.3f}" '
            f'data-duration="{dur:.3f}" data-track-index="{track}"')


def pos_center(pos, size):
    cx, cy, _ = pos
    return f"left:{int(cx - size/2)}px;top:{int(cy - size/2)}px;width:{int(size)}px;height:{int(size)}px"


def build_html(ep, theme_name, audio=None, sfx_manifest=None, gsap_src=None, fontes_css=None):
    from referencias import validate_tokens
    t = {**THEMES.get(theme_name, THEMES["cartoon"]),
         **validate_tokens(ep.get("visual_tokens", {}))}
    total = ep["total"]
    seq = [1]

    def nid():
        seq[0] += 1
        return f"e{seq[0]}"
    out = []
    out.append("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"UTF-8\">")
    out.append('<meta name="viewport" content="width=1920, height=1080">')
    out.append(f"<title>{escape(str(ep.get('episode') or 'Catálogo'))}</title>")
    # Fontes locais quando há pin válido; sem isso o texto cai na fonte do
    # sistema e o render muda. As woff2 estão em vendor/fonts, com versão e
    # sha256 em vendor/PINS.json.
    if fontes_css:
        out.append(f'<link rel="stylesheet" href="{fontes_css}">')
    else:
        out.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
        out.append('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
        out.append(f'<link href="{t["fonts"]}" rel="stylesheet">')
    # GSAP local quando há pin válido: a timeline é o motor do render e não
    # pode depender de CDN. Sem o pin, cai na CDN e avisa (vendor.script_tag).
    out.append(f'<script src="{gsap_src or vendor.script_tag("gsap.min.js")}"></script>')
    out.append(f"<style>{THEME_CSS}</style></head><body>")
    out.append(f'<div id="root" data-composition-id="main" data-width="1920" data-height="1080" '
               f'data-duration="{total:.3f}">')

    # O fundo pertence à cena. Sem decoração global imposta ao episódio.
    anim = []

    if theme_name == "doodle":
        out.append(f'<div {el_attrs("doodlebar", 0.0, total, 2)} '
                   f'style="z-index:2;position:absolute;left:0;top:0;width:1920px;height:132px;'
                   f'background:#0b1c33;border-bottom:4px solid #1c3b63"></div>')
        anim.append(("#doodlebar", "none", 0.0, total))

    for el in ep["elements"]:
        kind = el["tipo"]
        if kind == "sfx":       # áudio: emitido como <audio> depois dos visuais
            continue
        start, dur = float(el["start"]), float(el["dur"])
        if kind in ("fundo", "fundo_seg"):
            palettes = {
                "azul": "radial-gradient(ellipse at 50% 35%,#102b49,#040b16 80%)",
                "petroleo": "radial-gradient(ellipse at 30% 45%,#10343a,#040e14 80%)",
                "ameixa": "radial-gradient(ellipse at 65% 40%,#30203e,#0c0814 80%)",
                "preto": "#05070d",
                "space": "radial-gradient(ellipse at 50% 40%,#122440,#04060c 80%)",
                "white": "radial-gradient(ellipse at 50% 35%,#102b49,#040b16 80%)",
            }
            eid = nid()
            bg = palettes.get(el.get("fundo"), palettes["preto"])
            out.append(f'<div {el_attrs(eid, start, dur, 1)} '
                       f'data-background="{escape(str(el.get("fundo", "preto")))}" '
                       f'style="z-index:1;position:absolute;inset:0;background:{bg};'
                       f'transform:scale({BG_ZOOM:.3f})"></div>')
            # Parallax ambiente: o fundo da cena respira durante toda a tomada. O
            # zoom abre a sangria para o drift não mostrar borda. Sem isso um
            # painel de 4 s cuja única animação é a entrada de 1,2 s congela o
            # quadro e viola a asserção `keepsMoving` que a própria composição
            # escreve em index.motion.json.
            anim.append((f"#{eid}", "drift", start, dur, BG_DRIFT))
            continue
        if kind == "titulo":
            eid = nid()
            top = t["title_top"]
            if theme_name == "doodle":
                out.append(f'<div {el_attrs(eid, start, dur, 32)} '
                           f'style="z-index:34;position:absolute;left:0;top:{top}px;width:1920px;'
                           f'text-align:center;font-family:{t["title_font"]};'
                           f'font-size:{t["title_size"]}px;color:{t["title_color"]};'
                           f'line-height:132px"><span class="tt">{escape(el["texto"])}</span></div>')
            else:
                out.append(f'<div {el_attrs(eid, start, dur, 32)} '
                           f'style="z-index:34;position:absolute;left:0;top:{top}px;width:1920px;'
                           f'text-align:center;font-family:{t["title_font"]};font-weight:800;'
                           f'font-size:{t["title_size"]}px;line-height:1.1">'
                       f'<span class="comic" style="color:{t["title_color"]}">'
                       f'{escape(el["texto"])}</span></div>')
            anim.append((f"#{eid}", "title_in", start, min(dur, 0.6)))
            anim.append((f"#{eid}", "out_fade", start + dur - 0.25, 0.25))
            continue
        if kind == "ilustra":
            key = ilustras.resolve(el.get("id", ""))
            if not key:
                continue
            eid = nid()
            size = int((el.get("size") or 780) * 1.25)
            from_pos = POS_MAP.get(el.get("pos", "centro"), POS_MAP["centro"])
            left, top = int(from_pos[0] - size / 2), int(from_pos[1] - size / 2)
            # `cresce` — o objeto nasce pequeno e cresce até o tamanho final, ligado
            # à fala (ex.: uma anã vermelha que aumenta, um raio que se expande).
            cres = el.get("cresce") or None
            base_scale = float(cres.get("de", 0.45)) if cres else 1.0
            # o transform é 100% do GSAP (o fromTo aplica o estado inicial sozinho);
            # só a ORIGEM fica no CSS para o crescimento sair do pé do objeto.
            img_transform = ";transform-origin:50% 68%" if cres else ""
            effect = str(el.get("effect") or "")
            if effect == "collapse":
                accent = ('<svg class="object-impact" viewBox="0 0 400 400" '
                          'style="position:absolute;inset:0;width:100%;height:100%;'
                          'pointer-events:none;opacity:0">'
                          '<path d="M52 324 L115 292 L96 353 M163 326 L202 281 L221 356 '
                          'M268 322 L330 291 L350 354" fill="none" stroke="#ffb02b" '
                          'stroke-width="12" stroke-linecap="round"/>'
                          '<circle cx="105" cy="318" r="19" fill="#dbe9fb"/>'
                          '<circle cx="302" cy="328" r="25" fill="#dbe9fb"/></svg>')
            elif effect == "flood":
                accent = ('<svg class="object-impact" viewBox="0 0 400 400" '
                          'style="position:absolute;inset:0;width:100%;height:100%;'
                          'pointer-events:none;opacity:0">'
                          '<path d="M0 310 Q70 275 140 310 T280 310 T420 310 '
                          'L420 400 H0Z" fill="#36aaf0" opacity=".75"/>'
                          '<path d="M0 305 Q70 270 140 305 T280 305 T420 305" '
                          'fill="none" stroke="#bfe6ff" stroke-width="10"/></svg>')
            else:
                accent = ""
            out.append(f'<div {el_attrs(eid, start, dur, 16)} '
                       f'style="z-index:16;position:absolute;left:{left}px;top:{top}px;'
                       f'width:{size}px;height:{size}px">'
                       f'<div class="object-entry" style="width:100%;height:100%">'
                       f'<img src="assets/ilustra/{key}.svg" '
                       f'style="width:100%;height:100%;object-fit:contain;'
                       f'filter:drop-shadow(0 22px 34px rgba(0,0,0,.55)){img_transform}">'
                       f'{accent}</div></div>')
            if cres:
                delay = float(cres.get("delay", 0.15))
                ate = float(cres.get("ate", 1.0))
                anim.append((f"#{eid} img", "grow",
                             start + delay, max(0.6, dur - delay - 0.2), (base_scale, ate)))
            else:
                anim.append((f"#{eid} .object-entry", el.get("entrada", "fade"), start, min(0.3, dur)))
                if effect == "collapse":
                    anim.append((f"#{eid} img", "object_collapse", start,
                                 min(dur, 1.4)))
                    anim.append((f"#{eid} .object-impact", "object_impact",
                                 start + min(0.25, dur * 0.25), min(dur, 0.9)))
                elif effect == "flood":
                    anim.append((f"#{eid} img", "kenburns", start, dur))
                    anim.append((f"#{eid} .object-impact", "object_flood",
                                 start, min(dur, 1.4)))
                elif effect == "spin":
                    anim.append((f"#{eid} img", "object_spin", start, dur))
                elif key in ("flame", "wildfire", "sun", "thermometer"):
                    anim.append((f"#{eid} img", "object_heat", start, dur))
                elif key in ("earthquake", "volcano", "lightning"):
                    anim.append((f"#{eid} img", "object_shake", start, dur))
                elif key in ("tornado", "hurricane", "storm", "blizzard"):
                    anim.append((f"#{eid} img", "object_sway", start, dur))
                elif key in ("water", "flood", "tsunami", "cloud"):
                    anim.append((f"#{eid} img", "object_wave", start, dur))
                else:
                    anim.append((f"#{eid} img", el.get("motion", "kenburns"), start, dur,
                                 el.get("motion_extra")))
            if el.get("move_to"):     # tela dividida: desliza para o lado
                tgt = POS_MAP.get(el["move_to"], from_pos)
                dx = int(tgt[0] - from_pos[0])
                ma = float(el.get("move_at") or (start + 0.5))
                anim.append((f"#{eid}", "move_x", max(start, ma), 0.55, dx))
            continue
        if kind == "mg":
            recipe = str(el.get("id") or "")
            if not mg.has(recipe):
                continue
            uid = nid()
            spec = mg.build(recipe, uid, el.get("params") or {})
            if not spec:
                continue
            vw, vh = spec["vb"]
            inner = spec["inner"]
            # texto dentro da cena/widget é intencional (rótulos, ticks, números):
            # marca para o layout-audit não acusar sobreposição com o overlay.
            inner = inner.replace(
                "<text ", '<text data-layout-allow-overlap="true" '
                          'data-layout-allow-occlusion="true" ')
            if spec["mode"] == "full":
                # A receita explica um fenômeno; nenhum sweep/zoom genérico por cima.
                out.append(f'<div {el_attrs(uid, start, dur, 5)} style="z-index:5;'
                           f'position:absolute;inset:0;overflow:hidden">'
                           f'<svg viewBox="0 0 {vw} {vh}" preserveAspectRatio="xMidYMid slice" '
                           f'style="width:100%;height:100%;display:block">{inner}</svg></div>')
            else:
                # widget de dados: cartão escuro posicionado como um objeto
                if vw >= vh * 1.25:
                    w = int(el.get("w") or 1180)
                elif vh > vw * 1.25:
                    w = int(el.get("w") or 560)
                else:
                    w = int(el.get("w") or 860)
                h = int(w * vh / vw)
                if h > 660:            # não deixa o cartão invadir a legenda
                    h = 660
                    w = int(h * vw / vh)
                cx, cy = POS_MAP.get(el.get("pos", "centro_alto"), POS_MAP["centro_alto"])
                left, top = int(cx - w / 2), int(cy - h / 2)
                out.append(f'<div {el_attrs(uid, start, dur, 16)} style="z-index:16;'
                           f'position:absolute;left:{left}px;top:{top}px;'
                           f'width:{w}px;height:{h}px;overflow:hidden;border-radius:26px">'
                           f'<div class="mg-card" style="position:absolute;inset:0"></div>'
                           f'<svg viewBox="0 0 {vw} {vh}" preserveAspectRatio="xMidYMid meet" '
                           f'style="position:absolute;inset:0;width:100%;height:100%">'
                           f'{inner}</svg>'
                           f'</div>')
                anim.append((f"#{uid} > svg", "fade", start, min(dur, 0.3)))
            for a in spec["anims"]:
                s = str(a.get("sel") or "")
                if not s:
                    continue
                ad = float(a.get("dur") or 0)
                delay = float(a.get("delay", 0.0))
                if spec["mode"] != "full" and a["kind"] in ("mg_once", "mg_count", "mg_draw"):
                    # O dado se constrói durante a fala e termina com leitura estável.
                    # Não precisa de brilho/flutuação para disfarçar um painel parado.
                    ad = max(0.1, dur - delay - min(0.5, dur * 0.2))
                anim.append((f"#{uid} > svg {s}".strip(), a["kind"],
                             start + delay,
                             ad if ad > 0 else dur, a))
                if a["kind"] == "mg_count":
                    # O próprio número ganha ênfase enquanto acumula; o painel
                    # fica estável. A auditoria de movimento mede geometria,
                    # não mudanças de textContent ou strokeDashoffset.
                    anim.append((f"#{uid} > svg {s}".strip(), "grow", start + delay,
                                 ad if ad > 0 else dur, (0.9, 1.0)))
            continue
        if kind == "imagens":
            ids = [ilustras.resolve(x) for x in el.get("ids", [])]
            ids = [k for k in ids if k]
            if not ids:
                continue
            eid = nid()
            n = len(ids)
            step = int(el.get("size") or 500)
            gap = 44
            row_w = n * step + (n - 1) * gap
            cell_h = int(step * 1.12)
            cx, cy = POS_MAP.get(el.get("pos", "centro"), POS_MAP["centro"])
            left, top = int(cx - row_w / 2), int(cy - cell_h / 2)
            cells = "".join(
                f'<div class="cell" style="width:{step}px;height:{cell_h}px">'
                f'<img src="assets/ilustra/{k}.svg" style="width:100%;height:100%;'
                f'object-fit:contain;filter:drop-shadow(0 22px 34px rgba(0,0,0,.55))"></div>'
                for k in ids)
            out.append(f'<div {el_attrs(eid, start, dur, 16)} style="z-index:16;'
                       f'position:absolute;left:{left}px;top:{top}px;width:{row_w}px;'
                       f'height:{cell_h}px;display:flex;align-items:center;'
                       f'justify-content:center;gap:{gap}px">{cells}</div>')
            anim.append((f"#{eid} img", el.get("entrada", "fade"), start, min(0.3, dur)))
            anim.append((f"#{eid}", "float", start, dur))
            for j in range(n):
                anim.append((f"#{eid} .cell:nth-child({j + 1})", "cell_in",
                             start + j * 0.13, 0.45))
            continue
        if kind == "transicao":
            eid = nid()
            cor = el.get("cor") or "#8fd4ff"
            out.append(f'<div {el_attrs(eid, start, dur, 35)} style="z-index:35;'
                       f'position:absolute;top:-140px;left:-760px;width:480px;height:1360px;'
                       f'pointer-events:none;opacity:0">'
                       f'<div class="sweep" style="background:linear-gradient(90deg,'
                       f'transparent, {cor}, #ffffff, {cor}, transparent)"></div></div>')
            anim.append((f"#{eid}", "sweep", start, max(0.5, dur)))
            continue
        if kind == "heroi":
            # um objeto SÓ na tela, grande e rápido (ex.: interrogação) — troca a cena
            eid = nid()
            key = ilustras.resolve(el.get("id", "")) or "star_generic"
            bg = el.get("bg", "preto")
            bgcol = {"branco": "#070b14", "preto": "#05070d", "space": "#04060c"}.get(bg, "#05070d")
            star = (f'<div class="star-layer">{_stars_svg(41, 130, .8, 2.0, glow=True)}</div>'
                    if bg == "space" else "")
            cap = el.get("texto") or ""
            caphtml = ""
            if cap:
                caphtml = (f'<div style="position:absolute;left:0;right:0;bottom:96px;'
                           f'text-align:center;font-family:{t["title_font"]};font-weight:800;'
                           f'font-size:{int(t["callout_size"] * .7)}px;white-space:nowrap">'
                           f'<span class="comic" data-layout-allow-overlap="true" '
                           f'data-layout-allow-occlusion="true" '
                           f'style="color:{t["title_color"]}">{escape(str(cap))}</span></div>')
            out.append(f'<div {el_attrs(eid, start, dur, 56)} style="z-index:56;'
                       f'position:absolute;inset:0;background:{bgcol};overflow:hidden;opacity:0">'
                       f'{star}<img src="assets/ilustra/{key}.svg" style="position:absolute;'
                       f'left:50%;top:50%;width:1440px;height:1440px;object-fit:contain;'
                       f'transform:translate(-50%,-50%);'
                       f'filter:drop-shadow(0 34px 64px rgba(0,0,0,.6))">{caphtml}</div>')
            anim.append((f"#{eid}", "fade", start, 0.18))
            anim.append((f"#{eid} img", "slam", start, 0.42))
            anim.append((f"#{eid} img", "hero_spin", start, max(0.8, dur)))
            anim.append((f"#{eid} img", "hero_pulse", start + 0.45,
                         max(0.6, min(dur - 0.8, 2.6))))
            anim.append((f"#{eid}", "out_fade", start + dur - 0.26, 0.26))
            continue
        if kind == "textao":
            # tela SÓ de texto/legenda, entrando e saindo rápido
            eid = nid()
            bg = el.get("bg", "branco")
            bgcol = {"branco": "#070b14", "preto": "#05070d"}.get(bg, "#070b14")
            txtcol = el.get("cor") or "#eaf6ff"
            out.append(f'<div {el_attrs(eid, start, dur, 56)} style="z-index:56;'
                       f'position:absolute;inset:0;background:{bgcol};overflow:hidden;opacity:0;'
                       f'display:flex;align-items:center;justify-content:center;padding:0 150px">'
                       f'<span class="textao" data-layout-allow-overlap="true" '
                       f'data-layout-allow-occlusion="true" style="color:{txtcol};'
                       f'font-family:{t["title_font"]}">{escape(str(el["texto"]))}</span></div>')
            anim.append((f"#{eid}", "fade", start, 0.16))
            anim.append((f"#{eid} .textao", "slam_txt", start, 0.42))
            anim.append((f"#{eid}", "out_fade", start + dur - 0.26, 0.26))
            continue
        if kind == "palavra":
            eid = nid()
            cx, cy = CALLOUT_MAP.get(el.get("pos", "acima"), CALLOUT_MAP["acima"])
            cor = el.get("cor") or "#ffd84a"
            fsize = int(t["callout_size"] * 0.72)
            out.append(f'<div {el_attrs(eid, start, dur, 34)} '
                       f'style="z-index:34;position:absolute;left:60px;top:{int(cy - 150)}px;'
                       f'width:1800px;text-align:center;font-family:{t["title_font"]};'
                       f'font-weight:800;font-size:{fsize}px;line-height:1.1;white-space:nowrap">'
                       f'<span class="pill" style="background:{cor}">'
                       f'{escape(str(el["texto"]))}</span></div>')
            anim.append((f"#{eid}", "pill_pop", start, 0.4))
            anim.append((f"#{eid}", "wiggle", start + 0.4, min(max(0.4, dur), 1.4)))
            anim.append((f"#{eid}", "out", start + dur - 0.22, 0.22))
            continue
        if kind in ("callout", "lista_item", "frase"):
            eid = nid()
            if kind == "callout":
                pos = el.get("pos", "baixo")
                cx, cy = CALLOUT_MAP.get(pos, CALLOUT_MAP["baixo"])
                cls = "comic" if t["comic"] else "doodle-txt"
                size = t["callout_size"]
                # callouts do mesmo segmento empilham PRA CIMA (nunca saem do quadro)
                cy = cy - int(el.get("slot", 0)) * int(size * 1.6)
                if pos in ("esq", "esquerda"):
                    left, width, align = 60, 820, "left"
                elif pos in ("dir", "direita"):
                    left, width, align = 1040, 820, "left"
                else:
                    left, width, align = 60, 1800, "center"
                wrap = "normal" if pos in ("esq", "esquerda", "dir", "direita") else "nowrap"
                sub = el.get("sub") or el.get("rotulo")
                txt = escape(str(el["texto"]))
                if sub:
                    # main + sub como BLOCOS empilhados; o glow do contorno invade a
                    # caixa vizinha (intencional), então marcamos allow-overlap também
                    # nos filhos — sem isto o gate acusa overlap falso.
                    ao = 'data-layout-allow-overlap="true" data-layout-allow-occlusion="true"'
                    inner = (f'<div class="{cls}" {ao} style="display:block;'
                             f'color:{t["callout_color"]}">{txt}</div>'
                             f'<div class="c-sub" {ao}>{escape(str(sub))}</div>')
                else:
                    inner = (f'<span class="{cls}" style="color:{t["callout_color"]}">'
                             f'{txt}</span>')
                out.append(f'<div {el_attrs(eid, start, dur, 30)} '
                           f'style="z-index:30;position:absolute;left:{left}px;top:{int(cy-190)}px;'
                           f'width:{width}px;text-align:{align};font-family:{t["title_font"]};'
                           f'font-weight:800;font-size:{size}px;line-height:1.05;'
                           f'white-space:{wrap}"><div class="callout-content">{inner}</div></div>')
                anim.append((f"#{eid}", el.get("entrada", "pop"), start, min(dur, 0.45)))
                if dur > 2.5:
                    anim.append((f"#{eid} .callout-content", "drift", start, dur, (24, -12)))
                anim.append((f"#{eid}", "out", start + dur - 0.22, 0.22))
            elif kind == "lista_item":
                cx, cy = CALLOUT_MAP.get(el.get("pos", "dir"), CALLOUT_MAP["dir"])
                cls = "comic" if t["comic"] else "doodle-txt"
                idx = int(el.get("indice", 0))
                left = 1010 if el.get("pos", "dir") in ("dir", "direita") else 150
                top = 300 + idx * int(t["list_size"] * 1.7)
                out.append(f'<div {el_attrs(eid, start, dur, 30)} '
                           f'style="z-index:30;position:absolute;left:{left}px;top:{top}px;'
                           f'width:800px;font-family:{t["title_font"]};font-weight:800;'
                           f'font-size:{t["list_size"]}px">'
                           f'<span class="{cls}" style="color:{t["list_color"]}">'
                           f'{escape(str(el["texto"]))}</span></div>')
                anim.append((f"#{eid}", "slide_in", start, min(dur, 0.4)))
                anim.append((f"#{eid}", "out", start + dur - 0.22, 0.22))
            else:  # frase: centro = declaração; lado = acompanha um objeto
                cls = "comic" if t["comic"] else "doodle-txt"
                fpos = str(el.get("pos") or "centro")
                if fpos.startswith("esq"):
                    fl, fw, ftop = 70, 850, 330
                elif fpos.startswith("dir"):
                    fl, fw, ftop = 1000, 850, 330
                elif fpos in ("baixo", "legenda"):
                    fl, fw, ftop = 0, 1920, 880      # legenda abaixo de dois objetos
                else:
                    fl, fw, ftop = 0, 1920, 400
                fscale = 0.60 if fl else (0.72 if ftop >= 850 else 1.0)
                fsize = int(t["frase_size"] * fscale)
                falign = "left" if fl else "center"
                # A caixa da faixa precisa incluir as métricas reais da Baloo 2
                # (ascendentes/descendentes ultrapassam a line-height nominal).
                # O deslocamento mantém o texto na mesma posição visual.
                if fpos in ("baixo", "legenda"):
                    ftop -= 22
                    backing = 'background:rgba(3,9,22,.86);padding:30px 0 28px;'
                else:
                    backing = ''
                out.append(f'<div {el_attrs(eid, start, dur, 32)} '
                           f'style="z-index:32;position:absolute;left:{fl}px;top:{ftop}px;'
                           f'width:{fw}px;text-align:{falign};font-family:{t["title_font"]};'
                           f'font-weight:800;font-size:{fsize}px;line-height:1.06;{backing}">'
                           f'<span class="{cls}" style="color:{t["frase_color"]}">'
                           f'{escape(str(el["texto"]))}</span></div>')
                anim.append((f"#{eid}", "frase_in", start, min(dur, 0.36)))
                anim.append((f"#{eid}", "out", start + dur - 0.2, 0.2))
            continue
        if kind == "mascote":
            eid = nid()
            left, top, size = 1300, 470, 600
            mpos = el.get("pos")
            if mpos in ("canto_bd", "canto_baixo_direita"):
                left, top, size = 1490, 660, 360
            elif mpos in ("canto_be", "canto_baixo_esquerda"):
                left, top, size = 70, 660, 360
            out.append(f'<div {el_attrs(eid, start, dur, 40)} '
                       f'style="z-index:40;position:absolute;left:{left}px;top:{top}px;'
                       f'width:{size}px;height:{size}px">'
                       f'<img src="assets/ilustra/mascot.svg" '
                       f'style="width:100%;height:100%;object-fit:contain;'
                       f'filter:drop-shadow(0 20px 30px rgba(0,0,0,.5))"></div>')
            anim.append((f"#{eid}", "slide_in", start, 0.5))
            anim.append((f"#{eid}", "float", start, dur))
            anim.append((f"#{eid}", "out", start + dur - 0.3, 0.3))
            continue
        if kind in ("grafico", "barra", "medidor", "comparacao"):
            eid = nid()
            gpos = POS_MAP.get(el.get("pos", "centro"), POS_MAP["centro"])
            cw = int(el.get("w") or 1500)
            left = int(gpos[0] - cw / 2)
            unidade = str(el.get("unidade") or "")
            cor_def = el.get("cor") or "#29a8ff"
            rot = el.get("rotulo") or ""

            if kind == "grafico":
                itens = el.get("itens") or []
                if not itens:
                    continue
                titulo = el.get("titulo") or ""
                maxv = float(el.get("max") or 0)
                if maxv <= 0:
                    maxv = max([float(it.get("fim", it.get("valor", it.get("ini", 0))) or 0)
                                for it in itens] + [1.0])
                rows = []
                for it in itens:
                    ini = float(it.get("ini", it.get("valor", 0)) or 0)
                    fim = it.get("fim")
                    cor = it.get("cor") or cor_def
                    if fim is not None:
                        fv = float(fim)
                        a, b = 100.0 * ini / maxv, 100.0 * fv / maxv
                        valtxt = it.get("valor_txt") or \
                            f"{_num(ini)}–{_num(fv)} {unidade}".strip()
                    else:
                        a, b = 0.0, 100.0 * ini / maxv
                        valtxt = it.get("valor_txt") or f"{_num(ini)} {unidade}".strip()
                    rows.append(
                        f'<div class="bar-row"><div class="bar-label">'
                        f'{escape(str(it.get("rotulo", "")))}</div>'
                        f'<div class="bar-track"><div class="bar-fill" '
                        f'style="left:{a:.2f}%;width:{max(0.6, b - a):.2f}%;'
                        f'background:{cor};transform-origin:left center"></div></div>'
                        f'<div class="bar-val">{escape(valtxt)}</div></div>')
                inner = ((f'<div class="chart-title">{escape(titulo)}</div>' if titulo else "")
                         + f'<div class="bars">{"".join(rows)}</div>')
                est_h = 80 + len(itens) * 74
                top = int(gpos[1] - est_h / 2)
                out.append(f'<div {el_attrs(eid, start, dur, 30)} style="z-index:30;'
                           f'position:absolute;left:{left}px;top:{top}px;width:{cw}px">'
                           f'<div class="hf-card" style="padding:30px 42px">{inner}</div></div>')
                for i in range(len(itens)):
                    at = start + 0.12 + i * 0.11
                    anim.append((f"#{eid} .bars .bar-row:nth-child({i + 1}) .bar-fill",
                                 "bar_grow", at, min(0.55, dur)))
                    anim.append((f"#{eid} .bars .bar-row:nth-child({i + 1}) .bar-val",
                                 "pop_y", at + 0.2, 0.28))
                anim.append((f"#{eid}", "float", start, dur))
                anim.append((f"#{eid}", "out_fade", start + dur - 0.25, 0.25))
                continue

            if kind == "barra":
                valor = float(el.get("valor", 0) or 0)
                maxv = float(el.get("max", 100) or 100)
                pct = max(0.0, min(1.0, valor / maxv))
                cor = el.get("cor") or cor_def
                big = el.get("texto") or f"{_num(valor)}{unidade}"
                top = int(gpos[1] - 130)
                out.append(f'<div {el_attrs(eid, start, dur, 30)} style="z-index:30;'
                           f'position:absolute;left:{left}px;top:{top}px;width:{cw}px">'
                           f'<div class="hf-card" style="padding:34px 46px">'
                           f'<div class="gauge-val comic" style="color:{cor}">'
                           f'{escape(str(big))}</div>'
                           f'<div class="gauge-track"><div class="gauge-fill" '
                           f'style="width:{pct * 100:.2f}%;background:linear-gradient(90deg,'
                           f'{cor},#ffffff);transform-origin:left center"></div></div>'
                           + (f'<div class="gauge-rot">{escape(str(rot))}</div>' if rot else "")
                           + '</div></div>')
                anim.append((f"#{eid} .gauge-val", "pop", start + 0.08, 0.32))
                anim.append((f"#{eid} .gauge-fill", "bar_grow", start + 0.24, min(0.8, dur)))
                if rot:
                    anim.append((f"#{eid} .gauge-rot", "pop_y", start + 0.55, 0.3))
                anim.append((f"#{eid}", "float", start, dur))
                anim.append((f"#{eid}", "out_fade", start + dur - 0.25, 0.25))
                continue

            if kind == "medidor":
                minv = float(el.get("min", 0) or 0)
                maxv = float(el.get("max", 100) or 100)
                ini = float(el.get("ini", minv) or minv)
                fim = float(el.get("fim", maxv) or maxv)
                span = (maxv - minv) or 1.0
                a = max(0.0, min(100.0, 100.0 * (ini - minv) / span))
                b = max(0.0, min(100.0, 100.0 * (fim - minv) / span))
                cor = el.get("cor") or cor_def
                big = el.get("texto") or f"{_num(ini)} a {_num(fim)} {unidade}".strip()
                top = int(gpos[1] - 150)
                out.append(f'<div {el_attrs(eid, start, dur, 30)} style="z-index:30;'
                           f'position:absolute;left:{left}px;top:{top}px;width:{cw}px">'
                           f'<div class="hf-card" style="padding:34px 46px">'
                           f'<div class="gauge-val comic" style="color:{cor}">'
                           f'{escape(str(big))}</div>'
                           f'<div class="meter-track">'
                           f'<div class="meter-fill" style="left:{a:.2f}%;'
                           f'width:{max(0.6, b - a):.2f}%;background:linear-gradient(90deg,'
                           f'{cor},#ffffff);transform-origin:left center"></div>'
                           f'<div class="meter-tick" style="left:{a:.2f}%"></div>'
                           f'<div class="meter-tick" style="left:{b:.2f}%"></div></div>'
                           f'<div class="meter-ends"><span>'
                           f'{escape(el.get("min_txt") or _num(minv))}</span><span>'
                           f'{escape(el.get("max_txt") or _num(maxv))} {escape(unidade)}</span>'
                           f'</div>'
                           + (f'<div class="gauge-rot">{escape(str(rot))}</div>' if rot else "")
                           + '</div></div>')
                anim.append((f"#{eid} .gauge-val", "pop", start + 0.08, 0.32))
                anim.append((f"#{eid} .meter-fill", "bar_grow", start + 0.24, min(0.85, dur)))
                anim.append((f"#{eid}", "float", start, dur))
                anim.append((f"#{eid}", "out_fade", start + dur - 0.25, 0.25))
                continue

            # comparacao — linha de objetos em escala relativa (do menor ao maior)
            itens = [it for it in (el.get("itens") or [])
                     if ilustras.resolve(it.get("id", ""))]
            if not itens:
                continue
            base = int(el.get("size") or 620)
            gap = 40
            cell_w = max(int(base * float(it.get("escala", 1))) for it in itens)
            row_w = len(itens) * cell_w + (len(itens) - 1) * gap
            left = int(gpos[0] - row_w / 2)
            base_y = int(el.get("base_y") or 850)
            cells, labels = [], []
            for it in itens:
                key = ilustras.resolve(it["id"])
                bw = int(base * float(it.get("escala", 1)))
                cells.append(
                    f'<div class="cmp-cell" style="width:{cell_w}px">'
                    f'<img src="assets/ilustra/{key}.svg" style="width:{bw}px;height:{bw}px;'
                    f'object-fit:contain;transform-origin:50% 100%;'
                    f'filter:drop-shadow(0 20px 30px rgba(0,0,0,.55))"></div>')
                labels.append(f'<div class="cmp-cell cmp-lab" style="width:{cell_w}px">'
                              f'{escape(str(it.get("rotulo", "")))}</div>')
            out.append(f'<div {el_attrs(eid, start, dur, 30)} style="z-index:30;'
                       f'position:absolute;left:{left}px;top:{base_y - base - 30}px;'
                       f'width:{row_w}px;display:flex;align-items:flex-end;'
                       f'justify-content:center;gap:{gap}px">{"".join(cells)}</div>')
            out.append(f'<div {el_attrs(eid + "l", start, dur, 30)} style="z-index:30;'
                       f'position:absolute;left:{left}px;top:{base_y + 6}px;width:{row_w}px;'
                       f'display:flex;justify-content:center;gap:{gap}px">'
                       f'{"".join(labels)}</div>')
            for j in range(len(itens)):
                at = start + 0.08 + j * 0.22
                anim.append((f"#{eid} .cmp-cell:nth-child({j + 1}) img", "grow",
                             at, 0.42, (0.12, 1.0)))
            anim.append((f"#{eid}", "float", start, dur))
            anim.append((f"#{eid}", "out_fade", start + dur - 0.25, 0.25))
            anim.append((f"#{eid}l", "out_fade", start + dur - 0.25, 0.25))
            continue
        if kind in ("foto", "video"):
            eid = nid()
            x, y = int(el.get("x", 0)), int(el.get("y", 0))
            w, h = int(el.get("w", 1920)), int(el.get("h", 1080))
            src = str(el.get("src", ""))
            if kind == "foto":
                out.append(f'<img {el_attrs(eid, start, dur, 16)} src="{escape(src)}" '
                           f'style="z-index:16;position:absolute;left:{x}px;top:{y}px;'
                           f'width:{w}px;height:{h}px;object-fit:cover;'
                           f'border-radius:{int(el.get("radius", 18))}px;'
                           f'box-shadow:0 24px 50px rgba(0,0,0,.5)">')
            else:
                out.append(f'<video {el_attrs(eid, start, dur, 16)} src="{escape(src)}" muted '
                           f'playsinline data-media-start="{float(el.get("media_start", 0)):.2f}" '
                           f'style="z-index:16;position:absolute;left:{x}px;top:{y}px;'
                           f'width:{w}px;height:{h}px;object-fit:cover;'
                           f'border-radius:{int(el.get("radius", 18))}px;'
                           f'box-shadow:0 24px 50px rgba(0,0,0,.5)"></video>')
            anim.append((f"#{eid}", "fade", start, min(dur, 0.45)))
            anim.append((f"#{eid}", "out", start + dur - 0.28, 0.28))
            continue

    if audio:
        # preload=none: WAVs longos (>100 MB) não podem bloquear o load event
        # do Playwright (timeout fixo de 10 s no snapshot/render).
        out.append(f'<audio id="narration" src="{escape(audio)}" preload="none" data-start="0" '
                   f'data-duration="{total:.3f}" data-track-index="90" data-volume="1"></audio>')

    # efeitos sonoros: acentos pontuais (transições, revelações), NUNCA em todo corte
    if sfx_manifest:
        for i, el in enumerate(ep["elements"]):
            if el.get("tipo") != "sfx":
                continue
            meta = sfx_manifest.get(str(el.get("nome", "")))
            if not meta:
                continue
            start = max(0.0, float(el.get("start", 0.0)))
            gain = float(el.get("gain", 0.35))
            dur = min(float(meta.get("duration", 1.0)), max(0.3, total - start))
            out.append(f'<audio id="sfx{i}" src="assets/sfx/{escape(meta["file"])}" '
                       f'data-start="{start:.3f}" data-duration="{dur:.3f}" '
                       f'data-track-index="91" data-volume="{gain:.2f}"></audio>')

    out.append("</div>")
    out.append('<script>window.__timelines=window.__timelines||{};')
    out.append("document.fonts&&document.fonts.ready;const tl=gsap.timeline({paused:true});")
    for item in anim:
        sel, kind, at, dur = item[0], item[1], item[2], item[3]
        extra = item[4] if len(item) > 4 else None
        out.append(anim_js(sel, kind, max(0.0, at), max(0.05, dur), extra))
    out.append('window.__timelines["main"]=tl;')
    out.append("</script></body></html>")
    return "\n".join(out)


POS_MAP = {
    "centro": (960, 560), "centro_alto": (960, 490), "centro_baixo": (960, 700),
    "esquerda": (520, 560), "direita": (1400, 560),
}
CALLOUT_MAP = {
    "baixo": (960, 870), "acima": (960, 600), "esq": (470, 700), "dir": (1450, 700),
    "centro": (960, 560), "topo": (960, 380),
    "legenda": (960, 1000),   # faixa de destaque da palavra (abaixo dos objetos)
}


def anim_js(sel, kind, at, dur, extra=None):
    if kind == "none":
        return ""
    if kind == "intro_push":
        return (f'tl.fromTo("{sel}",{{scale:1.06}},'
                f'{{scale:1,duration:{dur:.2f},ease:"sine.out"}},{at});')
    if kind == "object_collapse":
        fall = max(0.2, min(0.65, dur * 0.5))
        return (f'tl.fromTo("{sel}",{{x:-12,rotation:-2}},'
                f'{{x:12,rotation:2,duration:.09,repeat:3,yoyo:true,immediateRender:false}},{at});'
                f'tl.to("{sel}",{{y:180,rotation:22,scale:.7,opacity:0,'
                f'duration:{fall:.2f},ease:"power3.in"}},{at + min(0.4, dur * 0.35):.3f});')
    if kind == "object_impact":
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:.6}},'
                f'{{opacity:1,scale:1.25,duration:{max(0.2, dur):.2f},'
                f'ease:"power2.out",immediateRender:false}},{at});')
    if kind == "object_flood":
        return (f'tl.fromTo("{sel}",{{opacity:0,y:130}},'
                f'{{opacity:1,y:0,duration:{max(0.2, dur):.2f},'
                f'ease:"power2.out",immediateRender:false}},{at});')
    if kind == "object_spin":
        return (f'tl.fromTo("{sel}",{{rotation:-20,scale:.75}},'
                f'{{rotation:340,scale:1.08,duration:{max(0.2, dur):.2f},'
                f'ease:"power2.out",immediateRender:false}},{at});')
    if kind == "object_heat":
        return (f'tl.fromTo("{sel}",{{scale:.88,rotation:-3}},'
                f'{{scale:1.12,rotation:3,duration:{max(0.18, dur/4):.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:3,immediateRender:false}},{at});')
    if kind == "object_shake":
        return (f'tl.fromTo("{sel}",{{x:-13,rotation:-4}},'
                f'{{x:13,rotation:4,duration:{max(0.09, dur/12):.2f},'
                f'ease:"none",yoyo:true,repeat:11,immediateRender:false}},{at});')
    if kind == "object_sway":
        return (f'tl.fromTo("{sel}",{{x:-34,rotation:-8,scale:.94}},'
                f'{{x:34,rotation:8,scale:1.06,duration:{max(0.25, dur/4):.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:3,immediateRender:false}},{at});')
    if kind == "object_wave":
        return (f'tl.fromTo("{sel}",{{y:20,rotation:-6}},'
                f'{{y:-20,rotation:6,duration:{max(0.25, dur/4):.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:3,immediateRender:false}},{at});')
    if kind == "drift":
        ex, ey = extra or (0, 0)
        return (f'tl.fromTo("{sel}",{{x:0,y:0}},'
                f'{{x:{ex},y:{ey},duration:{dur:.2f},ease:"none"}},{at});')
    if kind == "twinkle":
        reps = int(extra) if extra is not None else 60
        return (f'tl.fromTo("{sel}",{{opacity:.08,scale:.5}},'
                f'{{opacity:1,scale:1,duration:{dur:.2f},ease:"sine.inOut",'
                f'yoyo:true,repeat:{reps}}},{at});')
    if kind == "kenburns":
        return (f'tl.fromTo("{sel}",{{scale:1}},{{scale:1.08,duration:{dur:.2f},'
                f'ease:"sine.inOut"}},{at});')
    if kind == "move_x":
        return f'tl.to("{sel}",{{x:{int(extra or 0)},duration:{dur:.2f},ease:"power2.inOut"}},{at});'
    if kind == "grow":
        de, ate = extra or (0.4, 1.0)
        return (f'tl.fromTo("{sel}",{{scale:{float(de):.3f}}},'
                f'{{scale:{float(ate):.3f},duration:{dur:.2f},ease:"power1.inOut"}},{at});')
    if kind == "bar_grow":
        return (f'tl.fromTo("{sel}",{{scaleX:0}},{{scaleX:1,duration:{dur:.2f},'
                f'ease:"power2.out"}},{at});')
    if kind == "pop_y":
        return (f'tl.fromTo("{sel}",{{opacity:0,y:18}},'
                f'{{opacity:1,y:0,duration:{dur:.2f},ease:"back.out(1.6)"}},{at});')
    if kind == "slam":
        return (f'tl.fromTo("{sel}",{{scale:1.75,opacity:0}},'
                f'{{scale:1,opacity:1,duration:{dur:.2f},ease:"back.out(1.6)"}},{at});')
    if kind == "hero_spin":
        return (f'tl.fromTo("{sel}",{{rotate:-6}},{{rotate:6,duration:{dur:.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:1}},{at});')
    if kind == "hero_pulse":
        return (f'tl.fromTo("{sel}",{{scale:1}},{{scale:1.08,duration:{dur:.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:1}},{at});')
    if kind == "slam_txt":
        return (f'tl.fromTo("{sel}",{{scale:.7,opacity:0,y:24}},'
                f'{{scale:1,opacity:1,y:0,duration:{dur:.2f},ease:"back.out(1.7)"}},{at});')
    if kind == "cell_in":
        return (f'tl.fromTo("{sel}",{{opacity:0,y:44,scale:.84}},'
                f'{{opacity:1,y:0,scale:1,duration:.30,ease:"back.out(1.5)"}},{at});')
    if kind == "sweep":
        return (f'tl.fromTo("{sel}",{{x:0,opacity:0}},'
                f'{{x:2760,opacity:.65,duration:{dur:.2f},ease:"power2.inOut"}},{at});')
    if kind == "title_in":
        return (f'tl.fromTo("{sel}",{{opacity:0,y:-40}},'
                f'{{opacity:1,y:0,duration:.38,ease:"back.out(1.6)"}},{at});')
    if kind == "pop":
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:.62}},'
                f'{{opacity:1,scale:1,duration:.30,ease:"back.out(1.9)"}},{at});')
    if kind == "pill_pop":
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:.55,y:26}},'
                f'{{opacity:1,scale:1,y:0,duration:.30,ease:"back.out(2.1)"}},{at});')
    if kind == "wiggle":
        return (f'tl.fromTo("{sel}",{{rotate:-2.5}},{{rotate:2.5,duration:{dur:.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:1}},{at});')
    if kind == "cut_pop":
        # corte seco: já entra visível, só assenta a escala (sem piscar)
        return (f'tl.fromTo("{sel}",{{opacity:1,scale:.90}},'
                f'{{opacity:1,scale:1,duration:.22,ease:"power2.out",immediateRender:false}},{at});')
    if kind == "slide_in":
        return (f'tl.fromTo("{sel}",{{opacity:0,x:-46}},'
                f'{{opacity:1,x:0,duration:.28,ease:"power3.out"}},{at});')
    if kind == "frase_in":
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:.9,y:16}},'
                f'{{opacity:1,scale:1,y:0,duration:.34,ease:"power2.out"}},{at});')
    if kind == "fade":
        return f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:.3,ease:"power1.out"}},{at});'
    if kind == "float":
        return (f'tl.fromTo("{sel}",{{y:0}},{{y:-14,duration:{max(1.0,dur/2):.2f},'
                f'ease:"sine.inOut",yoyo:true,repeat:1,immediateRender:false}},{at});')
    if kind == "out":
        return f'tl.to("{sel}",{{opacity:0,y:-14,duration:.18,ease:"power2.in"}},{at});'
    if kind == "out_fade":
        return f'tl.to("{sel}",{{opacity:0,duration:.28,ease:"power1.in"}},{at});'
    # ---- motion graphics (mg.py) ----
    if kind == "mg_loop":
        frm = extra.get("frm") or {}
        to = dict(extra.get("to") or {})
        cyc = max(0.2, float(extra.get("cycle", 2.0)))
        ease = extra.get("ease", "none")
        yoyo = bool(extra.get("yoyo", False))
        reps = max(0, int(dur / cyc) - (1 if yoyo else 0))
        to.update({"duration": round(cyc, 2), "ease": ease, "repeat": reps,
                   "immediateRender": False})
        if yoyo:
            to["yoyo"] = True
        org = extra.get("origin")
        if org:
            to["svgOrigin"] = org
        return f'tl.fromTo("{sel}",{json.dumps(frm)},{json.dumps(to)},{at});'
    if kind in ("mg_once", "mg_grow_y", "mg_bar", "mg_turn"):
        frm = extra.get("frm")
        to = extra.get("to")
        if kind == "mg_grow_y" and frm is None:
            frm, to = {"scaleY": 0}, {"scaleY": 1}
        if kind == "mg_bar" and frm is None:
            frm, to = {"scaleX": 0}, {"scaleX": 1}
        frm = frm or {}
        to = dict(to or {})
        to["duration"] = round(max(0.05, dur), 3)
        to["ease"] = extra.get("ease", "power2.out")
        to["immediateRender"] = False
        org = extra.get("origin")
        if org:
            to["svgOrigin"] = org
        return f'tl.fromTo("{sel}",{json.dumps(frm)},{json.dumps(to)},{at});'
    if kind == "mg_draw":
        frm = extra.get("frm") or {"strokeDashoffset": 1}
        to = dict(extra.get("to") or {"strokeDashoffset": 0})
        to["duration"] = round(max(0.05, dur), 3)
        to["ease"] = extra.get("ease", "power1.inOut")
        to["immediateRender"] = False
        return f'tl.fromTo("{sel}",{json.dumps(frm)},{json.dumps(to)},{at});'
    if kind == "mg_count":
        tv = float(extra.get("to", 0) or 0)
        pre = str(extra.get("prefix", ""))
        suf = str(extra.get("suffix", ""))
        ease = extra.get("ease", "power2.out")
        # alvo é o PRÓPRIO elemento (não um objeto JS): o runtime do HyperFrames
        # percorre os alvos do timeline e não lida bem com objetos puros.
        # conta pelo PROGRESSO do tween (não guarda estado em propriedade): robusto
        # em qualquer runtime e determinístico ao buscar (seek).
        return (f'tl.fromTo("{sel}",{{opacity:1}},{{opacity:1,duration:{max(0.05, dur):.2f},'
                f'immediateRender:false,'
                f'ease:"{ease}",onUpdate:function(){{'
                f'var e=this.targets()[0];'
                f'e.textContent="{pre}"+Math.round(this.progress()*{tv})'
                f'.toLocaleString("pt-BR")+"{suf}";'
                f'}}}},{at});')
    return ""


THEME_CSS = """
body{margin:0;background:#04060c;font-family:'Nunito',sans-serif}
#root{position:relative;width:1920px;height:1080px;overflow:hidden}
.star-layer{position:absolute;left:-140px;top:-100px;width:2200px;height:1280px;
  will-change:transform}
.star-layer svg{display:block}
.tw{position:absolute;border-radius:50%;will-change:transform,opacity;
  background:radial-gradient(circle,#fff 0%,rgba(180,215,255,.55) 42%,transparent 72%)}
.sweep{position:absolute;inset:0;transform:skewX(-18deg);filter:blur(2px)}
.comic{display:inline-block;text-shadow:
  0 0 3px #ffffff,
  5px 0 0 #0d1b2a, -5px 0 0 #0d1b2a, 0 5px 0 #0d1b2a, 0 -5px 0 #0d1b2a,
  4px 4px 0 #0d1b2a, -4px 4px 0 #0d1b2a, 4px -4px 0 #0d1b2a, -4px -4px 0 #0d1b2a,
  0 0 22px rgba(96,190,255,.95), 0 8px 34px rgba(40,120,255,.6)}
.doodle-txt{display:inline-block;text-shadow:2px 2px 0 #fff,-1px -1px 0 #fff,1px -1px 0 #fff,-1px 1px 0 #fff}
.tt{display:inline-block}
.textao{display:inline-block;font-weight:800;font-size:150px;line-height:1.05;text-align:center}
.pill{display:inline-block;padding:.05em .32em;border-radius:.22em;color:#0b1420;
  box-shadow:0 12px 32px rgba(0,0,0,.5),0 0 30px rgba(255,255,255,.28);
  text-shadow:0 2px 0 rgba(255,255,255,.4)}
.c-sub{display:block;font-family:'Nunito',sans-serif;font-weight:800;font-size:.46em;
  letter-spacing:.06em;color:#eaf6ff;text-shadow:0 4px 0 #0d1b2a,0 0 18px rgba(96,190,255,.95);
  margin-top:.10em}
/* ---- motion graphics: gráfico de barras, medidor, barra, comparação ---- */
.hf-card{background:rgba(6,13,26,.96);border:3px solid rgba(120,190,255,.4);
  border-radius:24px;box-shadow:0 30px 70px rgba(0,0,0,.6);font-family:'Nunito',sans-serif}
.mg-card{background:radial-gradient(120% 140% at 50% 0%,rgba(15,34,58,.97) 0%,
  rgba(6,13,26,.97) 70%);border:3px solid rgba(120,190,255,.35);border-radius:26px;
  box-shadow:0 30px 70px rgba(0,0,0,.6),inset 0 0 40px rgba(40,110,200,.12)}
.mg-sweep{position:absolute;top:0;left:0;width:360px;height:100%;pointer-events:none;
  will-change:transform;background:linear-gradient(100deg,transparent,
  rgba(170,215,255,.16),transparent);filter:blur(8px)}
.mg-sheen{position:absolute;top:0;left:0;width:240px;height:100%;pointer-events:none;
  border-radius:26px;will-change:transform;mix-blend-mode:screen;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.22),transparent)}
.chart-title{font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;color:#8fd4ff;
  font-size:36px;letter-spacing:.03em;text-align:center;margin-bottom:14px}
.bar-row{display:flex;align-items:center;gap:18px;margin:9px 0}
.bar-label{flex:0 0 440px;text-align:right;font-weight:800;color:#eaf6ff;font-size:30px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{position:relative;flex:1;height:46px;border-radius:12px;
  background:rgba(255,255,255,.10);border:2px solid rgba(255,255,255,.16);overflow:hidden}
.bar-fill{position:absolute;top:0;height:100%;border-radius:10px;
  box-shadow:0 0 18px rgba(255,255,255,.25)}
.bar-val{flex:0 0 190px;font-weight:800;color:#fff;font-size:30px;white-space:nowrap}
.gauge-val{font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;font-size:96px;
  text-align:center;line-height:1}
.gauge-track{position:relative;height:56px;border-radius:14px;margin-top:22px;
  background:rgba(255,255,255,.10);border:2px solid rgba(255,255,255,.16);overflow:hidden}
.gauge-fill{position:absolute;left:0;top:0;height:100%;border-radius:12px}
.gauge-rot{margin-top:18px;text-align:center;font-weight:800;color:#cfe6ff;font-size:32px}
.meter-track{position:relative;height:56px;border-radius:14px;margin-top:22px;
  background:linear-gradient(90deg,#1b3a63,#2b6fbf,#ffd84a,#ff6a4a);overflow:hidden}
.meter-fill{position:absolute;top:0;height:100%;border-radius:12px;
  box-shadow:0 0 22px rgba(255,255,255,.5)}
.meter-tick{position:absolute;top:-10px;width:4px;height:76px;background:#fff;
  transform:translateX(-2px);box-shadow:0 0 10px #fff}
.meter-ends{display:flex;justify-content:space-between;margin-top:12px;
  font-weight:800;color:#9fc4ec;font-size:26px}
.cmp-cell{display:flex;align-items:flex-end;justify-content:center}
.cmp-lab{margin-top:10px;font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;
  color:#eaf6ff;font-size:30px;text-align:center;text-shadow:0 3px 0 #0d1b2a}
"""


def bounded_episode(ep, seconds):
    """Cria um spec curto para demonstração sem carregar cenas fora do intervalo."""
    limit = float(seconds)
    if limit <= 0 or limit > float(ep["total"]):
        raise ValueError("--seconds deve estar entre 0 e a duração do episódio")
    bounded = {**ep, "total": limit, "elements": []}
    for element in ep["elements"]:
        start = float(element.get("start", 0.0))
        if start >= limit:
            continue
        current = element.copy()
        if "dur" in current:
            current["dur"] = round(min(float(current["dur"]), limit - start), 3)
            if current["dur"] <= 0:
                continue
        bounded["elements"].append(current)
    return bounded


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--spec", default="episode.json")
    ap.add_argument("--theme", default=None)
    ap.add_argument("--out-dir", default="hyperframes")
    ap.add_argument("--seconds", type=float, default=None,
                    help="gera só os primeiros N segundos, para demonstração rápida")
    a = ap.parse_args()
    proj = a.project
    with open(os.path.join(proj, a.spec), encoding="utf-8") as source:
        ep = json.load(source)
    from referencias import load_references
    from pathlib import Path
    ep["visual_tokens"] = {**ep.get("visual_tokens", {}),
                           **load_references(Path(proj) / "referencias")}
    if a.seconds is not None:
        ep = bounded_episode(ep, a.seconds)
    theme = a.theme or ep.get("theme") or "cartoon"
    dest = os.path.join(proj, a.out_dir)
    os.makedirs(os.path.join(dest, "assets", "ilustra"), exist_ok=True)
    # As fontes só entram no HTML depois de copiadas; se a cópia falhar, o
    # HTML aponta para um CSS inexistente. Por isso resolvemos antes.
    fontes_css = vendor.CSS_DEST if vendor.available() and vendor.tem_fontes() else None

    # exporta as ilustrações usadas (inclusive as que entram lado a lado em `imagens`)
    used = set()
    for e in ep["elements"]:
        if e["tipo"] == "ilustra":
            used.add(ilustras.resolve(e.get("id", "")))
        elif e["tipo"] == "imagens":
            used.update(ilustras.resolve(i) for i in e.get("ids", []))
        elif e["tipo"] == "comparacao":
            used.update(ilustras.resolve(it.get("id", "")) for it in e.get("itens", []))
    used = [u for u in sorted(used) if u]
    if any(e["tipo"] == "mascote" for e in ep["elements"]):
        used.append("mascot")
    for key in sorted(set(used)):
        svg = ilustras.render(key, size=820)
        with open(os.path.join(dest, "assets", "ilustra", f"{key}.svg"),
                  "w", encoding="utf-8") as output:
            output.write(svg)

    # A versão do spec determina a versão do áudio. Sem versão (spec legado),
    # só aceitamos escolha automática quando existe uma única versão em disco.
    # Prefere arquivos comprimidos: WAVs longos podem bloquear o Playwright.
    audio_dir = os.path.join(proj, "assets", "audio")
    ver = ep.get("version")
    if not ver and os.path.isdir(audio_dir):
        versions = set()
        for name in os.listdir(audio_dir):
            match = re.fullmatch(r"(?:master|narration)_(?!raw_)(.+)\.(?:m4a|mp3|aac|wav)", name)
            if match:
                versions.add(match.group(1))
        if len(versions) > 1:
            raise ValueError("episode.json sem versão e várias narrações presentes: "
                             + ", ".join(sorted(versions)) + ". Regenere o spec com --version.")
        ver = next(iter(versions), None)
    candidates = []
    if ver:
        candidates = [f"{kind}_{ver}.{ext}" for ext in ("m4a", "mp3", "aac", "wav")
                      for kind in ("master", "narration")]
    else:
        candidates = [f"{kind}.{ext}" for ext in ("m4a", "mp3", "aac", "wav")
                      for kind in ("master", "narration")]
    audio = None
    for cand in candidates:
        src = os.path.join(audio_dir, cand)
        if os.path.exists(src):
            os.makedirs(os.path.join(dest, "assets", "audio"), exist_ok=True)
            shutil.copy2(src, os.path.join(dest, "assets", "audio", os.path.basename(src)))
            audio = f"assets/audio/{os.path.basename(src)}"
            break

    # efeitos sonoros: copia só os usados da biblioteca local (assets/sfx)
    sfx_manifest = None
    sfx_manifest_path = os.path.join(proj, "assets", "sfx", "manifest.json")
    if os.path.exists(sfx_manifest_path):
        with open(sfx_manifest_path, encoding="utf-8") as source:
            catalog = json.load(source)
        sfx_manifest = {}
        names = {str(e.get("nome", "")) for e in ep["elements"] if e.get("tipo") == "sfx"}
        sfx_dest = os.path.join(dest, "assets", "sfx")
        for name in names:
            meta = catalog.get(name)
            if not meta:
                continue
            src = os.path.join(proj, "assets", "sfx", meta["file"])
            if os.path.exists(src):
                os.makedirs(sfx_dest, exist_ok=True)
                shutil.copy2(src, os.path.join(sfx_dest, meta["file"]))
                sfx_manifest[name] = meta

    # Dependências fixadas primeiro: o HTML aponta para assets/vendor/, então
    # uma cópia que falhe tem de abortar antes de escrever a composição.
    if vendor.available():
        vendor.install(dest, "gsap.min.js")
        if vendor.tem_fontes():
            vendor.install_fontes(dest)

    html = build_html(ep, theme, audio=audio, sfx_manifest=sfx_manifest,
                      fontes_css=fontes_css)
    with open(os.path.join(dest, "index.html"), "w", encoding="utf-8") as output:
        output.write(html)
    # sidecar de motion: intenção que o `check` verifica de verdade (não pode ser vazio)
    with open(os.path.join(dest, "index.motion.json"), "w", encoding="utf-8") as output:
        json.dump({"duration": ep["total"],
                   "assertions": [
                       {"kind": "staysInFrame", "selector": "#root"},
                       {"kind": "keepsMoving", "withinSelector": "#root",
                        "maxStaticSec": motion_static_limit(ep["total"])},
                   ]}, output, indent=2)
    if not os.path.exists(os.path.join(dest, "hyperframes.json")):
        with open(os.path.join(dest, "hyperframes.json"), "w", encoding="utf-8") as output:
            json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                       "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                       "paths": {"blocks": "compositions", "components": "compositions/components",
                                 "assets": "assets"},
                       "media": {"autoProxy": True}}, output, indent=2)
    print(f"ok | tema={theme} | {len(ep['elements'])} elementos | ilustrações: {len(set(used))} "
          f"| {dest}")
    from workflow import record_build
    record_build(proj, Path(dest), a.spec, theme, a.seconds, audio)


if __name__ == "__main__":
    main()
