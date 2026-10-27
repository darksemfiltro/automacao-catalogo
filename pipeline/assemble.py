"""
assemble.py — monta a narração, o bed (opcional) e um master auditável do episódio.

Fluxo:
  1. cada segmento cru do OmniVoice passa por loudnorm two-pass (alvo em CONSTRAINTS.md);
  2. concatena com a pausa `block_gap_before` de cada segmento (lead 0.25 s / tail 0.14 s);
  3. mixa um bed musical no alvo de CONSTRAINTS.md quando existir `assets/music/bed.*`;
  4. mede o master com ebur128 real e escreve `audio_report_<v>.json`.

Os alvos de loudness vivem em `sistema/CONSTRAINTS.md` (`audio.*`), não aqui.

`timing_<v>.json` é a fonte de verdade do tempo: cada segmento com start/duração, usado
pelo alinhamento (align_mms) e pela composição (gen_comp).

Uso:
  python pipeline/assemble.py --project . --version v1
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from constraints import value as limite

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
TARGET_I = limite("audio.lufs_integrado", -16.0)
TARGET_TP = limite("audio.true_peak_dbtp", -1.5)
TARGET_LRA = limite("audio.lra_lu", 11.0)
BED_LUFS = limite("audio.bed_lufs", -30.0)
LEAD = 0.25
TAIL = 0.14
END_SILENCE = 1.6


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def loudnorm_measure(path: Path) -> dict:
    result = run([FFMPEG, "-hide_banner", "-i", str(path), "-af",
                  f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
                  "-f", "null", "-"])
    out = result.stderr
    start, end = out.rfind("{"), out.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError(f"Não foi possível medir loudness: {path}")
    return json.loads(out[start:end + 1])


def ebur128_measure(path: Path) -> dict:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
         "-f", "null", "-"], check=True, capture_output=True, text=True)
    out = result.stderr
    i = re.search(r"\n\s*I:\s*(-?\d+(?:\.\d+)?) LUFS", out)
    lra = re.search(r"\n\s*LRA:\s*(-?\d+(?:\.\d+)?) LU", out)
    tp = re.search(r"\n\s*Peak:\s*(-?\d+(?:\.\d+)?) dBFS", out)
    if not (i and lra and tp):
        raise RuntimeError(f"Não foi possível extrair ebur128: {path}")
    return {"integrated_lufs": float(i.group(1)), "lra_lu": float(lra.group(1)),
            "true_peak_dbTP": float(tp.group(1))}


def loudnorm_apply(source: Path, destination: Path, measurement: dict) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
          "measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}:linear=false:print_format=summary"
          ).format(**measurement)
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
         "-af", af, "-ar", "48000", "-ac", "2", str(destination)])


def find_bed(project: Path) -> Path | None:
    for pattern in ("assets/music/bed.*", "assets/music/bed_*.*"):
        matches = [m for m in glob.glob(str(project / pattern))
                   if Path(m).suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".flac")]
        if matches:
            return Path(sorted(matches)[0])
    return None


def build_voice(project: Path, version: str, meta: dict, result: dict):
    source_dir = project / "assets" / "audio" / version
    norm_dir = project / "assets" / "audio" / f"norm_{version}"
    norm_dir.mkdir(parents=True, exist_ok=True)
    result_by_id = {s["id"]: s for s in result["segments"]}
    timing, segment_report = [], []
    sample_rate = 48000
    parts = [np.zeros((int(sample_rate * LEAD), 2), dtype=np.float32)]
    cursor = LEAD

    for segment in meta["segments"]:
        sid = segment["id"]
        source = source_dir / f"{sid}.wav"
        if not source.exists():
            raise FileNotFoundError(f"Áudio ausente para {sid}: {source}")
        destination = norm_dir / f"{sid}.wav"
        measured = loudnorm_measure(source)
        loudnorm_apply(source, destination, measured)
        data, sr = sf.read(destination, dtype="float32", always_2d=True)
        if sr != sample_rate:
            raise RuntimeError(f"Sample rate inesperado em {destination}: {sr}")
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        gap = float(segment.get("block_gap_before", 0.18))
        parts.append(np.zeros((int(sample_rate * gap), 2), dtype=np.float32))
        cursor += gap
        parts.append(data)
        parts.append(np.zeros((int(sample_rate * TAIL), 2), dtype=np.float32))
        speech = float(result_by_id.get(sid, {}).get("duration_s", len(data) / sample_rate))
        timing.append({"id": sid, "chapter": segment.get("chapter"),
                       "start": round(cursor, 3), "speech_dur": round(speech, 3),
                       "dur": round(len(data) / sample_rate + TAIL + gap, 3),
                       "text": segment["text"]})
        cursor += len(data) / sample_rate + TAIL
        segment_report.append({"id": sid, "loudnorm": measured,
                               "ebur128": ebur128_measure(destination)})

    parts.append(np.zeros((int(sample_rate * END_SILENCE), 2), dtype=np.float32))
    raw = np.concatenate(parts, axis=0)
    raw_path = project / "assets" / "audio" / f"narration_raw_{version}.wav"
    sf.write(raw_path, raw, sample_rate, subtype="PCM_24")
    narration = project / "assets" / "audio" / f"narration_{version}.wav"
    loudnorm_apply(raw_path, narration, loudnorm_measure(raw_path))
    return timing, segment_report, narration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--version", default="v1")
    ap.add_argument("--segments", default=None)
    ap.add_argument("--tts-result", default=None)
    args = ap.parse_args()
    project, version = Path(args.project), args.version

    meta = json.loads(Path(args.segments or project / f"segments_{version}.json").read_text(encoding="utf-8"))
    result = json.loads(Path(args.tts_result or project / f"tts_result_{version}.json").read_text(encoding="utf-8"))

    timing, segment_report, narration = build_voice(project, version, meta, result)
    # The narration file is the timeline's source of truth. `dur` includes the
    # gap before a segment, while `start` is already after that gap.
    total = round(sf.info(narration).duration, 3)
    (project / f"timing_{version}.json").write_text(
        json.dumps({"total": total, "segments": timing}, ensure_ascii=False, indent=2), encoding="utf-8")

    bed_source = find_bed(project)
    bed = bed_measurement = None
    if bed_source:
        bed = project / "assets" / "music" / f"bed_norm_{version}.wav"
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-stream_loop", "-1",
             "-i", str(bed_source), "-af", f"loudnorm=I={BED_LUFS}:TP=-2:LRA=11",
             "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", str(bed)])
        bed_measurement = loudnorm_measure(bed)

    master = project / "assets" / "audio" / f"master_{version}.wav"
    raw_mix = project / "assets" / "audio" / f"mix_raw_{version}.wav"
    if bed:
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(narration), "-i", str(bed),
             "-filter_complex",
             "[1:a]volume=0.40[bed];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0",
             "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", str(raw_mix)])
        loudnorm_apply(raw_mix, master, loudnorm_measure(raw_mix))
    else:
        master = narration

    report = {
        "version": version,
        "targets": {"integrated_lufs": TARGET_I, "true_peak_dbTP": TARGET_TP,
                    "lra_lu": TARGET_LRA, "sample_rate": 48000, "channels": 2},
        "segments": segment_report,
        "narration": {"ebur128": ebur128_measure(narration)},
        "bed": {"source": str(bed_source), "ebur128": ebur128_measure(bed)} if bed else None,
        "master": {"ebur128": ebur128_measure(master)},
        "files": {"narration": str(narration), "bed": str(bed) if bed else None, "master": str(master)},
    }
    (project / f"audio_report_{version}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok | total: {total:.2f}s ({total/60:.2f} min) | master: {master}")


if __name__ == "__main__":
    main()
