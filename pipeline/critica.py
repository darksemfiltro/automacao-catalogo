# -*- coding: utf-8 -*-
"""
critica.py — registra a crítica de direção em contexto fresco.

O `gauntlet.py` tem regra, não gosto: reprova overlap, objeto invisível, texto
sobre objeto e tela parada. Nenhum número accuse uma direção monótona, uma
contraste que não sustenta a fala, ou um plano que cumpre o formato sem contar
nada. Para isso existe esta etapa — e ela é uma pergunta para o revisor, não
um verificador.

O que muda em relação ao `storyboard.py review`:

  - **Contexto fresco.** O revisor relê `plano_cenas.json` e o contrato
    (BIBLIA-CANAL, ESTILO-VISUAL, CENAS-NIVEL-1) sem o raciocínio de quem
    montou o plano, e com instrução adversarial: achar o que está errado, não
    validar.
  - **Não é aprovação.** O registro carrega `human_approval: false`. A aprovação
    continua sendo `storyboard.py review`, com responsável, observações e
    quadros. Criticar não substitui revisar; uma não cura a outra.
  - **Amarrado por hash.** O registro vale para o plano, o spec e o contrato que
    foram lidos. Editar qualquer um deles invalida a crítica, como invalida a
    revisão.

Por padrão a crítica é recomendada e registrada: `direcao.critica_obrigatoria`
em CONSTRAINTS.md decide se ela bloqueia o final.

Uso:
  python pipeline/critica.py <proj> review --critic "quem leu" --notas "..." \
      --achados "..." --verdict go
  python pipeline/critica.py <proj> validate
  python pipeline/critica.py <proj> brief          # imprime o prompt adversarial
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from constraints import value as limite
from workflow import ROOT, digest, read, write

CONTRATO = ("BIBLIA-CANAL.md", "sistema/ESTILO-VISUAL.md", "sistema/CENAS-NIVEL-1.md")
VERDICTS = ("go", "go-com-ressalvas", "no-go")
BRIEF = """\
Revisão adversarial. Encontre o que está errado neste plano de cenas.

Assuma que quem montou o plano está confiante demais. Procure:
- trechos em que a imagem não sustenta o que está sendo dito
- contraste ilegível, objeto que some no fundo escuro, texto sobre objeto
- direção repetitiva: a mesma ideia visual voltando sem mudança de informação
- cena que existe só para preencher tempo, sem informação
- alternância quebrada entre objeto e detalhe, e entre painel e número
- dado numérico sem unidade legível na tela
- silêncio tratado como problema, quando a pausa é expressiva

Não valide, não resuma. Aponte problemas, ou diga explicitamente que não
achou nenhum depois de examinar com cuidado.

PLANO: leia o arquivo indicado em `plano`.
CONTRATO: leia os documentos de contrato indicados em `contrato`.
"""

ARQUIVO = "critica.json"


def _projeto(project) -> Path:
    return Path(project).resolve()


def _hashes(projeto: Path) -> dict:
    itens = {}
    for nome in ("plano_cenas.json", "episode.json"):
        if (projeto / nome).is_file():
            itens[f"artefato/{nome}"] = digest(projeto / nome)
    for nome in CONTRATO:
        caminho = ROOT / nome
        if caminho.is_file():
            itens[f"contrato/{nome}"] = digest(caminho)
    return itens


def _exige(arquivo: dict) -> None:
    for campo in ("critic", "notas", "achados", "verdict"):
        if not str(arquivo.get(campo, "")).strip():
            raise ValueError(f"Crítica precisa de {campo}; crítica sem achado escrito é teatro")
    if arquivo["verdict"] not in VERDICTS:
        raise ValueError(f"Veredito deve ser um de {', '.join(VERDICTS)}")


def registrar(projeto, critic, notas, achados, verdict, contexto="contexto-fresco"):
    projeto = _projeto(projeto)
    if not (projeto / "plano_cenas.json").is_file():
        raise ValueError("plano_cenas.json ausente; rode build_cenas.py antes de criticar")
    if not critic.strip():
        raise ValueError("Informe quem fez a crítica")
    hashes = _hashes(projeto)
    if len(hashes) < 2:
        raise ValueError("Nada a criticar: faltam plano ou contrato")
    registro = {"schema_version": 1, "critic": critic, "contexto": contexto,
                "notas": notas, "achados": achados, "verdict": verdict,
                "human_approval": False,
                "aviso": "Isto não é aprovação humana; a aprovação continua em review.json",
                "inputs": hashes}
    _exige(registro)
    write(projeto / ARQUIVO, registro)
    return registro


def validar(projeto):
    projeto = _projeto(projeto)
    caminho = projeto / ARQUIVO
    if not caminho.is_file():
        raise ValueError(f"{ARQUIVO} ausente: a crítica de direção não foi registrada")
    registro = read(caminho)
    _exige(registro)
    if registro.get("inputs") != _hashes(projeto):
        raise ValueError("Crítica desatualizada: plano, spec ou contrato mudaram; critique de novo")
    return registro


def obrigatoria() -> bool:
    return bool(limite("direcao.critica_obrigatoria", False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    sub = ap.add_subparsers(dest="action", required=True)
    r = sub.add_parser("review")
    r.add_argument("--critic", required=True)
    r.add_argument("--notas", required=True)
    r.add_argument("--achados", required=True)
    r.add_argument("--verdict", choices=VERDICTS, required=True)
    r.add_argument("--contexto", default="contexto-fresco")
    sub.add_parser("validate")
    sub.add_parser("brief")
    a = ap.parse_args()
    if a.action == "brief":
        print(BRIEF)
        print("contrato: " + ", ".join(CONTRATO))
        return
    try:
        if a.action == "review":
            registro = registrar(a.project, a.critic, a.notas, a.achados, a.verdict, a.contexto)
            print(f"crítica registrada: {registro['verdict']} por {registro['critic']} "
                  f"(human_approval: false)")
        else:
            registro = validar(a.project)
            print(f"crítica válida: {registro['verdict']} | achado: {registro['achados'][:80]}")
    except (ValueError, OSError) as exc:
        print(f"FALHA: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()