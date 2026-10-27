# -*- coding: utf-8 -*-
"""A barra de qualidade é uma, fica escrita, e ninguém a afrouxa em silêncio."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import constraints
import floor_guard
from constraints import PATH as CONSTRAINTS_PATH


def _documento(**overrides):
    base = {
        "schema_version": 1,
        "revisado_em": "2026-10-04",
        "piso": list(constraints.FLOOR),
        "limites": {"plano.max_gap_s": {"valor": 0.9, "unidade": "s",
                                         "motivo": "ritmo", "verificado_por": "gauntlet.py",
                                         "roda_em": "todo render final"}},
        "medido": [{"metrica": "testes", "hoje": 58, "direcao": "nao pode cair"}],
        "excecoes": [],
        "remoto": [],
    }
    base.update(overrides)
    return base


def _markdown(data):
    return "# CONSTRAINTS\n\ntexto\n\n```json\n" + json.dumps(data, ensure_ascii=False) + "\n```\n"


class ConstraintsFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "CONSTRAINTS.md"

    def escrever(self, data):
        self.path.write_text(_markdown(data), encoding="utf-8")

    def test_barra_do_repositorio_valida(self):
        data = constraints.load(CONSTRAINTS_PATH)
        self.assertEqual(1, data["schema_version"])
        for chave in ("plano.max_gap_s", "montagem.max_buraco_s", "render.tolerancia_duracao_s",
                      "audio.lufs_integrado", "direcao.critica_obrigatoria"):
            self.assertIn(chave, data["limites"])

    def test_limite_sem_comando_e_recusado(self):
        self.escrever(_documento(limites={"plano.max_gap_s": {"valor": 0.9, "unidade": "s",
                                                            "motivo": "ritmo", "roda_em": "final"}}))
        with self.assertRaisesRegex(constraints.ConstraintError, "verificado_por"):
            constraints.load(self.path)

    def test_limite_sem_motivo_e_recusado(self):
        self.escrever(_documento(limites={"plano.max_gap_s": {"valor": 0.9, "unidade": "s",
                                                            "verificado_por": "x", "roda_em": "y"}}))
        with self.assertRaisesRegex(constraints.ConstraintError, "motivo"):
            constraints.load(self.path)

    def test_valor_nao_numerico_e_recusado(self):
        self.escrever(_documento(limites={"plano.max_gap_s": {"valor": "0.9 s", "unidade": "s",
                                                            "motivo": "m", "verificado_por": "v",
                                                            "roda_em": "r"}}))
        with self.assertRaisesRegex(constraints.ConstraintError, "valor"):
            constraints.load(self.path)

    def test_excecao_sem_responsavel_ou_prazo_e_recusada(self):
        self.escrever(_documento(excecoes=[{"id": "E1", "limite": "plano.max_gap_s",
                                            "motivo": "ep curtissimo"}]))
        with self.assertRaisesRegex(constraints.ConstraintError, "responsavel"):
            constraints.load(self.path)

    def test_excecao_para_limite_inexistente_e_recusada(self):
        self.escrever(_documento(excecoes=[{"id": "E1", "limite": "plano.max_gap_ms",
                                            "motivo": "x", "responsavel": "y",
                                            "expira": "2027-01-01"}]))
        with self.assertRaisesRegex(constraints.ConstraintError, "limite inexistente"):
            constraints.load(self.path)

    def test_piso_desconhecido_e_recusado(self):
        self.escrever(_documento(piso=["Pague o devo quando quiser"]))
        with self.assertRaisesRegex(constraints.ConstraintError, "piso nao reconhecida"):
            constraints.load(self.path)

    def test_data_de_revisao_obrigatoria(self):
        self.escrever(_documento(revisado_em=""))
        with self.assertRaisesRegex(constraints.ConstraintError, "revisado_em"):
            constraints.load(self.path)

    def test_arquivo_sem_bloco_json_e_recusado(self):
        self.path.write_text("# CONSTRAINTS\n\nsem bloco\n", encoding="utf-8")
        with self.assertRaises(constraints.ConstraintError):
            constraints.load(self.path)

    def test_ausente_nao_derruba_o_agente_que_so_precisa_do_piso(self):
        data = constraints.load(Path(self.tmp.name) / "nao-existe.md")
        self.assertTrue(data.get("_ausente"))
        self.assertEqual(constraints.FLOOR, tuple(data["piso"]))

    def test_limite_ausente_sem_padrao_exige_o_arquivo(self):
        self.escrever(_documento())
        with self.assertRaisesRegex(constraints.ConstraintError, "ausente"):
            constraints.value("plano.max_gap_ms", path=self.path)

    def test_padrao_so_entra_quando_a_chave_nao_existe(self):
        self.escrever(_documento())
        self.assertEqual(0.9, constraints.value("plano.max_gap_s", 42, path=self.path))
        self.assertEqual(42, constraints.value("plano.max_gap_ms", 42, path=self.path))

    def test_motor_nao_repete_numero(self):
        """Os gates leem a barra; nenhum módulo repete o literal."""
        motor = Path(constraints.ROOT / "pipeline")
        for nome, chave in (("gauntlet.py", "plano.max_gap_s"),
                            ("checa_densidade.py", "montagem.max_buraco_s"),
                            ("render_final.py", "render.tolerancia_duracao_s")):
            texto = (motor / nome).read_text(encoding="utf-8")
            self.assertIn(f'limite("{chave}")', texto, f"{nome} deve ler {chave} da barra")


class FloorGuardTests(unittest.TestCase):
    def diff(self, arquivo, linhas, removidas=()):
        corpo = [f"diff --git a/{arquivo} b/{arquivo}", f"--- a/{arquivo}", f"+++ b/{arquivo}",
                 "@@ -1,0 +1,5 @@"] + [f"+{linha}" for linha in linhas] + \
                [f"-{linha}" for linha in removidas]
        return "\n".join(corpo) + "\n"

    def test_barra_intacta_nao_acusa(self):
        achados = floor_guard.scan(self.diff("pipeline/gen_comp.py", ["x = 1", "y = 2"]))
        self.assertEqual([], achados)

    def test_limite_alterado_e_acusado(self):
        achados = floor_guard.scan(self.diff(
            f"sistema/{CONSTRAINTS_PATH.name}", ['"valor": 3.0,']))
        self.assertEqual(["LIMITE_ALTERADO"], [a["categoria"] for a in achados])

    def test_excecao_nova_e_acusada(self):
        achados = floor_guard.scan(self.diff(
            f"sistema/{CONSTRAINTS_PATH.name}", ['"id": "E7",', '"expira": "2027-01-01"']))
        self.assertEqual(["LIMITE_ALTERADO"], [a["categoria"] for a in achados])

    def test_limite_passado_na_mao_e_acusado(self):
        achados = floor_guard.scan(self.diff(
            "README.md", ["python pipeline/gauntlet.py ep.json --strict --max-gap 2.8"]))
        self.assertEqual(["LIMITE_NA_MAO"], [a["categoria"] for a in achados])

    def test_teste_pulado_e_acusado(self):
        achados = floor_guard.scan(self.diff(
            "pipeline/test_nivel1.py", ["    @unittest.skip(\"lento\")"]))
        self.assertEqual(["TESTE_PULADO"], [a["categoria"] for a in achados])

    def test_teste_removido_e_acusado(self):
        achados = floor_guard.scan(self.diff(
            "pipeline/test_gen_comp.py", ["    def test_novo(self): pass"], ["    def test_antigo(self): pass"]))
        self.assertEqual(["TESTE_PULADO"], [a["categoria"] for a in achados])

    def test_verificador_calado_e_acusado(self):
        achados = floor_guard.scan(self.diff("pipeline/gen_comp.py", ["    except ValueError: pass"]))
        self.assertEqual(["VERIFICADOR_CALADO"], [a["categoria"] for a in achados])

    def test_check_false_em_gate_e_acusado(self):
        achados = floor_guard.scan(self.diff(
            "pipeline/render_final.py", ["subprocess.run(cmd, check=False)"]))
        self.assertEqual(["VERIFICADOR_CALADO"], [a["categoria"] for a in achados])

    def test_trabalho_inacabado_no_motor_e_acusado(self):
        achados = floor_guard.scan(self.diff("pipeline/gen_comp.py", ["    # TODO: revisar isto"]))
        self.assertEqual(["TRABALHO_INACABADO"], [a["categoria"] for a in achados])

    def test_stub_fora_do_motor_nao_acusa(self):
        achados = floor_guard.scan(self.diff("episodios/EP05/roteiro.md", ["TODO: escrever"]))
        self.assertEqual([], achados)

    def test_codigos_de_saida_por_argumento(self):
        argv = ["floor_guard.py"]
        with patch.object(sys, "argv", argv), patch.object(floor_guard, "_git", return_value=""):
            with self.assertRaises(SystemExit) as erro:
                floor_guard.main()
        self.assertEqual(0, erro.exception.code)
        with patch.object(sys, "argv", argv), patch.object(floor_guard, "_git", return_value=self.diff(
                "sistema/CONSTRAINTS.md", ['"valor": 9.9,'])):
            with self.assertRaises(SystemExit) as erro:
                floor_guard.main()
        self.assertEqual(1, erro.exception.code)
        with patch.object(sys, "argv", argv), patch.object(floor_guard, "_git", return_value=None):
            with self.assertRaises(SystemExit) as erro:
                floor_guard.main()
        self.assertEqual(2, erro.exception.code)

    def test_cli_rodando_fora_do_git_nao_apaga_a_barra(self):
        proc = subprocess.run([sys.executable, "pipeline/floor_guard.py"],
                              cwd=constraints.ROOT, capture_output=True, text=True)
        self.assertIn(proc.returncode, (0, 1, 2))


if __name__ == "__main__":
    unittest.main()
