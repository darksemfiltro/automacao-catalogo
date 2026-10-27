import json
# -*- coding: utf-8 -*-
"""Crítica de direção em contexto fresco e o verificador local das etapas."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import critica
import render_final
import vendor
class CriticaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.projeto = Path(self.tmp.name) / "producao"
        self.projeto.mkdir()
        (self.projeto / "plano_cenas.json").write_text('{"cenas": []}', encoding="utf-8")
        (self.projeto / "episode.json").write_text('{"total": 2}', encoding="utf-8")

    def registrar(self, **kwargs):
        dados = dict(critic="leitor em contexto fresco", notas="notas",
                     achados="3 trechos com direção repetida", verdict="go-com-ressalvas")
        dados.update(kwargs)
        return critica.registrar(self.projeto, **dados)

    def test_critica_e_registrada_sem_confundir_com_aprovacao_humana(self):
        import critica
        registro = self.registrar()
        self.assertFalse(registro["human_approval"])
        self.assertIn("aprovação", registro["aviso"])
        self.assertIn("contrato/BIBLIA-CANAL.md", registro["inputs"])
        self.assertEqual(registro, critica.validar(self.projeto))

    def test_critica_exige_achado_escrito(self):
        import critica
        with self.assertRaisesRegex(ValueError, "achado"):
            self.registrar(achados="  ")

    def test_critica_exige_veredito_conhecido(self):
        import critica
        with self.assertRaisesRegex(ValueError, "Veredito"):
            self.registrar(verdict="parece-bom")

    def test_plano_editado_invalida_a_critica(self):
        import critica
        self.registrar()
        (self.projeto / "plano_cenas.json").write_text('{"cenas": ["nova"]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "desatualizada"):
            critica.validar(self.projeto)

    def test_contrato_editado_invalida_a_critica(self):
        import critica
        self.registrar()
        with patch.object(critica, "CONTRATO", ("AGENTS.md",)):
            registro = json.loads((self.projeto / "critica.json").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ValueError, "desatualizada"):
                (self.projeto / "critica.json").write_text(
                    json.dumps({**registro, "inputs": {**registro["inputs"], "contrato/AGENTS.md": "x"}}),
                    encoding="utf-8")
                critica.validar(self.projeto)

    def test_ausencia_de_critica_nao_e_aprovacao(self):
        import critica
        with self.assertRaisesRegex(ValueError, "não foi registrada"):
            critica.validar(self.projeto)
        self.assertFalse(critica.obrigatoria())

    def test_prompt_adversarial_e_adaptado_ao_canal(self):
        import critica
        for termo in ("adversarial", "Não valide", "contrato", "pausa é expressiva"):
            self.assertIn(termo, critica.BRIEF)


class RenderFinalGateTests(unittest.TestCase):
    def test_render_final_para_antes_de_chamar_subprocess(self):
        """A crítica entra antes de qualquer gate: nada é executado se ela reprovar."""
        import render_final
        with tempfile.TemporaryDirectory() as pasta:
            projeto = Path(pasta) / "producao"
            projeto.mkdir()
            with patch.object(sys, "argv", ["render_final.py", str(projeto)]), \
                 patch.object(render_final, "validate_review", side_effect=ValueError("revisão")), \
                 patch.object(subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    render_final.main()
            run.assert_not_called()

    def test_critica_invalida_barreia_o_render(self):
        import render_final
        with tempfile.TemporaryDirectory() as pasta:
            projeto = Path(pasta) / "producao"
            projeto.mkdir()
            (projeto / "plano_cenas.json").write_text('{"cenas": []}', encoding="utf-8")
            (projeto / "episode.json").write_text('{"total": 2}', encoding="utf-8")
            import critica
            critica.registrar(projeto, critic="leitor", notas="n", achados="a", verdict="go")
            (projeto / "plano_cenas.json").write_text('{"cenas": ["x"]}', encoding="utf-8")
            with patch.object(sys, "argv", ["render_final.py", str(projeto)]), \
                 patch.object(render_final, "validate_review"), \
                 patch.object(render_final, "read", return_value={"narration": "a.wav"}), \
                 patch.object(subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    render_final.main()
            run.assert_not_called()


class VerificaTests(unittest.TestCase):
    def test_todas_as_etapas_declaradas_sao_executaveis(self):
        import verifica
        self.assertEqual(set(verifica.ETAPAS), set(verifica.EXECUTAR))
        for etapa in verifica.ETAPAS:
            self.assertTrue(callable(verifica.EXECUTAR[etapa]), etapa)
        self.assertTrue((vendor.ROOT / verifica.FIXTURE_EPISODE).is_file())

    def test_etapa_que_precisa_de_node_e_pulada_com_aviso(self):
        import verifica
        with patch.object(verifica.shutil, "which", return_value=None), \
             patch("sys.stderr") as erro:
            self.assertEqual("pulado", verifica.etapa_composicao())
        self.assertTrue(any("npx" in str(chamada) for chamada in erro.write.call_args_list))

    def test_diff_sem_git_e_pulado_com_aviso(self):
        import verifica
        with tempfile.TemporaryDirectory() as pasta, \
             patch.object(verifica, "ROOT", Path(pasta)), \
             patch("sys.stderr") as erro:
            self.assertEqual("pulado", verifica.etapa_diff())
        self.assertTrue(any("git" in str(c) for c in erro.write.call_args_list))

    def test_aumento_de_barra_no_diff_barreia_a_verificacao(self):
        import verifica
        with tempfile.TemporaryDirectory() as pasta:
            (Path(pasta) / ".git").mkdir()
            with patch.object(verifica, "ROOT", Path(pasta)), \
                 patch.object(verifica.subprocess, "run") as run:
                run.return_value = SimpleNamespace(returncode=1)
                with self.assertRaises(SystemExit):
                    verifica.etapa_diff()


if __name__ == "__main__":
    unittest.main()
