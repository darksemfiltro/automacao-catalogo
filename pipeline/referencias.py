"""Contrato para converter observações de referências em tokens do motor."""
import json
import re
from pathlib import Path

from constraints import value as limite

COLORS = {"title_color", "callout_color", "list_color", "frase_color"}
SIZES = {"title_size", "callout_size", "list_size", "frase_size"}
MIN_PX = limite("referencias.tamanho_min_px", 24)
MAX_PX = limite("referencias.tamanho_max_px", 160)


def validate_tokens(tokens):
    for key, value in tokens.items():
        if key in COLORS:
            if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"Cor inválida: {key}")
        elif key in SIZES:
            if not isinstance(value, (int, float)) or not MIN_PX <= value <= MAX_PX:
                raise ValueError(f"Tamanho fora de {MIN_PX}–{MAX_PX}px: {key}")
        else:
            raise ValueError(f"Token não suportado: {key}")
    return tokens


def load_references(folder):
    folder = Path(folder).resolve()
    manifest = folder / "manifest.json"
    if not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Versão de referências desconhecida")
    for item in data.get("references", []):
        source = (folder / item["file"]).resolve()
        if not source.is_relative_to(folder) or not source.is_file():
            raise ValueError("Referência ausente ou fora da pasta")
        if not all(item.get(key) for key in ("source", "license", "observations")):
            raise ValueError("Referência precisa de origem, licença e observações")
    return validate_tokens(data.get("tokens", {}))
