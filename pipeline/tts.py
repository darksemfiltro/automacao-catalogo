"""Narração por provedor: OmniVoice, API compatível com OpenAI ou comando local.

Um manifesto (`tts_manifest_v1.json`) entra e um WAV por segmento sai. O resto
do pipeline só enxerga os WAVs, então trocar de provedor não muda mais nada.

  python pipeline/tts.py P/tts_manifest_v1.json --check
  python pipeline/tts.py P/tts_manifest_v1.json
  python pipeline/tts.py P/tts_manifest_v1.json --provedor openai
  python pipeline/tts.py P/tts_manifest_v1.json --retomar

O provedor vem de --provedor, da variável CATALOGO_VOZ_PROVEDOR ou de
sistema/voz.json (campo "provedor"). Veja prompts/02-voz-local.md e
prompts/03-voz-api.md para configurar cada um.

Provedores:
  omnivoice  clona uma voz de referência; delega para omnivoice_tts.py.
  openai     POST {base_url}/audio/speech. Serve para a OpenAI e para qualquer
             servidor local que imite essa rota (Kokoro-FastAPI, openedai-speech
             e semelhantes). A chave vem de uma variável de ambiente.
  comando    executa um programa local por segmento (Piper, por exemplo).

Se a síntese parar no meio, --retomar pula os segmentos que já têm um WAV
válido e gera só os que faltam. --overwrite refaz tudo.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import omnivoice_tts
import voz_config

PROVEDORES = ("omnivoice", "openai", "comando")
TENTATIVAS = 3
TEMPORARIOS = (429, 500, 502, 503, 504)


class ErroVoz(RuntimeError):
    """Falha de configuração ou de síntese, com mensagem pronta para o usuário."""


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Não segue redirecionamento: o cabeçalho Authorization não pode ir para outro host."""

    def redirect_request(self, *args, **kwargs):
        return None


def _abrir(pedido, timeout):
    return urllib.request.build_opener(_SemRedirecionar).open(pedido, timeout=timeout)


def _wav_valido(path):
    try:
        with wave.open(str(path), "rb") as wav:
            return wav.getnframes() > 0
    except (wave.Error, EOFError, OSError):
        return False


def _gravar_wav(destino, dados, segmento):
    """Grava em arquivo temporário e só troca pelo definitivo depois de validar."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_bytes(dados)
    if not _wav_valido(temporario):
        temporario.unlink(missing_ok=True)
        raise ErroVoz(f"A resposta do segmento {segmento} não é um WAV válido ou está vazia")
    temporario.replace(destino)


def _para_wav(dados):
    """A API pode devolver mp3 ou outro formato; converte com ffmpeg se não for WAV."""
    if dados[:4] == b"RIFF":
        return dados
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ErroVoz("A API não devolveu WAV e o ffmpeg não está no PATH para converter")
    resultado = subprocess.run([ffmpeg, "-v", "error", "-i", "pipe:0", "-f", "wav", "pipe:1"],
                               input=dados, capture_output=True)
    if resultado.returncode != 0 or not resultado.stdout:
        raise ErroVoz("O ffmpeg não conseguiu converter a resposta da API para WAV")
    return resultado.stdout


def _sem_chave(texto, chave):
    return texto.replace(chave, "***") if chave else texto


def _pedir_audio(api, texto, velocidade, abrir=_abrir):
    chave = os.environ.get(api.get("chave_env") or "")
    base = str(api.get("base_url") or "").rstrip("/")
    if not base:
        raise ErroVoz("Configure api.base_url em sistema/voz.json (ou voz.local.json)")
    corpo = {"model": api.get("modelo"), "input": texto, "voice": api.get("voz"),
             "response_format": "wav"}
    if api.get("instrucoes"):
        corpo["instructions"] = api["instrucoes"]
    if velocidade and float(velocidade) != 1.0:
        corpo["speed"] = float(velocidade)
    cabecalhos = {"Content-Type": "application/json"}
    if chave:
        cabecalhos["Authorization"] = f"Bearer {chave}"
        partes = urllib.parse.urlsplit(base)
        if partes.scheme == "http" and partes.hostname not in ("localhost", "127.0.0.1", "::1"):
            print("aviso: a chave seguirá sem criptografia (http://). Use https://", file=sys.stderr)
    elif api.get("exige_chave", True):
        raise ErroVoz(f"Defina a variável de ambiente {api.get('chave_env')} com a chave da API "
                      '(ou "exige_chave": false para servidor local sem chave)')
    pedido = urllib.request.Request(f"{base}/audio/speech", data=json.dumps(corpo).encode("utf-8"),
                                    headers=cabecalhos, method="POST")
    ultimo = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            with abrir(pedido, float(api.get("timeout_s", 120))) as resposta:
                return resposta.read()
        except urllib.error.HTTPError as exc:
            detalhe = _sem_chave(exc.read()[:200].decode("utf-8", "replace"), chave)
            ultimo = f"HTTP {exc.code}: {detalhe}"
            exc.close()
            if exc.code not in TEMPORARIOS:
                break
        except OSError as exc:
            ultimo = _sem_chave(str(exc), chave)
        if tentativa < TENTATIVAS:
            time.sleep(min(2 ** tentativa, 8))
    raise ErroVoz(f"A API de voz falhou: {ultimo}")


def sintetizar_openai(data, config, abrir=_abrir, retomar=False):
    api = config.get("api") or {}
    for s in data["segments"]:
        if retomar and _wav_valido(s["output"]):
            print(f"pulado {s['id']} (WAV já existe)")
            continue
        audio = _para_wav(_pedir_audio(api, s["text"], s.get("speed"), abrir))
        _gravar_wav(s["output"], audio, s["id"])
        print(f"ok {s['id']}")


def _montar_comando(argv, valores):
    comando = []
    for parte in argv:
        for chave, valor in valores.items():
            parte = parte.replace("{" + chave + "}", valor)
        comando.append(parte)
    return comando


def sintetizar_comando(data, config, retomar=False):
    spec = config.get("comando") or {}
    argv = spec.get("argv")
    if not argv or not isinstance(argv, list):
        raise ErroVoz('Configure comando.argv (lista) em sistema/voz.json, por exemplo '
                      '["piper", "--model", "pt_BR-faber-medium.onnx", "--output_file", "{saida}"]')
    entrada = spec.get("entrada", "stdin")
    if entrada not in ("stdin", "arquivo"):
        raise ErroVoz('comando.entrada deve ser "stdin" ou "arquivo"')
    limite = float(spec.get("timeout_s", 300))
    for s in data["segments"]:
        destino = Path(s["output"])
        if retomar and _wav_valido(destino):
            print(f"pulado {s['id']} (WAV já existe)")
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.unlink(missing_ok=True)  # um WAV velho não pode passar como se fosse novo
        with tempfile.TemporaryDirectory() as pasta:
            texto_arquivo = Path(pasta) / "texto.txt"
            texto_arquivo.write_text(s["text"], encoding="utf-8")
            valores = {"saida": str(destino), "texto_arquivo": str(texto_arquivo), "id": s["id"]}
            try:
                resultado = subprocess.run(
                    _montar_comando(argv, valores),
                    input=s["text"].encode("utf-8") if entrada == "stdin" else None,
                    capture_output=True, timeout=limite)
            except subprocess.TimeoutExpired:
                raise ErroVoz(f"O comando de voz passou de {limite:g} s no segmento {s['id']}") from None
        if resultado.returncode != 0:
            detalhe = resultado.stderr.decode("utf-8", "replace")[-300:]
            raise ErroVoz(f"O comando de voz falhou no segmento {s['id']}: {detalhe}")
        if not destino.is_file():
            raise ErroVoz(f"O comando terminou sem gerar {destino.name}; confira o campo {{saida}}")
        if not _wav_valido(destino):
            destino.unlink(missing_ok=True)
            raise ErroVoz(f"O arquivo gerado para {s['id']} não é um WAV válido ou está vazio")
        print(f"ok {s['id']}")


def _checar(provedor, config):
    """Valida a configuração sem rede, sem modelo e sem síntese."""
    if provedor == "openai":
        api = config.get("api") or {}
        if not api.get("base_url"):
            raise ErroVoz("Configure api.base_url")
        if api.get("exige_chave", True) and not os.environ.get(api.get("chave_env") or ""):
            raise ErroVoz(f"Defina a variável de ambiente {api.get('chave_env')}")
    elif provedor == "comando":
        argv = (config.get("comando") or {}).get("argv")
        if not argv or not isinstance(argv, list):
            raise ErroVoz("Configure comando.argv")
        if shutil.which(argv[0]) is None and not Path(argv[0]).is_file():
            raise ErroVoz(f"Programa não encontrado: {argv[0]}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    voz_config.carregar_env()
    try:
        config = voz_config.carregar()
    except ValueError as exc:
        p.error(f"sistema/voz.json ou sistema/voz.local.json não é um JSON válido: {exc}")
    p.add_argument("manifest", type=Path)
    p.add_argument("--provedor", default=os.environ.get("CATALOGO_VOZ_PROVEDOR", config.get("provedor", "omnivoice")),
                   help="omnivoice, openai ou comando")
    p.add_argument("--overwrite", action="store_true", help="refaz todos os WAVs")
    p.add_argument("--retomar", action="store_true", help="pula os segmentos que já têm WAV válido")
    p.add_argument("--check", action="store_true", help="valida manifesto e configuração sem sintetizar")
    a, resto = p.parse_known_args(argv)
    if a.provedor not in PROVEDORES:
        p.error(f"Provedor desconhecido: {a.provedor!r}. Use um de: {', '.join(PROVEDORES)}")
    if a.overwrite and a.retomar:
        p.error("Use --overwrite ou --retomar, não os dois")
    try:
        if a.provedor == "omnivoice":
            if a.retomar:
                raise ErroVoz("--retomar não existe para o omnivoice; use --overwrite ou outra versão")
            data = json.loads(a.manifest.read_text(encoding="utf-8"))
            if not data.get("ref_audio"):
                raise ErroVoz("O OmniVoice precisa de voz de referência: gere o manifesto sem "
                              "--sem-referencia, com --ref-audio e --ref-text")
            extra = (["--overwrite"] if a.overwrite else []) + (["--check"] if a.check else [])
            return omnivoice_tts.main([str(a.manifest), *extra, *resto])
        if resto:
            p.error(f"Argumentos desconhecidos para o provedor {a.provedor}: {' '.join(resto)}")
        data = omnivoice_tts.validate_manifest(a.manifest)
        _checar(a.provedor, config)
        if a.check:
            print(f"Manifesto válido: {len(data['segments'])} segmentos | provedor: {a.provedor}")
            return
        if not a.overwrite and not a.retomar and any(Path(s["output"]).exists() for s in data["segments"]):
            p.error("WAV já existe. Use --retomar para gerar só o que falta, --overwrite para refazer "
                    "tudo, ou um manifesto de outra versão")
        if a.provedor == "openai":
            sintetizar_openai(data, config, retomar=a.retomar)
        else:
            sintetizar_comando(data, config, retomar=a.retomar)
        print("Todos os WAVs foram gerados e verificados")
    except (ErroVoz, ValueError, FileNotFoundError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()
