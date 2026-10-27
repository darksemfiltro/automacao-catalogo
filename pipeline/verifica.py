# -*- coding: utf-8 -*-
"""
verifica.py — roda as verificações do projeto na sua máquina, em ordem.

Rode antes de abrir um pull request ou de renderizar um episódio. O projeto não
usa integração contínua: este script é a única fonte das etapas.

Etapas:
  barra        valida CONSTRAINTS.md
  vendor       confere o sha256 de cada dependência fixada
  testes       a suíte do motor
  fixture      gera uma composição sem áudio e mede a densidade
  composicao   `hyperframes check` de verdade (Gate 3)
  diff         floor_guard sobre o diff do git

Etapas que dependem de Node são puladas com aviso explícito, nunca
silenciosamente: sem `npx` no PATH, quem verifica precisa saber que o Gate 3
não foi exercido.

Uso:
  python pipeline/verifica.py
  python pipeline/verifica.py --etapas barra vendor testes
  python pipeline/verifica.py --sem diff
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
FIXTURE_EPISODE = "episodios/EP05-tipos-de-tempestade/producao/episode.json"
ETAPAS = ("barra", "vendor", "testes", "fixture", "composicao", "diff")


def rodar(comando, **kwargs):
    return subprocess.run(comando, cwd=ROOT, check=True, **kwargs)


def etapa_barra():
    rodar([sys.executable, str(PIPELINE / "constraints.py"), "--list"])


def etapa_vendor():
    rodar([sys.executable, str(PIPELINE / "vendor.py")])


def etapa_testes():
    rodar([sys.executable, "-m", "unittest", "discover", "-s", "pipeline", "-p", "test_*.py"])


def etapa_fixture():
    with TemporaryDirectory() as pasta:
        projeto = Path(pasta)
        origem = ROOT / FIXTURE_EPISODE
        if not origem.is_file():
            raise SystemExit(f"FALHA: {FIXTURE_EPISODE} ausente; a etapa depende dele")
        shutil.copyfile(origem, projeto / "episode.json")
        rodar([sys.executable, str(PIPELINE / "gen_comp.py"), str(projeto), "--spec", "episode.json"])
        rodar([sys.executable, str(PIPELINE / "checa_densidade.py"),
               str(projeto / "hyperframes" / "index.html")])


def etapa_composicao():
    npx = shutil.which("npx")
    if not npx:
        print("  PULADO: npx ausente no PATH; o Gate 3 precisa de Node 22+ e npm ci", file=sys.stderr)
        return "pulado"
    with TemporaryDirectory() as pasta:
        projeto = Path(pasta)
        shutil.copyfile(ROOT / FIXTURE_EPISODE, projeto / "episode.json")
        rodar([sys.executable, str(PIPELINE / "gen_comp.py"), str(projeto), "--spec", "episode.json"])
        rodar([npx, "--no-install", "hyperframes@0.8.144", "check", str(projeto / "hyperframes"),
               "--at", "5,15,25", "--timeout", "60000"])
    return "ok"


def etapa_diff():
    if not (ROOT / ".git").is_dir():
        print("  PULADO: não é um repositório git", file=sys.stderr)
        return "pulado"
    return_code = subprocess.run(
        [sys.executable, str(PIPELINE / "floor_guard.py"), "--base", "HEAD"],
        cwd=ROOT).returncode
    if return_code == 1:
        raise SystemExit("floor_guard achou a barra afrouxada no diff")
    if return_code == 2:
        print("  PULADO: git sem base de comparação", file=sys.stderr)
        return "pulado"


EXECUTAR = {"barra": etapa_barra, "vendor": etapa_vendor, "testes": etapa_testes,
            "fixture": etapa_fixture, "composicao": etapa_composicao, "diff": etapa_diff}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etapas", nargs="+", choices=ETAPAS, default=list(ETAPAS))
    ap.add_argument("--sem", nargs="+", choices=ETAPAS, default=[])
    a = ap.parse_args()
    escolhidas = [e for e in a.etapas if e not in a.sem]
    relatorio = []
    for nome in escolhidas:
        print(f"\n=== {nome} ===", flush=True)
        try:
            resultado = EXECUTAR[nome]() or "ok"
        except subprocess.CalledProcessError as erro:
            print(f"FALHA: {nome} saiu com {erro.returncode}", file=sys.stderr)
            raise SystemExit(1)
        relatorio.append((nome, resultado))
    print("\n=== resumo ===")
    for nome, resultado in relatorio:
        print(f"  {nome:12s} {resultado}")
    if any(r == "pulado" for _, r in relatorio):
        print("\netapa pulada é etapa não exercida; o veredicto acima não a inclui", file=sys.stderr)
    print(f"verifica: {len(relatorio)} etapa(s), "
          f"{sum(1 for _, r in relatorio if r == 'ok')} executada(s) sem erro")


if __name__ == "__main__":
    main()
