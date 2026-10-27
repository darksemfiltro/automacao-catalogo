"""Gera o plano legível e registra revisão explícita antes do render final."""
import argparse
from pathlib import Path
from workflow import create_storyboard, review, validate_review


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["create", "review", "validate"])
    p.add_argument("project", type=Path)
    p.add_argument("--composition", default="hyperframes")
    p.add_argument("--reviewed-by")
    p.add_argument("--notes")
    p.add_argument("--frames", nargs="+", type=Path)
    a = p.parse_args()
    folder = a.project / a.composition
    if a.action == "create":
        create_storyboard(a.project)
    elif a.action == "review":
        if not a.reviewed_by or not a.notes or not a.frames:
            p.error("Revisão exige --reviewed-by, --notes e --frames")
        review(a.project, folder, a.reviewed_by, a.notes, a.frames)
    else:
        validate_review(a.project, folder)
    print("Storyboard:", a.action, "OK")


if __name__ == "__main__":
    main()
