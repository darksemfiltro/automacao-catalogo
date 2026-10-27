# -*- coding: utf-8 -*-
"""
tempo.py — utilitários de tempo compartilhados pela pipeline.

O ponto crítico é o mapeamento entre as palavras do ROTEIRO (editorial) e as palavras
FALADAS (fonéticas). Quando o `fonetica.py` expande "2500" para "dois mil e quinhentos",
a palavra editorial passa a ocupar VÁRIOS tokens falados. Sem esse mapa, a ancoragem
dos callouts (que usa `editorial_words`) colapsa e o texto entra segundos fora de sincronia.

Uso (ambos os scripts):
    from tempo import plain, norm_words, editorial_spans, recompute_editorial
"""
from __future__ import annotations

import re
import unicodedata


def plain(word: str) -> str:
    """Forma comparável de uma palavra: minúscula, sem acento e sem pontuação."""
    w = unicodedata.normalize("NFD", str(word).lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def norm_words(text: str):
    """Tokeniza em palavras (ignora espaços e tokens sem letra/número)."""
    return [w for w in re.findall(r"\S+", text) if re.search(r"\w", w)]


def editorial_spans(original_words, spoken_words, spoken_spans):
    """
    Casa cada palavra do roteiro (`original_words`) com o bloco de palavras faladas que
    a representa, devolvendo `(original, t0, t1, valid)`.

    Estratégia (gulosa, robusta a expansões):
      - se a palavra falada na posição atual bate direto com a editorial -> 1:1;
      - senão a editorial é uma expansão (número/sigla): consome tokens falados ATÉ
        casar a próxima palavra editorial. Isso mantém o cursor correto e evita o
        colapso de tempo que acontecia antes.
    """
    n, m = len(original_words), len(spoken_spans)
    spoken_plain = [plain(w) for w in spoken_words]
    result, cursor = [], 0

    for i, original in enumerate(original_words):
        op = plain(original)
        if cursor < m and spoken_plain[cursor] == op:
            _, t0, t1 = spoken_spans[cursor]
            result.append((original, t0, t1, t0 is not None))
            cursor += 1
            continue

        # expansão: procura a próxima palavra editorial dentro do falado restante
        end = cursor + 1
        for k in range(i + 1, min(n, i + 5)):
            nxt = plain(original_words[k])
            if not nxt:
                continue
            found = None
            for j in range(cursor, m):
                if spoken_plain[j] == nxt:
                    found = j
                    break
            if found is not None:
                end = found
                break

        if end <= cursor:
            end = cursor + 1
        group = spoken_spans[cursor:end]
        cursor = end
        starts = [g[1] for g in group if g[1] is not None]
        ends = [g[2] for g in group if g[2] is not None]
        valid = bool(group) and len(starts) == len(group)
        result.append((original, min(starts) if starts else None,
                       max(ends) if ends else None, valid))
    return result


def recompute_editorial(seg, original_text):
    """
    Reconstrói `editorial_words` a partir de um segmento de `alignment_*.json` que já
    tem `words` (falado, com tempos). Usa o texto original do roteiro.

    `seg["words"]` = lista de {"w", "t", "t_end", ...}. Devolve lista no mesmo formato
    do align_mms, pronta para o `build_cenas`.
    """
    spoken = seg.get("words") or []
    spoken_words = [w["w"] for w in spoken]
    spoken_spans = [(w["w"], w.get("t"), w.get("t_end")) for w in spoken]
    original = norm_words(original_text or "")
    if not spoken or not original:
        return list(seg.get("editorial_words") or [])
    out = []
    prev = seg.get("start", 0.0)
    for wd, t0, t1, aligned in editorial_spans(original, spoken_words, spoken_spans):
        if t0 is None or t1 is None:
            out.append({"w": wd, "t": round(prev, 3), "t_end": round(prev, 3),
                        "aligned": False})
        else:
            out.append({"w": wd, "t": round(t0, 3), "t_end": round(t1, 3),
                        "aligned": aligned})
            prev = t0
    return out
