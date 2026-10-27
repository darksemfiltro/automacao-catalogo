"""Cria uma pasta de episódio pelo título, sem sobrescrever produção existente."""
import argparse
import re
import unicodedata
from pathlib import Path


def create_episode(root, title, episode_id):
    if not re.fullmatch(r"EP\d{2,4}", episode_id):
        raise ValueError("Use um ID como EP06")
    title = title.strip()
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:80].rstrip("-")
    if not slug:
        raise ValueError("Informe um título com letras ou números")
    episodes = Path(root).resolve() / "episodios"
    episodes.mkdir(parents=True, exist_ok=True)
    if any(episodes.glob(f"{episode_id}-*")):
        raise FileExistsError(f"{episode_id} já existe; use sua pasta para revisar o vídeo")
    target = episodes / f"{episode_id}-{slug}"
    target.mkdir()
    (target / "roteiro.md").write_text(f"# {episode_id} — {title}\n\n", encoding="utf-8")
    for folder in ("assets/audio", "assets/music", "assets/sfx", "renders", "revisoes", "entrada", "analise"):
        (target / "producao" / folder).mkdir(parents=True, exist_ok=True)
    import shutil
    references = Path(__file__).resolve().parents[1] / "referencias" / "base"
    shutil.copytree(references, target / "producao" / "referencias")
    (target / "producao" / "cenas.json").write_text(
        '{"theme": "cartoon", "chapters": {}, "cenas": {}}\n', encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("titulo")
    parser.add_argument("--id", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(create_episode(args.root, args.titulo, args.id))


if __name__ == "__main__":
    main()
