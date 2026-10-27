"""Executa o manifesto pela Central de Voz ou pelo OmniVoice direto."""
import argparse
import json
import os
import subprocess
import sys
import wave
from pathlib import Path


import voz_config

CONFIG_PATH = voz_config.CONFIG_PATH


def voice_config(path=CONFIG_PATH):
    """Configuração operacional separada dos manifestos/seeds já existentes.

    Lê sistema/voz.json e aplica sistema/voz.local.json por cima, se existir.
    """
    return voz_config.carregar(path)


def validate_ref_text(data):
    for segment in data["segments"]:
        ref = segment.get("ref_audio", data.get("ref_audio"))
        text = segment.get("ref_text", data.get("ref_text"))
        if not ref or (isinstance(text, str) and text.strip()):
            continue
        sibling = Path(ref).with_suffix(".txt")
        if not sibling.is_file() or not sibling.read_text(encoding="utf-8-sig").strip():
            raise ValueError(f"Transcrição de referência ausente: {sibling}; informe ref_text")


def validate_manifest(manifest):
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    if not segments:
        raise ValueError("Manifesto sem segmentos")
    seen, outputs = set(), set()
    for s in segments:
        if s["id"] in seen or not s.get("text", "").strip():
            raise ValueError("IDs repetidos ou texto vazio")
        seen.add(s["id"])
        output = Path(s["output"])
        if not output.is_absolute() or output.suffix.lower() != ".wav":
            raise ValueError("Saídas devem ser caminhos absolutos WAV")
        if output.resolve() in outputs:
            raise ValueError("Saída duplicada")
        outputs.add(output.resolve())
        ref = s.get("ref_audio", data.get("ref_audio"))
        if ref and (not Path(ref).is_file() or Path(ref).resolve() in outputs):
            raise ValueError("Referência ausente ou usada como saída")
    refs = {Path(s.get("ref_audio", data.get("ref_audio"))).resolve()
            for s in segments if s.get("ref_audio", data.get("ref_audio"))}
    if refs & outputs:
        raise ValueError("Referência usada como saída")
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    config = voice_config()
    p.add_argument("manifest", type=Path)
    p.add_argument("--modo", choices=["central", "direto"],
                   default=os.environ.get("CATALOGO_VOZ_MODO", config.get("modo", "direto")))
    p.add_argument("--central-runner",
                   default=os.environ.get("CATALOGO_CENTRAL_RUNNER", config.get("central_runner")))
    p.add_argument("--home", default=os.environ.get("OMNIVOICE_HOME"))
    p.add_argument("--python", dest="python_path")
    p.add_argument("--model", default="k2-fsa/OmniVoice")
    p.add_argument("--device", choices=["cpu", "cuda"])
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--check", action="store_true", help="valida caminhos e manifesto sem rede, modelos ou síntese")
    a = p.parse_args(argv)
    if a.modo not in ("central", "direto"):
        p.error("Modo inválido: configure central ou direto")
    data = validate_manifest(a.manifest)
    home = Path(a.home).resolve() if a.home else None
    if a.modo == "central":
        if not a.central_runner:
            p.error("Configure central_runner em sistema/voz.json, CATALOGO_CENTRAL_RUNNER ou --central-runner")
        interpreter = Path(a.python_path) if a.python_path else Path(sys.executable)
        runner = Path(a.central_runner).expanduser().resolve()
        validate_ref_text(data)
    else:
        interpreter = Path(a.python_path) if a.python_path else (
            home / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python") if home else Path(sys.executable))
        runner = home / "run_tts_batch.py" if home else Path(__file__).with_name("omnivoice_worker.py")
    if not interpreter.is_file() or not runner.is_file():
        p.error("Ambiente ausente: confira central_runner, OMNIVOICE_HOME e --python")
    if a.check:
        print(f"Manifesto válido: {len(data['segments'])} segmentos | modo: {a.modo}")
        return
    if not a.overwrite and any(Path(s["output"]).exists() for s in data["segments"]):
        p.error("WAV já existe; use novo manifesto/versão ou --overwrite")
    if a.modo == "direto":
        subprocess.run([str(interpreter), "-c", "from omnivoice.models.omnivoice import OmniVoice; import soundfile, torch; print('OmniVoice disponível')"], check=True)
    command = [str(interpreter), str(runner), "--manifest", str(a.manifest.resolve()), "--model", a.model]
    if a.device:
        command += ["--device", a.device]
    subprocess.run(command, check=True)
    for s in data["segments"]:
        with wave.open(s["output"], "rb") as wav:
            if wav.getnframes() == 0:
                raise ValueError(f"WAV vazio: {s['id']}")
    print("Todos os WAVs foram gerados e verificados")


if __name__ == "__main__":
    main()
