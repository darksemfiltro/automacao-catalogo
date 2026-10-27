"""Proveniência, storyboard e revisão vinculados aos arquivos efetivamente usados."""
import hashlib
import html
import json
import math
from pathlib import Path

from constraints import value as limite

ROOT = Path(__file__).resolve().parents[1]
SCENE_TYPES = {"objeto", "detalhe", "dados", "dado_texto", "fenomeno"}
# A barra e as dependências fixadas entram no hash: mudá-las invalida storyboard
# e revisão, porque muda o veredicto dos gates.
SISTEMA = ("package-lock.json", "sistema/CENAS-NIVEL-1.md", "sistema/CONSTRAINTS.md")
VENDOR = ("vendor/PINS.json", "vendor/gsap.min.js")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def fingerprint(project):
    project = Path(project).resolve()
    files = {p for pattern in ("*.json",) for p in project.glob(pattern)
             if p.name not in {"storyboard.json", "review.json"}}
    files |= {p for folder in ("assets", "referencias", "entrada")
              for p in (project / folder).rglob("*") if p.is_file()}
    script = project.parent / "roteiro.md"
    if script.is_file():
        files.add(script)
    result = {p.relative_to(project.parent).as_posix(): digest(p) for p in sorted(files)}
    for p in sorted((ROOT / "pipeline").glob("*.py")):
        result["motor/" + p.name] = digest(p)
    for name in SISTEMA + VENDOR:
        p = ROOT / name
        if p.is_file():
            result[name] = digest(p)
    return result


def composition_hashes(folder):
    return {p.relative_to(folder).as_posix(): digest(p) for p in sorted(Path(folder).rglob("*"))
            if p.is_file() and p.name != "build.json"}


def record_build(project, folder, spec, theme, seconds, narration=None):
    write(Path(folder) / "build.json", {"schema_version": 1, "inputs": fingerprint(project),
        "spec": spec, "theme": theme, "seconds": seconds, "narration": narration,
        "files": composition_hashes(folder)})


def validate_episode(ep):
    total = ep.get("total", 0)
    if not isinstance(total, (float, int)) or not math.isfinite(total) or total <= 0:
        raise ValueError("Duração inválida")
    scenes = ep.get("scene_plan", [])
    if not scenes:
        raise ValueError("episode.json sem scene_plan; regenere com build_cenas.py")
    adj = limite("plano.tolerancia_adjacencia_s", .05)
    previous, ids = 0.0, set()
    for s in scenes:
        start, dur = s["start"], s["dur"]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (start, dur)):
            raise ValueError("Tempo não finito")
        if s["id"] in ids or s["tipo"] not in SCENE_TYPES or not s.get("motivo"):
            raise ValueError("Cena duplicada, desconhecida ou sem justificativa")
        ids.add(s["id"])
        if dur <= 0 or abs(start - previous) > adj:
            raise ValueError("Plano com lacuna, sobreposição ou duração negativa")
        previous = start + dur
    if abs(previous - total) > adj:
        raise ValueError("Plano não cobre a duração completa")


def create_storyboard(project):
    project = Path(project).resolve()
    ep = read(project / "episode.json")
    validate_episode(ep)
    texts = {}
    script = project.parent / "roteiro.md"
    if script.is_file():
        from parse_roteiro import parse
        texts = {s["id"]: s["text"] for s in parse(str(script))["segments"]}
    story = {"schema_version": 1, "inputs": fingerprint(project), "texts": texts,
             "episode": ep.get("episode"), "total": ep["total"],
             "scenes": ep["scene_plan"], "silence_policy": "preserve",
             "renderer": "hyperframes"}
    write(project / "storyboard.json", story)
    rows = []
    for s in story["scenes"]:
        values = [s["id"], f'{s["start"]:.2f}–{s["start"] + s["dur"]:.2f}s',
                  texts.get(s["segment"], s["segment"]), s["tipo"], s.get("entrada", ""), s["motivo"]]
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in values) + "</tr>")
    (project / "storyboard.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Storyboard</title>'
        '<style>body{font:16px system-ui;background:#101827;color:#eff6ff;padding:32px}'
        'td,th{padding:12px;border-bottom:1px solid #405065;text-align:left}table{width:100%}</style>'
        f'<h1>{html.escape(str(ep.get("episode", "Episódio")))}</h1>'
        '<p>Plano de cenas antes do render final. Pausas preservadas. Revisão visual e auditiva pendente.</p>'
        '<table><tr><th>Cena</th><th>Tempo</th><th>Fala (ou ID)</th><th>Tipo</th><th>Entrada</th><th>Motivo</th></tr>'
        + "".join(rows) + '</table>', encoding="utf-8")
    return story


def validate_current(project, folder):
    project, folder = Path(project).resolve(), Path(folder).resolve()
    story = read(project / "storyboard.json")
    current = fingerprint(project)
    ep = read(project / "episode.json")
    validate_episode(ep)
    if story["inputs"] != current or story["scenes"] != ep["scene_plan"]:
        raise ValueError("Storyboard desatualizado; gere novamente e revise")
    build = read(folder / "build.json")
    if build["inputs"] != current or build["files"] != composition_hashes(folder):
        raise ValueError("Composição alterada ou desatualizada; regenere e revise")
    if build["seconds"] is not None or build["spec"] != "episode.json":
        raise ValueError("Render final exige episode.json completo, sem --seconds")
    return story


def review(project, folder, reviewer, notes, frames):
    project, folder = Path(project).resolve(), Path(folder).resolve()
    validate_current(project, folder)
    if not reviewer.strip() or not notes.strip() or not frames:
        raise ValueError("Informe responsável, observações e quadros revisados")
    snapshots = {}
    for frame in frames:
        frame = Path(frame).resolve()
        if frame.suffix.lower() not in {".png", ".jpg", ".jpeg"} or not frame.is_file():
            raise ValueError("Quadro de revisão ausente ou inválido")
        snapshots[frame.relative_to(project).as_posix()] = digest(frame)
    write(project / "review.json", {"schema_version": 1, "reviewer": reviewer,
        "notes": notes, "storyboard_sha256": digest(project / "storyboard.json"),
        "build_sha256": digest(folder / "build.json"), "frames": snapshots})


def validate_review(project, folder):
    project, folder = Path(project).resolve(), Path(folder).resolve()
    validate_current(project, folder)
    report = read(project / "review.json")
    if not report.get("reviewer") or not report.get("notes") or not report.get("frames"):
        raise ValueError("Revisão incompleta")
    if (report["storyboard_sha256"] != digest(project / "storyboard.json") or
            report["build_sha256"] != digest(folder / "build.json")):
        raise ValueError("Revisão não corresponde ao storyboard/composição atual")
    for name, sha in report["frames"].items():
        frame = (project / name).resolve()
        if not frame.is_relative_to(project) or digest(frame) != sha:
            raise ValueError("Quadros de revisão alterados")
