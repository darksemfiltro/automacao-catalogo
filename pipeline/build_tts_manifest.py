# -*- coding: utf-8 -*-
"""Gera um manifesto OmniVoice a partir do roteiro fonético.

Uma semente fixa por segmento (BASE + n*1000) permite refazer uma frase sem
alterar as outras. O roteiro pode marcar a tentativa com @2 no ID.

Exemplo:
  python pipeline/build_tts_manifest.py . roteiro_fonetico_v1.json v1 \
      --ref-audio minha_voz.wav --ref-text-file minha_voz.txt

Também é possível definir CATALOGO_REF_AUDIO e omitir --ref-audio. Sem
--ref-text ou --ref-text-file, usa-se um .txt ao lado do áudio de referência.

Provedores que não clonam voz (API compatível com OpenAI, comando local como
o Piper) não precisam de referência: use --sem-referencia.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

BASE_SEED = 90000


def _selected_ids(only: str | list[str] | set[str] | None) -> set[str]:
    if only is None:
        return set()
    values = [only] if isinstance(only, str) else only
    return {item.strip() for value in values for item in value.split(",") if item.strip()}


def main(proj, fonetico, version="v1", only=None, speed=1.0, ref_audio=None,
         ref_text=None, output_name=None, ref_text_file=None, sem_referencia=False):
    if speed <= 0:
        raise ValueError("--speed deve ser maior que zero")
    if sem_referencia and (ref_audio or ref_text or ref_text_file):
        raise ValueError("--sem-referencia não combina com --ref-audio, --ref-text ou --ref-text-file")

    project = Path(proj).expanduser().resolve()
    phonetic_path = Path(fonetico).expanduser()
    if not phonetic_path.is_absolute() and not phonetic_path.is_file():
        phonetic_path = project / phonetic_path
    if not phonetic_path.is_file():
        raise FileNotFoundError(f"Roteiro fonético não encontrado: {phonetic_path}")

    audio_path = None
    if not sem_referencia:
        audio_arg = ref_audio or os.environ.get("CATALOGO_REF_AUDIO")
        if not audio_arg:
            raise ValueError("Informe --ref-audio ou defina CATALOGO_REF_AUDIO com o áudio de referência")
        audio_path = Path(audio_arg).expanduser().resolve()
        if not audio_path.is_file():
            raise FileNotFoundError(f"Áudio de referência não encontrado: {audio_path}")

        if ref_text is not None and ref_text_file is not None:
            raise ValueError("Use --ref-text ou --ref-text-file, não ambos")
        if ref_text is None:
            text_path = Path(ref_text_file).expanduser() if ref_text_file else audio_path.with_suffix(".txt")
            if not text_path.is_file():
                raise FileNotFoundError(
                    f"Transcrição de referência não encontrada: {text_path}. "
                    "Informe --ref-text, --ref-text-file ou crie um .txt ao lado do áudio"
                )
            ref_text = text_path.read_text(encoding="utf-8")
        ref_text = ref_text.strip()
        if not ref_text:
            raise ValueError("A transcrição de referência não pode estar vazia")

    fon = json.loads(phonetic_path.read_text(encoding="utf-8"))
    selected = _selected_ids(only)
    found: set[str] = set()
    audio_dir = project / "assets" / "audio" / version
    out = {"language": "Portuguese", "output_dir": str(audio_dir), "segments": []}
    if audio_path is not None:
        out = {"ref_audio": str(audio_path), "ref_text": ref_text, **out}
    for i, s in enumerate(fon["segments"]):
        raw_id = s["id"]
        base_id, _, attempt_text = raw_id.partition("@")
        if selected and raw_id not in selected and base_id not in selected:
            continue
        if raw_id in selected:
            found.add(raw_id)
        if base_id in selected:
            found.add(base_id)
        if not base_id or base_id in (".", "..") or "/" in base_id or "\\" in base_id:
            raise ValueError(f"ID de segmento inválido para nome de arquivo: {raw_id}")
        attempt_value = s.get("attempt", attempt_text or 1)
        try:
            attempt = int(attempt_value)
        except (TypeError, ValueError):
            raise ValueError(f"Tentativa inválida no segmento {raw_id}: {attempt_value}") from None
        if attempt < 1:
            raise ValueError(f"Tentativa inválida no segmento {raw_id}: {attempt}")
        out["segments"].append({
            "id": base_id,
            "text": s["text"],
            "output": str(audio_dir / f"{base_id}.wav"),
            "language": "Portuguese",
            "speed": speed,
            "seed": BASE_SEED + i * 1000 + (attempt - 1),
            "gap_after": 0.0,
        })
    missing = selected - found
    if missing:
        raise ValueError(f"Segmento(s) não encontrado(s): {', '.join(sorted(missing))}")

    dest = Path(output_name) if output_name else project / f"tts_manifest_{version}.json"
    audio_dir.mkdir(parents=True, exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    voice = audio_path.name if audio_path is not None else "sem referência"
    print(f"manifest: {len(out['segments'])} segmentos | voz: {voice} -> {dest}")
    return dest


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="pasta de produção do episódio")
    parser.add_argument("phonetic", help="JSON do roteiro fonético, relativo ao cwd ou ao projeto")
    parser.add_argument("version", nargs="?", default="v1", help="versão dos arquivos (padrão: v1)")
    parser.add_argument("legacy_only", nargs="?", help="IDs separados por vírgula (compatibilidade)")
    parser.add_argument("--only", help="gera apenas os IDs informados, separados por vírgula")
    parser.add_argument("--ref-audio", help="arquivo de voz de referência; pode usar CATALOGO_REF_AUDIO")
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument("--ref-text", help="transcrição da voz de referência")
    text_group.add_argument("--ref-text-file", help="arquivo UTF-8 com a transcrição da voz")
    parser.add_argument("--sem-referencia", action="store_true",
                        help="não exige voz de referência (API ou comando local)")
    parser.add_argument("--speed", type=float, default=1.0, help="velocidade da narração (padrão: 1.0)")
    args = parser.parse_args(argv)
    if args.only and args.legacy_only:
        parser.error("Use --only ou o quarto argumento posicional, não ambos")
    try:
        main(args.project, args.phonetic, args.version, args.only or args.legacy_only,
             args.speed, args.ref_audio, args.ref_text, ref_text_file=args.ref_text_file,
             sem_referencia=args.sem_referencia)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    cli()
