import tempfile
import unittest
from pathlib import Path
from novo_episodio import create_episode


class EpisodeFolderTests(unittest.TestCase):
    def test_named_folder_and_duplicate_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            result = create_episode(directory, "Tipos de vulcão", "EP06")
            self.assertEqual(result.name, "EP06-tipos-de-vulcao")
            self.assertTrue((result / "producao/assets/audio").is_dir())
            with self.assertRaises(FileExistsError):
                create_episode(directory, "Outro título", "EP06")
            self.assertIn("Tipos de vulcão", (result / "roteiro.md").read_text(encoding="utf-8"))

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create_episode(directory, "Vídeo", "../../outside")
            self.assertEqual(list(Path(directory).iterdir()), [])
