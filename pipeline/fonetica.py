# -*- coding: utf-8 -*-
"""
fonetica.py — normaliza o roteiro para TTS (pt-BR) antes de gerar o áudio.

O OmniVoice lê o que está escrito, não o que você quis dizer. Este script transforma
o roteiro legível em TEXTO FALÁVEL: números por extenso, siglas na forma falada,
símbolos e unidades expandidos, estrangeirismos aportuguesados.

Uso:
  python pipeline/fonetica.py --in segments.json --out roteiro_fonetico.json
  python pipeline/fonetica.py --in segments.json --check      # só aponta pendências
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

UNITS = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez",
         "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
TENS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
HUND = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
        "seiscentos", "setecentos", "oitocentos", "novecentos"]
SCALE = [(10**12, "trilhão", "trilhões"), (10**9, "bilhão", "bilhões"), (10**6, "milhão", "milhões"),
         (1000, "mil", "mil")]
NUMERIC_TOKEN = r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?"


def _three(n: int) -> str:
    if n == 0:
        return ""
    if n == 100:
        return "cem"
    h, r = divmod(n, 100)
    out = []
    if h:
        out.append(HUND[h])
    if r:
        if r < 20:
            out.append(UNITS[r])
        else:
            t, u = divmod(r, 10)
            out.append(TENS[t] + (" e " + UNITS[u] if u else ""))
    return " e ".join(out)


def num2words_pt(n: int) -> str:
    if n == 0:
        return "zero"
    out = []
    for v, sing, plur in SCALE:
        q, n = divmod(n, v)
        if q:
            if v == 1000:
                label = "mil" if q == 1 else f"{_three(q)} mil"
            else:
                label = f"{_three(q)} {sing if q == 1 else plur}"
            out.append((label, v * q))
    if n:
        out.append((_three(n), n))
    if len(out) == 1:
        return out[0][0]
    res = out[0][0]
    for i in range(1, len(out)):
        label, val = out[i]
        res += (" e " if (val < 100 or val % 100 == 0) else " ") + label
    return res


# Siglas soletradas ou lidas como palavra (ajuste depois de ouvir o TTS).
SIGLAS = {
    "IBGE": "i bê gê é", "MMA": "eme eme á", "ONU": "o ene u", "NASA": "nássa",
    "ESA": "éssa", "JPL": "jota pê éle", "HST": "agá ésse tê", "JWST": "jota duplo u",
    "SGR": "ésse gê érre", "UV": "u vê", "IA": "i á", "ADN": "a dê ene",
}
# Estrangeirismos / nomes próprios: escreva como se pronuncia em português.
ESTRANGEIROS = {
    "YouTube": "iutúbi", "Google": "gúgol", "online": "onlaine", "site": "saite",
    "Wolf-Rayet": "Volf Raiet", "Wolf Rayet": "Volf Raiet", "Betelgeuse": "Beteljeuse",
    "UY Scuti": "u ipsilon Escúti", "Jocelyn Bell Burnell": "Jósselin Bel Burnel",
    "LGM-1": "éle gê eme um", "K-type": "tipo cá", "G-type": "tipo gê",
    "Kelvin": "Kélvin", "kelvin": "kélvin",
}

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _roman_number(value: str) -> int:
    total, previous = 0, 0
    for char in reversed(value.upper()):
        current = ROMAN[char]
        total += -current if current < previous else current
        previous = current
    return total


def _seculo(m: re.Match) -> str:
    return "século " + num2words_pt(_roman_number(m.group(1)))


def _dec(m: re.Match) -> str:
    """1,5 -> um vírgula cinco."""
    inteiro, frac = m.group(1), m.group(2)
    return num2words_pt(int(inteiro)) + " vírgula " + " ".join(UNITS[int(d)] for d in frac)


def _escala(m: re.Match) -> str:
    inteiro, frac, palavra = int(m.group(1)), m.group(2), m.group(3)
    if frac:
        scale = {"milhão": 10**6, "milhões": 10**6, "bilhão": 10**9,
                 "bilhões": 10**9, "mil": 10**3, "trilhão": 10**12, "trilhões": 10**12}[palavra]
        total = (inteiro * 10 ** len(frac) + int(frac)) * scale // 10 ** len(frac)
        return num2words_pt(total)
    return num2words_pt(inteiro) + (" " + palavra)


def _inteiro(m: re.Match) -> str:
    return num2words_pt(int(m.group(0)))


def _moeda(m: re.Match) -> str:
    n = m.group(1).replace(".", "")
    val = int(n)
    cents = m.group(2)
    s = num2words_pt(val) + (" reais" if val != 1 else " real")
    if cents and int(cents):
        s += " e " + num2words_pt(int(cents)) + " centavos"
    return s


def _num(v: str) -> str:
    if v.startswith("-"):
        return "menos " + _num(v[1:])
    v = v.replace(".", "")
    return _dec(re.fullmatch(r"(\d+),(\d+)", v)) if "," in v else num2words_pt(int(v))


def _unidade(m: re.Match, nome: str, plural_extra: str | None) -> str:
    v = m.group(1)
    base = _num(v)
    plural = "s" if ("," in v or int(v.replace(".", "")) > 1) else ""
    tail = (" " + plural_extra + plural) if plural_extra else ""
    return f"{base} {nome}{plural}{tail}"


def _toneladas(m: re.Match) -> str:
    v = m.group(1)
    n = int(v.replace(".", "")) if "," not in v else None
    if n == 1:
        return "uma tonelada"
    spoken = _num(v)
    spoken = re.sub(r"\bum$", "uma", spoken)
    spoken = re.sub(r"\bdois$", "duas", spoken)
    return spoken + " toneladas"


def normaliza(texto: str) -> str:
    t = texto
    for k, v in SIGLAS.items():
        t = re.sub(rf"\b{re.escape(k)}\b", v, t)
    for k, v in ESTRANGEIROS.items():
        t = re.sub(rf"(?<![\w-]){re.escape(k)}(?![\w-])", v, t)
    # classe espectral: "tipo K", "tipo G" -> "tipo cá", "tipo gê"
    _letters = {"O": "ó", "B": "bê", "A": "á", "F": "éfe", "G": "gê", "K": "cá", "M": "eme"}
    t = re.sub(r"\btipo\s+([OBAFGKM])\b", lambda m: "tipo " + _letters[m.group(1)], t)
    # séculos em algarismos romanos travam o TTS — escreva a leitura
    t = re.sub(r"\bséc\.\s*([IVXLCDM]+)\b", _seculo, t, flags=re.IGNORECASE)
    # temperatura: 2500 K / 3.500 K
    t = re.sub(r"(\d[\d.]*)\s*K\b", lambda m: num2words_pt(int(m.group(1).replace(".", ""))) + " Kélvin", t)
    # velocidade: km/s, m/s
    t = re.sub(rf"({NUMERIC_TOKEN})\s*km/s\b", lambda m: _num(m.group(1)) + " quilômetros por segundo", t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*m/s\b", lambda m: _num(m.group(1)) + " metros por segundo", t)
    # vezes: 1700x, 10x
    t = re.sub(r"\b(\d[\d.]*)\s*[xX]\b", lambda m: num2words_pt(int(m.group(1).replace(".", ""))) +
               (" vez" if m.group(1).replace(".", "") == "1" else " vezes"), t)
    # moeda
    t = re.sub(r"R\$\s*([\d.]+)(?:,(\d+))?", _moeda, t)
    # escala com decimal: 1,5 milhão
    t = re.sub(r"(\d+),(\d+)\s*(milhão|milhões|bilhão|bilhões|trilhão|trilhões|mil)\b", _escala, t)
    # percentual
    t = re.sub(rf"({NUMERIC_TOKEN})\s*%", lambda m: _num(m.group(1)) + " por cento", t)
    # unidades
    t = re.sub(rf"({NUMERIC_TOKEN})\s*km²", lambda m: _unidade(m, "quilômetro", "quadrado"), t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*m²", lambda m: _unidade(m, "metro", "quadrado"), t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*km\b", lambda m: _unidade(m, "quilômetro", None), t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*kg\b", lambda m: _unidade(m, "quilograma", None), t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*toneladas?\b", _toneladas, t)
    t = re.sub(rf"({NUMERIC_TOKEN})\s*massas? solares?\b", lambda m: _num(m.group(1)) +
               (" massa solar" if _num(m.group(1)) == "um" else " massas solares"), t)
    t = re.sub(rf"(-?{NUMERIC_TOKEN})\s*°C\b", lambda m: _num(m.group(1)) + " graus", t)
    # unidades após quantidades já escritas por extenso (ex.: 3,5 milhões de km²)
    t = re.sub(r"\bkm²(?!\w)", "quilômetros quadrados", t)
    t = re.sub(r"\bkg\b", "quilogramas", t)
    # separador de milhar: 1.234 -> mil duzentos e trinta e quatro
    t = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b", lambda m: num2words_pt(int(m.group(0).replace(".", ""))), t)
    # decimais soltos
    t = re.sub(r"(\d+),(\d+)", _dec, t)
    # inteiros soltos
    t = re.sub(r"\b\d+\b", _inteiro, t)
    # símbolos
    for a, b in {"&": " e ", "+": " mais ", "=": " igual a ", "@": " arroba ",
                 "°": " graus ", "≤": " menor ou igual a ", "≥": " maior ou igual a "}.items():
        t = t.replace(a, b)
    return re.sub(r"\s{2,}", " ", t).strip()


PEND = re.compile(r"[%$@&+=°]|\b\d[\d.,]*\b|R\$|\bkm²(?!\w)|\bkm\b|\bm²(?!\w)|\bkg\b|\bK\b|\bx\b")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.inp, encoding="utf-8"))
    segs = data["segments"] if isinstance(data, dict) else data
    out, pend = [], []
    for s in segs:
        orig = s["text"]
        fon = normaliza(orig)
        item = {"id": s["id"], "text_original": orig, "text": fon}
        item.update({k: v for k, v in s.items() if k not in ("id", "text")})
        out.append(item)
        for m in PEND.finditer(fon):
            pend.append(f"{s['id']}: '{m.group(0)}' -> {fon[max(0, m.start()-20):m.end()+20]!r}")
    if a.check:
        print(f"segmentos: {len(segs)} | pendências: {len(pend)}")
        for p in pend[:40]:
            print("  -", p)
        sys.exit(1 if pend else 0)
    payload = {"segments": out}
    if isinstance(data, dict):
        for k, v in data.items():
            if k != "segments":
                payload[k] = v
    dest = a.out or "roteiro_fonetico.json"
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    json.dump(payload, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"ok | segmentos: {len(out)} | pendências restantes: {len(pend)} -> {dest}")
    for p in pend[:20]:
        print("  -", p)


if __name__ == "__main__":
    main()
