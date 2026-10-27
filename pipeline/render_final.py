"""Única entrada suportada para render final: plano, revisão e verificações atuais."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from constraints import value as limite
from workflow import ROOT, read, validate_review


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", type=Path)
    p.add_argument("--composition", default="hyperframes")
    p.add_argument("--output", default="final.mp4", help="nome novo dentro de renders/")
    p.add_argument("--validate-only", action="store_true")
    a = p.parse_args()
    project = a.project.resolve()
    folder = project / a.composition
    if Path(a.output).name != a.output or not a.output.lower().endswith(".mp4"):
        p.error("Use apenas nome.mp4 como saída")
    output = project / "renders" / a.output
    if output.exists() and not a.validate_only:
        p.error("O render já existe; escolha outro nome")
    # Os limites vêm de CONSTRAINTS.md; nenhum número é repetido aqui.
    max_gap = limite("plano.max_gap_s")
    tolerancia = limite("render.tolerancia_duracao_s")
    validate_review(project, folder)
    # A crítica de direção não substitui a revisão humana; por padrão ela é
    # recomendada. `direcao.critica_obrigatoria` no CONSTRAINTS.md decide se
    # ela bloqueia o final.
    import critica
    if (project / critica.ARQUIVO).is_file():
        registro = critica.validar(project)
        print(f"crítica de direção: {registro['verdict']} por {registro['critic']} "
              f"(human_approval: false)")
    elif critica.obrigatoria():
        p.error("Crítica de direção obrigatória (CONSTRAINTS.md) e ausente")
    else:
        print("aviso: sem crítica de direção registrada; recomendada, não obrigatória "
              "(pipeline/critica.py review)")
    if not read(folder / "build.json").get("narration"):
        p.error("Final narrado exige áudio; para demo silenciosa use a CLI direta")
    # A validação de revisão não substitui a execução real dos gates.
    print(f"gates: max-gap {max_gap}s (plano.max_gap_s) | densidade pelo CONSTRAINTS.md")
    for script, args in [("gauntlet.py", [str(project / "episode.json"), "--strict"]),
                         ("checa_densidade.py", [str(folder / "index.html")])]:
        subprocess.run([sys.executable, str(ROOT / "pipeline" / script), *args], check=True)
    npx = shutil.which("npx")
    if not npx:
        p.error("Instale Node.js e execute npm ci")
    subprocess.run([npx, "--no-install", "hyperframes@0.8.144", "check", str(folder)], cwd=ROOT, check=True)
    validate_review(project, folder)
    if a.validate_only:
        print("Gates finais aprovados; nenhum MP4 renderizado")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([npx, "--no-install", "hyperframes@0.8.144", "render", str(folder),
                    "--quality", "high", "--fps", "30", "--output", str(output)], cwd=ROOT, check=True)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Render não produziu MP4 válido")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                            "-of", "json", str(output)], check=True, capture_output=True, text=True)
    metadata = json.loads(probe.stdout)
    if not any(s["codec_type"] == "video" for s in metadata["streams"]):
        raise RuntimeError("Render sem stream de vídeo")
    expected = read(project / "episode.json")["total"]
    if abs(float(metadata["format"]["duration"]) - expected) > tolerancia:
        raise RuntimeError(
            f"Duração do MP4 diverge do plano em mais de {tolerancia}s; revise a saída")
    print(f"Render final verificado: {output} "
          f"(dentro de {tolerancia}s de {expected:.2f}s; limites de CONSTRAINTS.md)")


if __name__ == "__main__":
    main()
