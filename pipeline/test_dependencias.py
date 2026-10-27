# -*- coding: utf-8 -*-
"""Dependências fixadas: GSAP e as woff2, por versão e sha256."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gen_comp
import vendor
class VendorTests(unittest.TestCase):
    def test_gsap_vendorizado_bate_com_o_pin(self):
        arquivo = "gsap.min.js"
        caminho, pin = vendor.source(arquivo)
        self.assertTrue(caminho.is_file())
        self.assertEqual(vendor.digest(caminho), pin["sha256"])
        self.assertEqual(pin["versao"], "3.14.2")

    def test_pin_exige_origem_e_licenca(self):
        with tempfile.TemporaryDirectory() as pasta:
            alvo = Path(pasta) / "PINS.json"
            alvo.write_text(json.dumps({"schema_version": 1, "arquivos": {
                "x.js": {"versao": "1", "sha256": "0" * 64, "origem": "https://exemplo/x.js"}}}),
                encoding="utf-8")
            with patch.object(vendor, "PINS", alvo):
                with self.assertRaisesRegex(ValueError, "licenca"):
                    vendor.pin("x.js")

    def test_arquivo_alterado_e_erro_e_nao_aviso(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "vendor").mkdir()
            (raiz / "vendor" / "x.js").write_text("alterado", encoding="utf-8")
            (raiz / "vendor" / "PINS.json").write_text(json.dumps({"schema_version": 1, "arquivos": {
                "x.js": {"versao": "1", "sha256": "0" * 64, "origem": "https://exemplo/x.js",
                         "licenca": "MIT"}}}), encoding="utf-8")
            with patch.object(vendor, "PINS", raiz / "vendor" / "PINS.json"), \
                 patch.object(vendor, "ROOT", raiz):
                with self.assertRaisesRegex(ValueError, "divergente"):
                    vendor.source("x.js")

    def test_script_tag_local_quando_o_pin_bate(self):
        self.assertEqual("assets/vendor/gsap.min.js", vendor.script_tag("gsap.min.js"))

    def test_script_tag_cai_para_cdn_com_aviso_quando_falta_o_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            pins = Path(pasta) / "PINS.json"
            pins.write_text(json.dumps({"schema_version": 1, "arquivos": {"gsap.min.js": {
                "versao": "3.14.2", "sha256": "0" * 64,
                "origem": "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js",
                "licenca": "GSAP Standard License"}}}), encoding="utf-8")
            with patch.object(vendor, "PINS", pins), \
                 patch.object(vendor, "ROOT", Path(pasta)):
                self.assertIn("cdn.jsdelivr.net", vendor.script_tag("gsap.min.js"))

    def test_composicao_usa_o_gsap_local(self):
        import gen_comp
        html = gen_comp.build_html({"total": 2, "elements": [], "scene_plan": []}, "cartoon")
        self.assertIn('<script src="assets/vendor/gsap.min.js">', html)
        self.assertNotIn("cdn.jsdelivr.net", html)


class FontesVendorizadasTests(unittest.TestCase):
    def test_todas_as_fontes_do_tema_estao_fixadas(self):
        pinos = vendor.pins()["fontes"]
        por_familia = {}
        for entrada in pinos.values():
            por_familia.setdefault(entrada["familia"], set()).add(entrada["peso"])
        self.assertEqual({600, 700, 800}, por_familia["Baloo 2"])
        self.assertEqual({700, 800}, por_familia["Nunito"])
        self.assertEqual({400}, por_familia["Patrick Hand"])
        self.assertEqual({600, 700}, por_familia["Caveat"])

    def test_woff2_bate_com_o_pin_e_tem_ofl(self):
        for arquivo, entrada in vendor.pins()["fontes"].items():
            caminho, pin = vendor.source(arquivo, "fontes")
            self.assertTrue(caminho.is_file(), arquivo)
            self.assertEqual(vendor.digest(caminho), pin["sha256"], arquivo)
            self.assertIn("1.1", pin["licenca"])
            self.assertFalse(pin["modificado"])

    def test_versao_do_pacote_esta_na_origem(self):
        """A origem é imutável por conter a versão, não só o sha256 local."""
        for arquivo, entrada in vendor.pins()["fontes"].items():
            self.assertIn(f"@{entrada['versao']}/", entrada["origem"], arquivo)

    def test_licenca_das_fontes_acompanha_o_pacote(self):
        licenca = vendor.ROOT / "vendor" / "fonts" / "LICENCA-OFL-1.1.txt"
        self.assertTrue(licenca.is_file())
        self.assertIn("SIL Open Font License", licenca.read_text(encoding="utf-8"))

    def test_css_local_nao_tem_nenhuma_url_remota(self):
        css = vendor.css_fontes()
        self.assertEqual(8, css.count("@font-face"))
        self.assertNotIn("http", css)
        for arquivo in vendor.pins()["fontes"]:
            self.assertIn(f"url('fonts/{arquivo}')", css)

    def test_install_fontes_copia_woff2_e_escreve_css(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "hyperframes"
            relatorio = vendor.install_fontes(destino)
            self.assertEqual("assets/vendor/fonts.css", relatorio)
            css = (destino / "assets" / "vendor" / "fonts.css").read_text(encoding="utf-8")
            self.assertIn("Baloo 2", css)
            woff2 = list((destino / "assets" / "vendor" / "fonts").glob("*.woff2"))
            self.assertEqual(len(vendor.pins()["fontes"]), len(woff2))

    def test_composicao_nao_usa_cdn_de_fonte(self):
        import gen_comp
        html = gen_comp.build_html({"total": 2, "elements": [], "scene_plan": []}, "cartoon",
                                   fontes_css=vendor.CSS_DEST)
        self.assertIn('<link rel="stylesheet" href="assets/vendor/fonts.css">', html)
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("fonts.gstatic.com", html)

    def test_sem_pin_de_fonte_a_composicao_avisa_e_usa_cdn(self):
        import gen_comp
        with patch.object(vendor, "tem_fontes", return_value=False):
            html = gen_comp.build_html({"total": 2, "elements": [], "scene_plan": []}, "cartoon")
        self.assertIn("fonts.googleapis.com", html)

    def test_sem_pin_de_gsap_a_composicao_avisa_e_usa_cdn(self):
        import gen_comp
        with tempfile.TemporaryDirectory() as pasta:
            pinos = Path(pasta) / "PINS.json"
            pinos.write_text(json.dumps({"schema_version": 1, "arquivos": {
                "gsap.min.js": {"versao": "3.14.2", "sha256": "0" * 64,
                                "origem": "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js",
                                "licenca": "GSAP Standard License"}}}), encoding="utf-8")
            with patch.object(vendor, "PINS", pinos), patch.object(vendor, "ROOT", Path(pasta)), \
                 patch("sys.stderr") as erro:
                html = gen_comp.build_html({"total": 2, "elements": [], "scene_plan": []}, "cartoon")
        self.assertIn("cdn.jsdelivr.net", html)
        self.assertTrue(any("AVISO" in str(c) for c in erro.write.call_args_list))

    def test_sem_pino_algum_a_composicao_falha_em_vez_de_silenciar(self):
        import gen_comp
        with tempfile.TemporaryDirectory() as pasta:
            pinos = Path(pasta) / "PINS.json"
            pinos.write_text(json.dumps({"schema_version": 1, "arquivos": {}}), encoding="utf-8")
            with patch.object(vendor, "PINS", pinos), patch.object(vendor, "ROOT", Path(pasta)):
                with self.assertRaises(KeyError):
                    gen_comp.build_html({"total": 2, "elements": [], "scene_plan": []}, "cartoon")


if __name__ == "__main__":
    unittest.main()
