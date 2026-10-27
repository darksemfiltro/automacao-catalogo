"""Extrai quadros e pausas para revisão; nunca corta nem modifica a fonte."""
import argparse
import html
import json
import math
import re
import subprocess
from pathlib import Path


def silence_ranges(log, duration):
    ranges, start = [], None
    for kind, value in re.findall(r"silence_(start|end):\s*([0-9.]+)", log):
        if kind == "start":
            start = float(value)
        elif start is not None:
            ranges.append({"start": start, "end": min(float(value), duration),
                           "action": "review_only"})
            start = None
    if start is not None:
        ranges.append({"start": start, "end": duration, "action": "review_only"})
    return ranges


def analyze(source, out, interval=5.0):
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("Intervalo deve ser positivo e finito")
    source, out = Path(source).resolve(), Path(out).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", str(source)], check=True, capture_output=True, text=True)
    meta = json.loads(probe.stdout)
    video = next(s for s in meta["streams"] if s["codec_type"] == "video")
    duration = float(meta["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Fonte sem duração finita e positiva")
    if math.ceil(duration / interval) > 1000:
        raise ValueError("Mais de 1000 quadros; aumente --interval ou analise um trecho")
    out.mkdir(parents=True, exist_ok=False)
    frames = []
    for i in range(math.ceil(duration / interval)):
        t = i * interval
        filename = f"frame-{i:05d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(source),
                        "-frames:v", "1", "-vf", "scale=960:-2", str(out / filename)], check=True)
        if not (out / filename).is_file():
            raise RuntimeError(f"Quadro ausente em {t}s")
        frames.append({"time": t, "file": filename, "fit": "contain",
                       "crop_allowed": False, "presenter_bounds": None})
    pauses = []
    if any(s["codec_type"] == "audio" for s in meta["streams"]):
        result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(source),
                                 "-af", "silencedetect=noise=-35dB:d=0.6", "-vn",
                                 "-f", "null", "-"], check=True, capture_output=True, text=True)
        pauses = silence_ranges(result.stderr, duration)
    report = {"schema_version": 1, "source_name": source.name, "duration": duration,
              "width": video["width"], "height": video["height"],
              "policy": "contain-no-overlays-on-video", "frames": frames,
              "silence_candidates": pauses,
              "warning": "Amostragem não rastreia rostos; não autoriza crop nem cortes automáticos."}
    (out / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = "".join(f'<figure><img src="{f["file"]}"><figcaption>{f["time"]:.2f}s</figcaption></figure>' for f in frames)
    (out / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Quadros</title>'
        '<style>body{background:#18202c;color:white;font:18px sans-serif}main{display:grid;grid-template-columns:repeat(3,1fr)}img{width:100%}figure{margin:10px}</style>'
        f'<h1>{html.escape(source.name)}</h1><p>Quadro integral. Recorte não autorizado.</p><main>{cards}</main>', encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("--out", required=True)
    p.add_argument("--interval", type=float, default=5)
    a = p.parse_args()
    analyze(a.source, a.out, a.interval)
