"""Create a temporary HyperFrames project with a bounded duration.

It never edits the production composition. Render the returned directory with
`npx --yes hyperframes@0.8.144 render --quality draft` to make a review-only preview.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--out-dir")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    source = (project / "hyperframes").resolve()
    destination = (Path(args.out_dir) if args.out_dir
                   else Path(tempfile.mkdtemp(prefix="catalogo-preview-"))).resolve()
    # copytree cannot safely copy a directory into itself. Also guard against an
    # ancestor destination, which would otherwise be deleted by rmtree below.
    if destination == source or source in destination.parents or destination in source.parents:
        parser.error("--out-dir deve ficar fora de hyperframes e não pode conter essa pasta")
    if args.out_dir and destination.exists():
        parser.error(f"--out-dir já existe: {destination}")
    # mkdtemp creates an empty directory for the default destination.
    shutil.copytree(source, destination, dirs_exist_ok=not args.out_dir)
    html_path = destination / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html, replaced = re.subn(
        r'(<div[^>]+id="root"[^>]+data-duration=")[^"]+"',
        rf'\g<1>{args.seconds:.3f}"',
        html,
        count=1,
    )
    if replaced != 1:
        raise RuntimeError("root data-duration não encontrado")
    def keep_video(match):
        tag = match.group(0)
        start = re.search(r'data-start="([0-9.]+)"', tag)
        if start and float(start.group(1)) >= args.seconds:
            return ""
        return tag
    # The first-minute preview has no authored b-roll video yet. Removing
    # later video clips avoids extracting media that cannot appear in this copy.
    html = re.sub(r"<video\b[^>]*></video>", keep_video, html)
    html_path.write_text(html, encoding="utf-8")
    sidecar = destination / "index.motion.json"
    if sidecar.exists():
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        data["duration"] = args.seconds
        sidecar.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
