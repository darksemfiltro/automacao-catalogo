# -*- coding: utf-8 -*-
"""
measure_durations.py — lê os .wav gerados pelo OmniVoice e escreve tts_result_<v>.json.

Robusto: mede os arquivos em disco (não depende do stdout do batch).

Uso:
  python pipeline/measure_durations.py <proj> <version> [out.json] [roteiro_fonetico.json]
"""
from __future__ import annotations

import json
import os
import sys

import soundfile as sf


def main(proj, version="v1", out=None, phonetic=None):
    d = os.path.join(proj, "assets", "audio", version)
    fon = json.load(open(phonetic or os.path.join(proj, f"roteiro_fonetico_{version}.json"),
                         encoding="utf-8"))
    order = [s["id"] for s in fon["segments"]]
    segs, sr = [], 24000
    for sid in order:
        p = os.path.join(d, sid + ".wav")
        if not os.path.exists(p):
            segs.append({"id": sid, "output": None, "error": "missing"})
            continue
        info = sf.info(p)
        sr = info.samplerate
        segs.append({"id": sid, "output": os.path.abspath(p),
                     "duration_s": round(info.frames / info.samplerate, 3)})
    total = round(sum(s.get("duration_s", 0) for s in segs), 3)
    missing = [s["id"] for s in segs if not s.get("output")]
    payload = {"ok": not missing, "provider": "omnivoice", "model": "k2-fsa/OmniVoice",
               "sampling_rate": sr, "segments": segs, "total_duration_s": total}
    dest = out or os.path.join(proj, f"tts_result_{version}.json")
    json.dump(payload, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"segmentos: {len(segs)} | fala: {total:.1f}s (~{total/60:.1f} min) -> {dest}")
    if missing:
        print(f">>> FALTANDO ({len(missing)}): {', '.join(missing[:20])}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "v1",
         sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None,
         sys.argv[4] if len(sys.argv) > 4 else None)
