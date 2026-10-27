"""Transcrição local por palavra; não confundir ASR com alinhamento forçado."""
import argparse
import json
from pathlib import Path


def transcribe(model, source, language):
    segments, info = model.transcribe(str(source), language=language,
                                      word_timestamps=True, vad_filter=True)
    words = []
    for segment in segments:
        for word in segment.words or []:
            words.append({"w": word.word.strip(), "t": round(word.start, 3),
                          "t_end": round(word.end, 3),
                          "probability": round(word.probability, 4)})
    if not words:
        raise ValueError("Nenhuma palavra detectada; confira o áudio e o idioma")
    return {"schema_version": 1, "engine": "faster-whisper",
            "language": info.language, "duration": info.duration, "words": words}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--model", default="small", help="nome ou pasta local do modelo")
    p.add_argument("--language", default="pt")
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--offline", action="store_true")
    a = p.parse_args()
    if not a.source.is_file() or a.source.resolve() == a.out.resolve():
        p.error("Fonte ausente ou saída igual à fonte")
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device=a.device,
                         compute_type="int8" if a.device == "cpu" else "float16",
                         local_files_only=a.offline)
    result = transcribe(model, a.source, a.language)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
