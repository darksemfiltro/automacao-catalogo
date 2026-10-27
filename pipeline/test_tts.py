"""Provedores de voz: servidor HTTP e comando simulados, sem rede externa nem modelo."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import tts
import voz_config


def wav_bytes(frames=2400, rate=24000):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x01\x00" * frames)
    return buffer.getvalue()


class Servidor:
    """Imita POST /v1/audio/speech e guarda os pedidos recebidos."""

    def __init__(self, status=200, corpo=None):
        self.pedidos = []
        servidor = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                tamanho = int(self.headers.get("Content-Length", 0))
                servidor.pedidos.append({"caminho": self.path, "auth": self.headers.get("Authorization"),
                                         "json": json.loads(self.rfile.read(tamanho))})
                self.send_response(status)
                self.send_header("Content-Type", "audio/wav")
                self.end_headers()
                self.wfile.write(corpo if corpo is not None else wav_bytes())

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def fechar(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class TtsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.saidas = [self.root / "audio" / "a01.wav", self.root / "audio" / "a02.wav"]
        self.manifest.write_text(json.dumps({"language": "Portuguese", "segments": [
            {"id": "a01", "text": "Primeira frase.", "output": str(self.saidas[0]), "speed": 1.0},
            {"id": "a02", "text": "Segunda frase.", "output": str(self.saidas[1]), "speed": 1.2},
        ]}), encoding="utf-8")
        patch.dict(os.environ, {"MINHA_CHAVE": "segredo-de-teste"}).start()
        patch.object(voz_config, "carregar_env", return_value=[]).start()
        self.addCleanup(patch.stopall)

    def config(self, **api):
        base = {"base_url": "", "modelo": "m", "voz": "v", "chave_env": "MINHA_CHAVE", "timeout_s": 5}
        base.update(api)
        return {"provedor": "openai", "api": base}

    def rodar(self, config, *args):
        with patch.object(voz_config, "carregar", return_value=config):
            tts.main([str(self.manifest), *args])

    def test_openai_envia_pedido_correto_e_grava_wavs(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.assertTrue(all(s.is_file() for s in self.saidas))
        primeiro, segundo = servidor.pedidos
        self.assertEqual("/v1/audio/speech", primeiro["caminho"])
        self.assertEqual("Bearer segredo-de-teste", primeiro["auth"])
        self.assertEqual({"model": "m", "input": "Primeira frase.", "voice": "v", "response_format": "wav"},
                         primeiro["json"])
        self.assertEqual(1.2, segundo["json"]["speed"])

    def test_openai_sem_chave_falha_antes_de_chamar_a_rede(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.assertEqual([], servidor.pedidos)

    def test_servidor_local_sem_chave_quando_nao_exige(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        with patch.dict(os.environ, {}, clear=True):
            self.rodar(self.config(base_url=servidor.url, exige_chave=False), "--provedor", "openai")
        self.assertIsNone(servidor.pedidos[0]["auth"])

    def test_erro_4xx_nao_e_repetido(self):
        servidor = Servidor(status=401, corpo=b'{"error":"invalid"}')
        self.addCleanup(servidor.fechar)
        with self.assertRaises(SystemExit):
            self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.assertEqual(1, len(servidor.pedidos))

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg ausente")
    def test_resposta_que_nao_e_wav_e_convertida(self):
        mp3 = subprocess.run(["ffmpeg", "-v", "error", "-f", "wav", "-i", "pipe:0", "-f", "mp3", "pipe:1"],
                             input=wav_bytes(24000), capture_output=True).stdout
        servidor = Servidor(corpo=mp3)
        self.addCleanup(servidor.fechar)
        self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        with wave.open(str(self.saidas[0]), "rb") as wav:
            self.assertGreater(wav.getnframes(), 0)

    def test_comando_local_recebe_texto_por_stdin_e_grava_saida(self):
        codigo = ("import sys,wave;t=sys.stdin.read();assert t.strip();"
                  "w=wave.open(sys.argv[1],'wb');w.setnchannels(1);w.setsampwidth(2);"
                  "w.setframerate(22050);w.writeframes(b'\\x01\\x00'*len(t)*100)")
        config = {"provedor": "comando", "comando": {"argv": [sys.executable, "-c", codigo, "{saida}"]}}
        self.rodar(config, "--provedor", "comando")
        self.assertTrue(all(s.is_file() for s in self.saidas))

    def test_comando_com_arquivo_de_texto(self):
        codigo = ("import sys,wave;t=open(sys.argv[1],encoding='utf-8').read();assert t.strip();"
                  "w=wave.open(sys.argv[2],'wb');w.setnchannels(1);w.setsampwidth(2);"
                  "w.setframerate(22050);w.writeframes(b'\\x01\\x00'*200)")
        config = {"provedor": "comando", "comando": {
            "argv": [sys.executable, "-c", codigo, "{texto_arquivo}", "{saida}"], "entrada": "arquivo"}}
        self.rodar(config, "--provedor", "comando")
        self.assertTrue(self.saidas[1].is_file())

    def test_comando_que_nao_gera_arquivo_e_erro_claro(self):
        config = {"provedor": "comando", "comando": {"argv": [sys.executable, "-c", "pass"]}}
        with self.assertRaises(SystemExit):
            self.rodar(config, "--provedor", "comando")

    def test_check_valida_sem_sintetizar(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        self.rodar(self.config(base_url=servidor.url), "--provedor", "openai", "--check")
        self.assertEqual([], servidor.pedidos)
        self.assertFalse(self.saidas[0].exists())

    def test_nao_sobrescreve_sem_pedido(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        self.saidas[0].parent.mkdir(parents=True)
        self.saidas[0].write_bytes(wav_bytes())
        with self.assertRaises(SystemExit):
            self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.rodar(self.config(base_url=servidor.url), "--provedor", "openai", "--overwrite")

    def test_omnivoice_delega_para_o_executor_existente(self):
        dados = json.loads(self.manifest.read_text(encoding="utf-8"))
        dados["ref_audio"] = str(self.root / "voz.wav")
        self.manifest.write_text(json.dumps(dados), encoding="utf-8")
        with patch.object(tts.omnivoice_tts, "main") as principal:
            self.rodar({"provedor": "omnivoice"}, "--provedor", "omnivoice", "--check")
        principal.assert_called_once_with([str(self.manifest), "--check"])

    def test_omnivoice_recusa_manifesto_sem_referencia(self):
        with patch.object(tts.omnivoice_tts, "main") as principal, self.assertRaises(SystemExit):
            self.rodar({"provedor": "omnivoice"}, "--provedor", "omnivoice")
        principal.assert_not_called()

    def test_provedor_desconhecido_vindo_da_configuracao_e_recusado(self):
        with self.assertRaises(SystemExit) as erro:
            self.rodar({"provedor": "openia"})
        self.assertNotEqual(0, erro.exception.code)

    def test_json_invalido_na_configuracao_vira_mensagem(self):
        with patch.object(voz_config, "carregar", side_effect=ValueError("virgula")), (
                self.assertRaises(SystemExit)):
            tts.main([str(self.manifest)])

    def test_chaves_literais_no_argv_nao_quebram(self):
        script = self.root / "gera.py"
        linhas = ["import sys, wave",
                  "w = wave.open(sys.argv[2], 'wb')",
                  "w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)",
                  "w.writeframes(bytes(100))"]
        script.write_text(os.linesep.join(linhas) + os.linesep, encoding="utf-8")
        config = {"provedor": "comando", "comando": {
            "argv": [sys.executable, str(script), '{"a": 1}', "{saida}"]}}
        self.rodar(config, "--provedor", "comando")
        self.assertTrue(self.saidas[0].is_file())

    def test_wav_velho_nao_passa_quando_o_comando_nao_grava(self):
        self.saidas[0].parent.mkdir(parents=True)
        self.saidas[0].write_bytes(wav_bytes())
        config = {"provedor": "comando", "comando": {"argv": [sys.executable, "-c", "pass"]}}
        with self.assertRaises(SystemExit):
            self.rodar(config, "--provedor", "comando", "--overwrite")
        self.assertFalse(self.saidas[0].exists())

    def test_retomar_pula_o_que_ja_existe(self):
        servidor = Servidor()
        self.addCleanup(servidor.fechar)
        self.saidas[0].parent.mkdir(parents=True)
        self.saidas[0].write_bytes(wav_bytes())
        self.rodar(self.config(base_url=servidor.url), "--provedor", "openai", "--retomar")
        self.assertEqual(["Segunda frase."], [p["json"]["input"] for p in servidor.pedidos])
        self.assertTrue(self.saidas[1].is_file())

    def test_resposta_invalida_nao_deixa_arquivo_no_disco(self):
        servidor = Servidor(corpo=b"RIFF isto nao e um wav")
        self.addCleanup(servidor.fechar)
        with self.assertRaises(SystemExit):
            self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.assertFalse(self.saidas[0].exists())
        self.assertFalse(self.saidas[0].with_name("a01.wav.tmp").exists())

    def test_corpo_do_erro_nao_expoe_a_chave(self):
        servidor = Servidor(status=400, corpo=b'{"error":"bad key segredo-de-teste"}')
        self.addCleanup(servidor.fechar)
        with self.assertRaises(SystemExit):
            with patch("sys.stderr", new_callable=io.StringIO) as erro:
                self.rodar(self.config(base_url=servidor.url), "--provedor", "openai")
        self.assertNotIn("segredo-de-teste", erro.getvalue())

    def test_overwrite_e_retomar_nao_combinam(self):
        with self.assertRaises(SystemExit):
            self.rodar(self.config(base_url="http://127.0.0.1:1/v1"), "--provedor", "openai",
                       "--overwrite", "--retomar")


class ConfigTests(unittest.TestCase):
    def test_local_sobrepoe_e_mescla_chaves_aninhadas(self):
        with tempfile.TemporaryDirectory() as pasta:
            publico = Path(pasta) / "voz.json"
            publico.write_text(json.dumps({"provedor": "omnivoice", "api": {"voz": "alloy", "modelo": "x"}}))
            Path(pasta, "voz.local.json").write_text(json.dumps({"api": {"voz": "nova"}}))
            with patch.object(voz_config, "CONFIG_PATH", publico):
                config = voz_config.carregar(publico)
        self.assertEqual({"provedor": "omnivoice", "api": {"voz": "nova", "modelo": "x"}}, config)

    def test_variaveis_carregam_sem_sobrescrever_o_ambiente(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "variaveis"
            arquivo.write_text('# chaves\nCHAVE_NOVA="abc"\nCHAVE_JA_DEFINIDA=outra\nvazia=\n', encoding="utf-8")
            with patch.dict(os.environ, {"CHAVE_JA_DEFINIDA": "original"}):
                carregadas = voz_config.carregar_env(arquivo)
                self.assertEqual(["CHAVE_NOVA"], carregadas)
                self.assertEqual("abc", os.environ["CHAVE_NOVA"])
                self.assertEqual("original", os.environ["CHAVE_JA_DEFINIDA"])
                os.environ.pop("CHAVE_NOVA")

    def test_variaveis_ausentes_nao_fazem_nada(self):
        self.assertEqual([], voz_config.carregar_env(Path("nao-existe-variaveis")))

    def test_arquivo_ausente_devolve_vazio(self):
        self.assertEqual({}, voz_config.carregar(Path("nao-existe-voz.json")))


if __name__ == "__main__":
    unittest.main()
