# -*- coding: utf-8 -*-
"""
align_mms.py — alinhamento FORÇADO (word-level) com MMS_FA do torchaudio.

Usa o texto conhecido (roteiro) para forçar o alinhamento — preciso, sem o colapso do
whisper em listas rápidas. Requer torch, torchaudio, soundfile e uroman.

Saída (alignment_<v>.json): por segmento, `words` (tokens falados) e `editorial_words`
(casando o texto do roteiro com as expansões fonéticas, ex.: "NASA" -> "nássa").

Uso:
  python pipeline/align_mms.py --project . \
      --timing timing_v1.json --phonetic roteiro_fonetico_v1.json \
      --audio-dir assets/audio/norm_v1 --out alignment_v1.json
"""
from __future__ import annotations

import argparse
import json
import os
import re

import soundfile as sf
import torch
import torchaudio
import uroman as ur

from tempo import editorial_spans, norm_words, plain  # noqa: F401  (reexport p/ compat)

U = ur.Uroman()


def romanize(text: str) -> str:
    return U.romanize_string(text, lcode="por")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--timing", default=None)
    ap.add_argument("--audio-dir", default=None)
    ap.add_argument("--phonetic", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--segment", default=None, help="alinhar só um id (debug)")
    ap.add_argument("--device", default=None,
                    help="'cuda' ou 'cpu'; autodetecta se omitido. Use 'cpu' quando o "
                         "build do torchaudio não expõe forced_align em CUDA.")
    a = ap.parse_args()
    proj = a.project
    timing = json.load(open(a.timing or os.path.join(proj, "timing_v1.json"), encoding="utf-8"))
    phonetic_path = a.phonetic
    if phonetic_path is None:
        for cand in ("roteiro_fonetico_v1.json", "roteiro_fonetico_v2.json"):
            if os.path.exists(os.path.join(proj, cand)):
                phonetic_path = os.path.join(proj, cand)
                break
    phonetic = json.load(open(phonetic_path, encoding="utf-8"))
    phonetic_by_id = {s["id"]: s for s in phonetic["segments"]}
    audio_dir = a.audio_dir or os.path.join(proj, "assets", "audio", "norm_v1")
    out = a.out or os.path.join(proj, "alignment_v1.json")
    if not os.path.isdir(audio_dir):
        audio_dir = os.path.join(proj, "assets", "audio", "v1")

    dev = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", dev, "| carregando MMS_FA ...")
    bundle = torchaudio.pipelines.MMS_FA
    sr = bundle.sample_rate
    model = bundle.get_model().to(dev)
    tokenizer = bundle.get_tokenizer()

    def word_spans(wav_path, words):
        wav, csr = sf.read(wav_path, dtype="float32")
        if wav.ndim == 2:
            wav = wav.mean(axis=1)
        w = torch.from_numpy(wav)
        if csr != sr:
            w = torchaudio.functional.resample(w, csr, sr)
        with torch.inference_mode():
            em, _ = model(w.unsqueeze(0).to(dev))
        roms = [re.sub(r"[^a-z]", "", romanize(wd).lower()) for wd in words]
        tok_words = []
        for r in roms:
            try:
                tok_words.append(tokenizer([r])[0] if r else [])
            except Exception:
                tok_words.append([])
        flat = [t for tw in tok_words for t in tw]
        if not flat:
            return []
        targets = torch.tensor([flat], dtype=torch.int32, device=dev)
        aligned, scores = torchaudio.functional.forced_align(em, targets, blank=0)
        spans = torchaudio.functional.merge_tokens(aligned[0], scores[0])
        spf = (w.shape[-1] / em.shape[1]) / sr
        res, k = [], 0
        for wi, tw in enumerate(tok_words):
            n = len(tw)
            seg = spans[k:k + n]
            k += n
            if not seg:
                res.append((words[wi], None, None))
                continue
            res.append((words[wi], seg[0].start * spf, seg[-1].end * spf))
        return res

    result = []
    for s in timing["segments"]:
        sid = s["id"]
        if a.segment and sid != a.segment:
            continue
        p = os.path.join(audio_dir, sid + ".wav")
        original_words = norm_words(s["text"])
        spoken_text = phonetic_by_id.get(sid, {}).get("text", s["text"])
        words = norm_words(spoken_text)
        if not os.path.exists(p):
            result.append({"id": sid, "start": s["start"], "dur": s["dur"],
                           "words": [], "aligned_ratio": 0.0})
            continue
        try:
            sp = word_spans(p, words)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sid}: {e}")
            sp = []
        wl, prev, good = [], s["start"], 0
        for wd, t0, t1 in sp:
            t = prev if t0 is None else s["start"] + t0
            good += 0 if t0 is None else 1
            t = max(s["start"], min(t, s["start"] + s["dur"]))
            wl.append({"w": wd, "t": round(t, 3), "aligned": t0 is not None})
            prev = t
        for i, wd in enumerate(wl):
            wd["t_end"] = round(wl[i + 1]["t"] if i + 1 < len(wl) else s["start"] + s["dur"], 3)
        editorial = []
        for wd, t0, t1, aligned in editorial_spans(original_words, words, sp):
            if t0 is None:
                editorial.append({"w": wd, "t": round(prev, 3), "t_end": round(prev, 3), "aligned": False})
            else:
                editorial.append({"w": wd, "t": round(s["start"] + t0, 3),
                                  "t_end": round(s["start"] + t1, 3), "aligned": aligned})
        result.append({"id": sid, "start": s["start"], "dur": s["dur"], "words": wl,
                       "editorial_words": editorial,
                       "aligned_ratio": round(good / max(1, len(words)), 2),
                       "editorial_aligned_ratio": round(
                           sum(x["aligned"] for x in editorial) / max(1, len(editorial)), 2)})
        print(f"  {sid:<8} {result[-1]['aligned_ratio']:.0%}")
    json.dump({"total": timing.get("total"), "segments": result},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ratios = [x["aligned_ratio"] for x in result if x["words"]]
    print(f"ok | segmentos: {len(result)} | alinhamento médio: "
          f"{sum(ratios)/max(1,len(ratios)):.0%} -> {out}")


if __name__ == "__main__":
    main()
