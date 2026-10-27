# -*- coding: utf-8 -*-
"""
build_cenas.py — motor de cenas do Catálogo.

Transforma (segmentos + timing + alinhamento por palavra + plano visual) em
`episode.json`: a lista de elementos com tempo absoluto, pronta para o gen_comp.

Princípio visual: capítulo = tema, com título breve na entrada; dentro dele,
a cada ~2-3 s entra algo (ilustração, callout de número,
foto, lista) SEMPRE ancorado na palavra falada — nada de offset fixo.

O plano visual (`cenas.json`) é opcional. Sem ele, o motor AUTOGERA:
  - a ilustração do capítulo (`chapters.<id>.ilustra`);
  - um callout para cada número dito (75%, 2.500 K, 5,5 toneladas...);
  - uma `frase` com a palavra-chave quando o trecho não tem número;
  - a lista quando o roteiro enumera ("primeiro", "segundo", "1.").

Uso:
  python pipeline/build_cenas.py <proj> --timing timing_v1.json --align alignment_v1.json \
      --segments segments_v1.json [--cenas cenas.json] --out episode.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import unicodedata

import ilustras
import mg
import tempo
from constraints import value as limite

# ---------------------------------------------------------------- posições

POS = {
    "centro":       (960, 560, 820),
    "centro_alto":  (960, 470, 760),
    "centro_baixo": (960, 650, 720),
    "esquerda":     (480, 560, 700),
    "direita":      (1440, 560, 700),
    "canto_bd":     (1500, 800, 520),
}

CALLOUT_POS = {
    "baixo":  (960, 880),
    "acima":  (960, 600),
    "esq":    (470, 760),
    "dir":    (1450, 760),
    "centro": (960, 560),
    "topo":   (960, 220),
}

# unidade falada (mantém a UNIDADE junto do número — km/h, graus, hectares, %…)
_UNIT = (r"(?:%|por cento|km/h|quil[oô]metr(?:o|os)?\s+por\s+hora|km\s+por\s+hora|"
         r"quil[oô]metros?|km/s|km|metros?|hectares?|graus?|°c|kelvin|k|"
         r"milh(?:ão|ões)?|mil|bilh(?:ão|ões)?|trilh(?:ão|ões)?|toneladas?|"
         r"vezes|anos|minutos?|segundos?|horas?|semanas?|dias?|massas?\s+solares?)")
NUMBER_RE = re.compile(rf"\d[\d.]*(?:,\d+)?\s*(?:{_UNIT})?", re.IGNORECASE)

ORDINALS = ["primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto",
            "sétimo", "oitavo", "nono", "décimo"]

# tipos de motion graphic (tela de dados: gráfico, medidor, barra, comparação)
GRAPHIC = {"grafico", "barra", "medidor", "comparacao"}
_OPENERS = ("ilustra", "imagens") + tuple(GRAPHIC)

# Palavra FALADA -> objeto ilustrado. É o que dá relevância semântica e permite
# ancorar cada objeto na palavra exata (chaves em forma `plain`, sem acento).
WORD_PROP: dict[str, str] = {}


def _wp(prop, *words):
    for w in words:
        WORD_PROP[w] = prop


_wp("thermometer", "temperatura", "temperaturas", "kelvin", "graus", "termometro", "mede")
_wp("snowflake", "frio", "fria", "frios", "frias", "gelo", "neve", "congela", "congelar",
    "esfria", "inverno", "floco", "flocos")
_wp("iceberg", "iceberg", "glacial", "glaciacao", "geleira")
_wp("flame", "calor", "quente", "quentes", "fogo", "chama", "queima", "queimam", "queimar",
    "incandescente", "brasa", "aquece", "esquenta", "aquecido")
_wp("water", "agua", "liquido", "chuva", "vapor", "hidrico")
_wp("lightning", "energia", "raio", "relampago", "eletricidade", "descarga", "eletrico")
_wp("cloud", "nuvem", "nuvens", "atmosfera", "gas", "gases", "poeira")
_wp("storm", "tempestade", "tempestades", "tormenta", "vento", "furacao", "vendaval")
_wp("mountain", "montanha", "montanhas", "monte", "colossal")
_wp("magnet", "magnetismo", "magnetico", "campo", "ima")
_wp("battery", "bateria", "carga", "acumula")
_wp("comet", "cometa", "cometas", "cauda", "viajante")
_wp("meteor", "meteoro", "meteoros", "asteroide", "asteroides", "rocha", "rochas", "pedra")
_wp("planet_rings", "aneis", "anel", "saturno", "orbita", "orbitas")
_wp("volcano", "vulcao", "vulcoes", "erupcao", "erupcoes", "lava", "magma")
_wp("tree", "vida", "arvore", "floresta", "nascer", "nasceu", "biologico", "vivendo")
_wp("brain", "ideia", "cerebro", "pensa", "inteligencia", "mente", "raciocinio", "conhecimento")
_wp("magnifier", "pesquisa", "estudo", "estudar", "estudada", "estudadas", "investiga",
    "analisa", "examinar")
_wp("eye", "observar", "observa", "enxerga", "vista", "olho", "olhos")
_wp("eye", "visibilidade", "visivel", "invisivel")
_wp("gear", "funciona", "funcionam", "mecanismo", "processo", "sistema", "motor")
_wp("crown", "rei", "recorde", "lider", "maximo", "maxima", "supremo", "gigantesco")
_wp("arrow_up", "aumenta", "aumentar", "aumentaria", "cresce", "crescimento", "sobe",
    "expande", "expandir", "subiu")
_wp("arrow_down", "diminui", "diminuir", "cai", "caiu", "reduz", "reduzir", "desce")
_wp("sun", "sol")
_wp("question", "pergunta", "duvida", "misterio", "enigma", "desconhecido", "misteriosa")
_wp("hourglass", "tempo", "anos", "bilhao", "bilhoes", "trilhao", "trilhoes", "milhao",
    "milhoes", "dura", "duram", "durar", "envelhecer", "idade", "antigo", "antiga", "antigas")
_wp("scale", "massa", "massas", "densidade", "densa", "peso", "pesaria", "pesa", "tonelada",
    "toneladas", "balanca", "macica", "pesada", "pesado")
_wp("hydrogen", "hidrogenio", "combustivel", "combustao", "fusao", "funde", "fundir",
    "helio", "deuterio", "litio", "queimando")
_wp("atom", "nucleo", "atomo", "atomos", "protons", "eletrons", "quarks", "neutron",
    "particula", "particulas")
_wp("galaxy", "universo", "galaxia", "galaxias", "galactico", "halo", "cosmos", "cosmico")
_wp("nebula", "nebulosa", "nebulosas", "morrer", "morre", "mortas", "apagando", "apaga", "morte")
_wp("supernova", "supernova", "supernovas", "explosao", "explosoes", "explode", "violentas",
    "violenta", "detona", "detonacao")
_wp("earth", "terra", "terrestre", "mundo")
_wp("gas_giant", "planeta", "planetas", "gasoso", "jupiter")
_wp("prism", "prisma", "espectro", "espalha", "cores", "comprimentos", "decompoe")
_wp("spoon", "colher", "colherada", "colherzinha")
_wp("telescope", "telescopio", "astrofisica", "observatorio", "observacao")
_wp("lightbulb", "brilho", "brilhante", "brilhantes", "luminosa", "luminosas", "luminosidade",
    "luz", "claridade", "ilumina", "radiante")
_wp("tape", "tamanho", "diametro", "raio", "estica", "vezes", "medida", "comprimento", "inchar")
_wp("rocket", "foguete", "espacial", "lancamento", "transfer")
_wp("moon", "lua")
_wp("black_hole", "buraco")
# adjetivos, verbos e cores (cobrir as partes principais da narrativa)
_wp("atom", "elementos", "elemento", "metal", "metais", "pesados", "pesado", "pesada")
_wp("cloud", "camadas", "camada", "externa", "externas", "opaca", "opacas", "opaco")
_wp("arrow_down", "fraca", "fraco", "fracas", "fracos", "diminuta", "diminuto", "reduzida")
_wp("battery", "forte", "fortes", "potente", "poderosa", "poderoso", "intensa", "intenso")
_wp("mountain", "gigante", "gigantes", "enorme", "enormes", "imensa", "imenso", "colossal")
_wp("eye", "parece", "parecem", "parecer", "aparenta", "aparentam")
_wp("gear", "gira", "giram", "rotacao", "rotaciona", "rotacionam", "motor")
_wp("comet", "rapida", "rapido", "veloz", "velozes", "rapidamente")
_wp("tree", "viva", "vivo", "vivas", "vivos", "nasce", "nascem", "cresce", "crescem")
_wp("lightbulb", "clara", "claro", "iluminada", "iluminado", "brilha", "brilham")
_wp("planet_rings", "orbitam", "orbitando", "orbitar")
_wp("red_giant", "vermelho", "vermelha", "vermelhos", "vermelhas")
_wp("blue_giant", "azul", "azuis")
_wp("yellow_dwarf", "amarelo", "amarela", "amarelos", "amarelas")
_wp("white_dwarf", "branco", "branca", "brancos", "brancas")
_wp("orange_dwarf", "laranja", "laranjas")
_wp("brown_dwarf", "marrom", "marrons")
_wp("supernova", "moribunda", "moribundo", "agoniza", "agonizante")

# ---- generalização: desastres naturais -------------------------------------
_wp("tornado", "tornado", "tornados", "funil", "vendaval", "redemoinho")
_wp("hurricane", "furacao", "furacoes", "ciclone", "ciclones", "tufao", "moncao")
_wp("earthquake", "terremoto", "terremotos", "sismo", "sismos", "tremor", "tremores",
    "falha", "tectonica", "placas")
_wp("tsunami", "tsunami", "tsunamis", "maremoto", "ondas", "onda")
_wp("wildfire", "incendio", "incendios", "queimada", "queimadas", "fumaca", "chamas")
_wp("flood", "enchente", "enchentes", "inundacao", "inundacoes", "alagamento", "transborda")
_wp("drought", "seca", "secas", "estiagem", "aridez", "deserto", "estiagem")
_wp("blizzard", "nevasca", "nevascas", "nevasca", "geada", "congelamento")
_wp("volcano", "vulcao", "vulcoes", "vulcanica", "vulcanico", "erupcao", "erupcoes",
    "lava", "magma", "cinzas", "cratera")
# ---- energia ---------------------------------------------------------------
_wp("nuclear_plant", "nuclear", "uranio", "reator", "reacao", "fissao", "fusao nuclear")
_wp("dam", "hidreletrica", "barragem", "represa", "turbina hidraulica", "reservatorio")
_wp("solar_panel", "solar", "fotovoltaica", "fotovoltaico", "painel", "paineis")
_wp("wind_turbine", "eolica", "eolico", "catavento", "aero", "aerogerador")
_wp("coal_plant", "carvao", "termoeletrica", "termica", "chamine", "poluicao")
_wp("geothermal", "geotermica", "geotermico", "geiser", "vapor")
_wp("power_grid", "rede", "transmissao", "distribuicao", "torre", "linhas")
# ---- biomas / natureza -----------------------------------------------------
_wp("amazon", "amazonia", "floresta", "selva", "umida", "dossel")
_wp("cerrado", "cerrado", "savana", "arvores tortas")
_wp("caatinga", "caatinga", "sertao", "mandacaru", "seco")
_wp("pantanal", "pantanal", "alagado", "alagavel")
_wp("mangrove", "mangue", "manguezal", "estuario")
_wp("pampa", "pampa", "campo", "graminea")
# ---- vida / ciência --------------------------------------------------------
_wp("dna", "dna", "genetico", "gene", "genes", "hereditariedade", "codigo")
_wp("virus", "virus", "viral", "pandemia", "epidemia", "infecta")
_wp("cell", "celula", "celulas", "membrana", "citoplasma")
_wp("heart", "coracao", "cardiaca", "pulsa", "batimento")
_wp("leaf", "folha", "folhas", "fotossintese", "clorofila")
_wp("microscope", "microscopio", "microscopicos", "lente")
# ---- mundo / tecnologia ----------------------------------------------------
_wp("satellite", "satelite", "satelites", "orbita baixa")
_wp("plane", "aviao", "avioes", "aeronave", "voo")
_wp("ship", "navio", "navios", "barco", "cargueiro", "porto")
_wp("factory", "fabrica", "industria", "industrial", "producao")
_wp("city", "cidade", "cidades", "urbano", "metropole", "capital")
_wp("house", "casa", "casas", "moradia", "residencia")
_wp("car", "carro", "carros", "veiculo", "automovel", "transporte")


# ---- MOTION GRAPHICS: palavra/conceito -> cena animada de TELA CHEIA --------
# (substitui o objeto cartoon; a cena cobre o quadro e dá movimento constante)
MG_SCENE_BY_WORD = {
    "tornado": "vortex", "funil": "vortex", "redemoinho": "vortex", "vendaval": "vortex",
    "furacao": "spiral_storm", "ciclone": "spiral_storm", "tufao": "spiral_storm",
    "moncao": "spiral_storm",
    "terremoto": "seismic", "sismo": "seismic", "tremor": "seismic", "placas": "seismic",
    "falha": "seismic", "tectonica": "seismic",
    "tsunami": "wave_stack", "maremoto": "wave_stack", "ondas": "wave_stack", "onda": "wave_stack",
    "incendio": "wildfire", "queimada": "wildfire", "fogo": "wildfire", "chamas": "wildfire",
    "enchente": "water_rise", "inundacao": "water_rise", "alagamento": "water_rise",
    "chuva": "water_rise", "transborda": "water_rise",
    "seca": "drought", "estiagem": "drought", "seco": "drought", "aridez": "drought",
    "nevasca": "snowstorm", "neve": "snowstorm", "geada": "snowstorm",
    "congelamento": "snowstorm",
    "vulcao": "volcano", "erupcao": "volcano", "lava": "volcano", "magma": "volcano",
    "cratera": "volcano", "cinzas": "volcano",
    "vento": "wind_field", "ventos": "wind_field", "rajada": "wind_field",
    "mar": "ocean_depth", "oceano": "ocean_depth", "fundodomar": "ocean_depth",
    "globo": "globe_grid", "terra": "globe_grid", "mundo": "globe_grid",
    "universo": "star_warp", "galaxia": "star_warp", "estrela": "star_warp",
}
MG_TOPIC_SCENE = {"nature": "wind_field", "energy": "wind_field", "biome": "wind_field",
                  "life": "wind_field", "astro": "star_warp", "general": "wind_field"}

# A cena de fundo é uma textura de movimento. O objeto na frente é escolhido
# pela fala; não existe uma sequência fixa por ID de capítulo ou por episódio.
SCENE_PROP = {
    "vortex": "tornado", "spiral_storm": "hurricane", "seismic": "earthquake",
    "wave_stack": "tsunami", "wildfire": "wildfire", "water_rise": "flood",
    "drought": "drought", "snowstorm": "blizzard", "volcano": "volcano",
    "wind_field": "storm", "ocean_depth": "water", "star_warp": "star_generic",
    "star_glow": "star_generic", "globe_grid": "earth",
}
SCENE_SUPPORT = {
    "vortex": "cloud", "spiral_storm": "storm", "seismic": "mountain",
    "wave_stack": "water", "wildfire": "flame", "water_rise": "cloud",
    "drought": "sun", "snowstorm": "snowflake", "volcano": "flame",
    "wind_field": "cloud", "ocean_depth": "question", "star_warp": "telescope",
    "star_glow": "lightbulb",
}

ACTION_WORDS = {
    "destruir", "destruiu", "destroi", "destroem", "destruindo", "devastar",
    "devasta", "devastador", "derrubar", "derruba", "derrubam", "desabar",
    "desaba", "arrasar", "arrasa", "demolir", "demole", "colapsa",
}

# legenda curta e legível que acompanha cada cena (evita frase-sopa de palavras)
MG_SCENE_LABEL = {
    "vortex": "AR EM ROTAÇÃO VIOLENTA", "spiral_storm": "TEMPESTADE GIGANTE",
    "seismic": "PLACAS TECTÔNICAS", "wave_stack": "ONDAS GIGANTES",
    "wildfire": "O FOGO SE ESPALHA", "water_rise": "A ÁGUA SOBE",
    "drought": "SEM CHUVA POR MUITO TEMPO", "snowstorm": "NEVE E VENTO FORTE",
    "volcano": "MAGMA SOB PRESSÃO", "wind_field": "VENTO EM ALTA VELOCIDADE",
    "ocean_depth": "FUNDO DO MAR", "globe_grid": "AS FORÇAS DA NATUREZA",
    "star_warp": "O UNIVERSO EM MOVIMENTO",
}

# unidade falada -> (widget, unidade de exibição, máximo típico)
WIDGET_UNITS = [
    (r"km/h|km por hora|quil[oô]metr(?:o|os) por hora|por hora", "speed_gauge", "km/h", 400),
    (r"escala|magnitude|richter", "magnitude_scale", "", 10),
    (r"graus|°c|kelvin|\bkelvin\b", "thermometer", "graus", 1500),
    (r"hectares?", "area_counter", "hectares", 8000),
    (r"quil[oô]metros|km\b", "distance_ruler", "km", 0),
    (r"minutos?|segundos?|horas?|semanas?|dias?", "duration_bar", "", 0),
    (r"%|por cento", "pct_ring", "%", 100),
]


def word_prop(word: str) -> str | None:
    p = plain(word)
    if p in WORD_PROP:
        return WORD_PROP[p]
    # generalização: plural/singular ("ventos"->"vento", "chuvas"->"chuva")
    if p.endswith("s") and p[:-1] in WORD_PROP:
        return WORD_PROP[p[:-1]]
    if not p.endswith("s") and (p + "s") in WORD_PROP:
        return WORD_PROP[p + "s"]
    return None


# expressões compostas: o termo inteiro vale mais que as palavras soltas
# (ex.: "gigantes azuis" -> blue_giant, e NÃO "gigante"->montanha)
STAR_PATTERNS = [
    (r"an[ãa]s?\s+vermelh", "red_dwarf"), (r"an[ãa]s?\s+laranj", "orange_dwarf"),
    (r"an[ãa]s?\s+amarel", "yellow_dwarf"), (r"an[ãa]s?\s+branc", "white_dwarf"),
    (r"an[ãa]s?\s+azul", "blue_dwarf"), (r"an[ãa]s?\s+marrom", "brown_dwarf"),
    (r"sub[ãa]n[ãa]", "subdwarf"),
    (r"supergigantes?\s+azuis?", "blue_supergiant"),
    (r"supergigantes?\s+vermelh", "red_supergiant"),
    (r"gigantes?\s+azuis?", "blue_giant"), (r"gigantes?\s+vermelh", "red_giant"),
    (r"estrela\s+de\s+n[eê]utrons", "neutron_star"), (r"buraco\s+negro", "black_hole"),
    (r"wolf[\s-]rayet", "blue_supergiant"),
    (r"via\s+l[áa]ctea", "galaxy"),
]

# palavras cujo objeto é fraco/ambíguo (só entram se não houver opção melhor)
WEAKWORD = {"funciona", "funcionam", "processo", "sistema", "motor", "aumenta", "aumentar",
            "aumentaria", "cresce", "diminui", "diminuir", "cai", "reduz", "parece", "parecem",
            "muda", "vira", "viram", "deixa", "gigante", "gigantes", "enorme", "enormes",
            "elementos", "elemento", "camadas", "camada", "opaca", "opacas", "fraca", "fraco",
            "forte", "fortes", "causa", "causam", "coisa", "coisas", "campo",
            "gira", "giram", "rapido", "rapida", "velocidade", "movimento",
            "pesado", "pesada", "pesados", "pesadas"}


def topic_of(ch_id, label):
    """Domínio do capítulo — guia a escolha do objeto (astro, natureza, energia...)."""
    s = slug(f"{ch_id} {label or ''}").replace("-", " ")
    if re.search(r"\b(?:ana|anas|subana|subanas)\b", s) or any(
            k in s for k in ("gigante", "estrela", "astro", "universo", "wolf", "rayet",
                             "neutron", "pulsar")):
        return "astro"
    if any(k in s for k in ("furac", "desastr", "natural", "clima", "catastrof",
                          "tornado", "terremoto", "tsunami", "incendio", "enchente",
                          "seca", "nevasca", "vulcao", "erupcao")):
        return "nature"
    if any(k in s for k in ("usina", "energ", "eletric", "reator", "bateria")):
        return "energy"
    if any(k in s for k in ("bioma", "floresta", "amazon", "cerrado", "caatinga", "pantanal")):
        return "biome"
    if any(k in s for k in ("vida", "célula", "celula", "ciência", "ciencia", "biolog")):
        return "life"
    return "general"


def rank_objects(text, pairs, topic, bg_white):
    """Ranqueia objetos por contexto: expressão composta + categoria + fundo."""
    low = text.lower()
    cand: dict[str, list] = {}
    for rx, obj in STAR_PATTERNS:
        if re.search(rx, low):
            cand[obj] = [6 + (3 if topic == "astro" else 0), None]
    for w, t in pairs:
        obj = word_prop(w)
        if not obj:
            continue
        cat = ilustras.category(obj)
        sc = 1
        if cat == topic:
            sc += 3
        elif topic not in ("general", "concept") and cat not in ("concept", topic):
            sc -= 2                       # objeto fora do tema (ex.: montanha em cap. de estrela)
        if plain(w) in WEAKWORD:
            sc -= 2
        if bg_white and ilustras.needs_dark(obj):
            sc -= 3                       # some no fundo branco
        if obj in cand:
            cand[obj][0] += sc
            if cand[obj][1] is None:
                cand[obj][1] = t
        else:
            cand[obj] = [sc, t]
    out = [(sc, (t if t is not None else 0.0), obj) for obj, (sc, t) in cand.items() if sc > 0]
    out.sort(key=lambda x: (-x[0], x[1]))
    return out


def seg_word_list(align, sid):
    """Palavras editoriais do segmento com o tempo falado: [(palavra, t), ...]."""
    seg = align.by_id.get(sid) or {}
    ws = seg.get("editorial_words") or seg.get("words") or []
    return [(w["w"], float(w["t"])) for w in ws if w.get("t") is not None]


# palavras longas que NÃO rendem bom destaque (advérbios/conectivos)
WEAK = {"relativamente", "aproximadamente", "principalmente", "praticamente", "basicamente",
        "justamente", "anteriormente", "geralmente", "realmente", "possivelmente",
        "provavelmente", "especialmente", "atualmente", "simplesmente", "normalmente",
        "teoricamente", "cientificamente", "completamente", "diretamente", "exatamente",
        "certamente", "finalmente", "inclusive", "conseguem", "consegue", "conseguiria"}


def salient_word(pairs, used, min_t=None, max_t=None):
    """Palavra mais 'forte' do segmento para virar destaque na tela."""
    best = None
    for w, t in pairs:
        p = plain(w)
        if len(p) < 5 or p in STOP or p in used or p.isdigit() or p in WEAK:
            continue
        if min_t is not None and t < min_t:
            continue
        if max_t is not None and t > max_t:
            continue
        if best is None or len(p) > len(plain(best)):
            best = w
    return best

STOP = set("a o e de do da que em um uma para com os as no na se por sao é eu você voce "
           "mais ja não nao como isso ele ela mas ou ao dos das nem so vai vou tem ter foi "
           "ser sua seu me te lhe aqui ali la então entao tambem muito muita pouco sobre "
           "entre sem ate cada todo toda todos todas pelo pela qual quais quando onde quem "
           "muito bem tudo isso isto aquilo".split())


def plain(word: str) -> str:
    w = unicodedata.normalize("NFD", str(word).lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def slug(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# ---------------------------------------------------------------- alinhamento

class Align:
    def __init__(self, align_obj, text_by_id=None):
        self.by_id = {s["id"]: s for s in align_obj["segments"]}
        # Reconstrói o mapa editorial -> falado a partir dos tempos por palavra.
        # Sem isto, números expandidos ("2500" -> "dois mil e quinhentos") colapsam
        # o tempo e os callouts entram segundos fora de sincronia.
        if text_by_id:
            for sid, seg in self.by_id.items():
                original = text_by_id.get(sid)
                if original and seg.get("words"):
                    seg["editorial_words"] = tempo.recompute_editorial(seg, original)

    def word_time(self, sid, word, seg_start, seg_end):
        """Tempo da palavra falada no segmento (editorial primeiro). Por fração se faltar."""
        seg = self.by_id.get(sid)
        target = plain(word)
        if seg:
            for key in ("editorial_words", "words"):
                for w in seg.get(key, []):
                    if plain(w["w"]) == target and target:
                        return max(seg_start, min(float(w["t"]), seg_end))
        return None

    def missing_ratio(self, sid):
        seg = self.by_id.get(sid) or {}
        return 1.0 - float(seg.get("aligned_ratio", 0) or 0)


# ---------------------------------------------------------------- plano visual

def load_plan(path):
    if not path or not os.path.exists(path):
        return {"theme": "cartoon", "chapters": {}, "cenas": {}, "defaults": {}}
    plan = json.load(open(path, encoding="utf-8"))
    plan.setdefault("theme", "cartoon")
    plan.setdefault("chapters", {})
    plan.setdefault("cenas", {})
    plan.setdefault("defaults", {})
    return plan


def chapter_cfg(plan, ch):
    cfg = dict(plan.get("chapters", {}).get(ch["id"], {}))
    cfg.setdefault("titulo", ch["label"].upper())
    cfg.setdefault("fundo", plan.get("defaults", {}).get("fundo", "space"))
    cfg.setdefault("cor", "#29a8ff")
    return cfg


# ---------------------------------------------------------------- autogeração

RANGE_RE = re.compile(
    rf"(\d[\d.]*(?:,\d+)?)\s*({_UNIT})?\s*(?:a|até|e)\s*"
    rf"(\d[\d.]*(?:,\d+)?)\s*({_UNIT})?", re.IGNORECASE)


def find_numbers(text):
    """Extrai números e faixas ('2500 e 3500 Kelvin', '8% e 50%' -> um callout só)."""
    out, consumed = [], []
    for m in RANGE_RE.finditer(text):
        lo, u1, hi, u2 = m.group(1), m.group(2), m.group(3), m.group(4)
        unit = (u2 or u1 or "").strip()
        if unit == "%":
            raw = f"{lo}% a {hi}%"
        else:
            raw = f"{lo} a {hi}" + (f" {unit}" if unit else "")
        out.append({"palavra": re.sub(r"\s+", "", lo), "raw": raw})
        consumed.append((m.start(), m.end()))
    for m in NUMBER_RE.finditer(text):
        if any(a <= m.start() < b for a, b in consumed):
            continue
        raw = m.group(0).strip()
        if not raw or not any(ch.isdigit() for ch in raw):
            continue
        word = re.sub(r"\s+", "", raw.split()[0]) if raw.split() else raw
        out.append({"palavra": word, "raw": raw})
    return out


def find_list(text):
    """Detecta enumeração ('primeiro...', '1. ...') e devolve os itens."""
    items = []
    for i, ordv in enumerate(ORDINALS):
        if re.search(rf"\b{ordv}\b", text, re.IGNORECASE):
            items.append(ordv.capitalize())
    numbered = re.findall(r"(?:^|\s)(\d)[.)]\s*([A-ZÀ-Þ][^.;]{2,60})", text)
    for _, it in numbered:
        items.append(it.strip())
    return items


def key_phrase(text, chapter_label):
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{5,}", text) if plain(w) not in STOP]
    if not words:
        return None
    words.sort(key=len, reverse=True)
    return words[0].upper()


def short_phrase(text, maxn=4):
    """Frase CONTÍGUA de palavras fortes (a mais longa) para a tela só de texto."""
    best, run = [], []
    for w in re.findall(r"[A-Za-zÀ-ÿ]{3,}", text):
        p = plain(w)
        if p in STOP or p in WEAK or len(p) < 4:
            if len(run) > len(best):
                best = run
            run = []
        else:
            run.append(w)
            if len(run) > maxn:
                if len(run) - 1 > len(best):
                    best = run[:-1]
                run = run[1:]
    if len(run) > len(best):
        best = run
    return " ".join(best).upper() if len(best) >= 2 else None


def _anchor_time(el, tmap, seg_start):
    if el.get("at") is not None:
        return float(el["at"])
    p = el.get("palavra")
    if p and plain(p) in tmap:
        return tmap[plain(p)]
    return seg_start


def fill_gaps(els, text, pairs, topic, bg_white, seg_start, seg_end, cfg,
              max_gap=2.4, max_add=8, max_ilus=5):
    """Densifica: garante um NOVO visual a cada ≤ max_gap, ALTERNANDO os lados.
    Faltando objeto, entra TEXTO no lado oposto — nunca em cima do objeto."""
    tmap = {}
    for w, t in pairs:
        tmap.setdefault(plain(w), t)
    if seg_end - seg_start < 1.5:
        return els
    ranked = rank_objects(text, pairs, topic, bg_white)
    for _ in range(max_add):
        ilus = [e for e in els if e.get("tipo") in ("ilustra", "imagens")]
        if len(ilus) >= max_ilus:
            break
        # se os dois lados já estão ocupados, mais um objeto vai sobrepor: para
        sides = {("esq" if str(e.get("pos", "")).startswith("esq") else "dir") for e in ilus}
        if len(sides) >= 2:
            break
        existing = {e.get("id") for e in ilus}
        last_prop = ilus[-1].get("id") if ilus else None
        times = sorted([seg_start] + [_anchor_time(e, tmap, seg_start) for e in els]
                       + [seg_end])
        a, b = max((b - a, a, b) for a, b in zip(times, times[1:]))[1:]
        if b - a <= max_gap:
            break
        # lado do texto (não se põe objeto em cima de texto)
        busy = {"esq" if str(e.get("pos", "")).startswith("esq") else "dir"
                for e in els if e.get("tipo") in ("frase", "callout", "palavra")}
        pos = "centro_alto"
        if ilus:
            p0 = str(ilus[-1].get("pos") or "")
            pos = "direita" if p0.startswith("esq") else "esquerda"
        pside = "esq" if str(pos).startswith("esq") else "dir"
        if pside in busy or pside in sides:   # lado do texto/objeto ocupado -> tenta o outro
            pos = opposite(pos)
            pside = "esq" if pos.startswith("esq") else "dir"
            if pside in busy or pside in sides:
                break
        cand = next(((t, obj) for sc, t, obj in ranked
                     if a + 0.4 <= t <= b - 0.3 and obj not in existing and obj != last_prop),
                    None)
        if cand:
            els.append({"tipo": "ilustra", "id": cand[1], "at": cand[0], "pos": pos, "size": 520})
            continue
        # sem objeto novo: TEXTO no lado oposto ao último objeto (nunca sobre ele)
        ja_tem = any(e.get("tipo") in ("frase", "callout", "palavra")
                     and a - 0.1 <= _anchor_time(e, tmap, seg_start) <= b for e in els)
        if not ja_tem:
            ph = short_phrase(text)
            if ph:
                els.append({"tipo": "frase", "texto": ph, "at": round(a + 0.25, 3),
                            "dur": round(min(2.9, max(1.3, b - a - 0.4)), 3), "pos": pos})
                continue
        break
    return els


# ---------------------------------------------------------------- diretor de cena
#
# O diretor decide o TIPO de cena ANTES de montar os elementos, para o segmento
# nunca virar "um objeto parado": ele escolhe entre tela de dados, lista+objeto,
# cadeia de objetos, dois objetos, objeto+texto ou só texto — sempre LADO A LADO,
# para texto e objeto nunca se sobreporem.

BEAT_S = 2.3          # ritmo: um novo visual a cada ~2,3 s
MAX_BEATS = 6         # teto de objetos por segmento

# objeto genérico por domínio, quando nenhuma palavra do trecho casa com um objeto
FALLBACK = {"nature": "storm", "energy": "lightning", "biome": "leaf", "life": "cell",
            "astro": "star_generic", "general": "question"}


def opposite(pos: str) -> str:
    return "direita" if str(pos).startswith("esq") else "esquerda"


def _percent(n):
    m = re.fullmatch(r"(\d{1,3})\s*%", str(n.get("raw", "")).strip())
    return int(m.group(1)) if m and 1 <= int(m.group(1)) <= 100 else None


def _range(n):
    m = RANGE_RE.search(str(n.get("raw", "")))
    if not m:
        return None
    unit = (m.group(4) or m.group(2) or "").strip()
    return m.group(1).replace(".", ""), m.group(3).replace(".", ""), unit


def _fisica(unit: str) -> bool:
    """Faixa que rende um MEDIDOR (temperatura/massa), não uma mera proporção."""
    u = str(unit).lower()
    return u in ("k", "kelvin", "graus", "°c", "c") or "tonelada" in u or "massa" in u


def scene_of(ranked, nums, itens, dur: float) -> str:
    if nums:
        return "tela_dados"
    if len(itens) >= 3:
        return "lista_objeto"
    n = len(ranked)
    if n >= 3 and dur >= 6.5:
        return "cadeia_objetos"
    if n >= 2 and dur >= 4.0:
        return "dois_objetos"
    if n >= 1:
        return "objeto_texto"
    return "so_texto"


def _tag(els, scene):
    for e in els:
        e["_dir"] = True
        e["_scene"] = scene
    return els


def _side_frase(els, text, pairs, pos):
    """Texto curto no lado oposto ao objeto (frase lateral ou palavra de destaque)."""
    ph = short_phrase(text)
    if ph:
        els.append({"tipo": "frase", "texto": ph, "pos": pos})
        return True
    w = salient_word(pairs, set())
    if w:
        els.append({"tipo": "palavra", "texto": w.upper(), "palavra": w, "pos": pos})
        return True
    return False


def _fmt(v) -> str:
    f = float(v)
    if abs(f - round(f)) < 1e-9:
        return f"{int(round(f)):,}".replace(",", ".")
    return f"{f:.1f}".replace(".", ",")


def _unit_of(raw):
    m = re.search(_UNIT, str(raw or ""), re.IGNORECASE)
    return m.group(0).strip() if m else ""


def _unit_display(u):
    p = plain(u)
    if p in ("kmh", "kmporhora", "quilometrosporhora", "porhora", "quilometroporhora"):
        return "km/h"
    if p in ("graus", "grau", "c", "°c"):
        return "graus"
    if p in ("kelvin", "k"):
        return "K"
    if p.startswith("hectare"):
        return "hectares"
    if p in ("km", "quilometros", "quilometro", "kilometros"):
        return "km"
    if p in ("%", "porcento"):
        return "%"
    return u


def _parse_vals(raw):
    out = []
    for m in re.findall(r"\d[\d.]*(?:,\d+)?", str(raw or "")):
        try:
            out.append(float(m.replace(".", "").replace(",", ".")))
        except ValueError:
            pass
    return out


def build_widget(text, num):
    """Widget de dados (sempre com UNIDADE) a partir do número dito.

    A UNIDADE escrita junto do número manda; só na falta dela usamos o contexto
    da frase (ex.: "a escala vai até 10" -> magnitude).
    """
    raw = str(num.get("raw") or "")
    unit = _unit_of(raw)
    disp = _unit_display(unit)
    p = plain(unit)
    vals = _parse_vals(raw)
    up = max(vals) if vals else 0.0
    lo = min(vals) if vals else 0.0
    low = f"{text} {raw}".lower()

    if p in ("kmh", "kmporhora", "quilometrosporhora", "quilometroporhora", "porhora") \
            or re.search(r"km/h|por hora", raw, re.I):
        return ("speed_gauge", {"valor": up, "max": int(math.ceil(up / 100.0) * 100) or 400,
                                "unidade": "km/h"}, f"VENTOS DE ATÉ {_fmt(up)} KM/H")
    if p.startswith("hectare"):
        return ("area_counter", {"valor": up or 1000},
                f"{_fmt(up)} DE HECTARES" if up else "MILHARES DE HECTARES")
    if p in ("graus", "grau", "c", "°c", "kelvin", "k"):
        mx = int(math.ceil(up / 500.0) * 500) or 1500
        txt = (f"{_fmt(lo)} A {_fmt(up)} GRAUS" if len(vals) >= 2 else f"{_fmt(up)} GRAUS")
        return ("thermometer", {"valor": up, "max": mx, "unidade": "graus"}, txt)
    if p in ("km", "quilometros", "quilometro", "kilometros", "metros", "metro"):
        return ("distance_ruler", {"texto": f"{_fmt(up)} {disp or 'km'}"},
                f"{_fmt(up)} {disp.upper() or 'KM'} DE DIÂMETRO")
    if p in ("minutos", "minuto", "horas", "hora", "semanas", "semana", "dias", "dia",
             "segundos", "segundo", "anos", "ano"):
        return ("duration_bar", {"texto": raw.upper()}, raw.upper())
    if p in ("%", "porcento"):
        txt = f"{_fmt(up)}%" if len(vals) == 1 else f"{_fmt(lo)}% A {_fmt(up)}%"
        return ("pct_ring", {"valor": up}, txt)
    # sem unidade escrita: usa o contexto da frase
    if re.search(r"escala|magnitude|richter", low):
        return ("magnitude_scale", {"valor": up or 10, "max": 10},
                f"MAGNITUDE ATÉ {_fmt(up or 10)}")
    if re.search(r"%|por cento", raw, re.I) and vals:
        return ("pct_ring", {"valor": up}, f"{_fmt(up)}%")
    if re.search(r"hectares?", low):
        return ("area_counter", {"valor": up or 1000},
                f"{_fmt(up)} DE HECTARES" if up else "MILHARES DE HECTARES")
    if re.search(r"quil[oô]metros|di[aâ]metro", low) and vals:
        return ("distance_ruler", {"texto": f"{_fmt(up)} km"},
                f"{_fmt(up)} KM DE DIÂMETRO")
    return None


def chapter_scene(ch_id, label, topic):
    """Receita candidata do capítulo; o planejador decide em quais tomadas usá-la."""
    s = plain(f"{ch_id} {label}")
    for k, r in MG_SCENE_BY_WORD.items():
        if plain(k) and plain(k) in s:
            return r
    return MG_TOPIC_SCENE.get(topic, "globe_grid")


def scene_cut_times(ch, bounds, segs, align):
    """Cortes curtos nas palavras medidas, sem cortar o áudio nem deixar buracos."""
    start, end = bounds
    words = []
    for sid in ch.get("segments", []):
        for w in (align.by_id.get(sid) or {}).get("editorial_words", []):
            t = float(w.get("t", -1))
            if start + 1.7 <= t <= end - 0.8:
                words.append(t)
    words.sort()
    cuts = [start]
    while end - cuts[-1] > 3.5:
        target = cuts[-1] + 2.55
        candidates = [t for t in words if cuts[-1] + 1.8 <= t <= cuts[-1] + 3.2]
        nxt = min(candidates, key=lambda t: abs(t - target)) if candidates else target
        if end - nxt < 1.2:
            break
        cuts.append(round(nxt, 3))
    return cuts


def scene_for_cut(base, ch, align, start, stop):
    """Varia o diagrama somente quando a fala nomeia um fenômeno específico."""
    if base == "star_warp":
        return base
    for sid in ch.get("segments", []):
        for word, t in seg_word_list(align, sid):
            if not start <= t < stop:
                continue
            recipe = MG_SCENE_BY_WORD.get(plain(word))
            if recipe and recipe not in ("globe_grid", "star_warp", "ocean_depth"):
                return recipe
    return base


def semantic_objects(text, pairs, topic, scene, seg_start, seg_end, last_prop=None,
                     densify=True):
    """Escolhe objetos concretos pela fala e pela ação, em ordem temporal.

    A biblioteca existente fornece os SVGs. Palavras fracas não substituem o
    assunto; verbos de dano ganham um alvo visível e uma ação de colapso.
    """
    candidates = []
    terms = {plain(w) for w, _ in pairs}
    phrase_indices = set()
    # A unidade semântica pode ocupar várias palavras ("anã vermelha",
    # "gigante azul", "fusão nuclear"). O nome completo precede o adjetivo
    # isolado, que poderia apontar para outro objeto da mesma biblioteca.
    for span in (3, 2):
        for i in range(len(pairs) - span + 1):
            indices = set(range(i, i + span))
            if indices & phrase_indices:
                continue
            tokens = [plain(w) for w, _t in pairs[i:i + span]]
            phrase = " ".join(tokens)
            obj = WORD_PROP.get(phrase) or ilustras.resolve("_".join(tokens))
            if obj and ilustras.resolve(obj):
                candidates.append((float(pairs[i][1]), 10, ilustras.resolve(obj), None))
                phrase_indices.update(indices)
    for i, (word, t) in enumerate(pairs):
        if i in phrase_indices:
            continue
        token = plain(word)
        obj = word_prop(word)
        if not obj or token in WEAKWORD or not ilustras.resolve(obj):
            continue
        if obj == "earth" and topic == "nature":
            obj = "earthquake"  # solo/placas, não globo astronômico
        if obj == "prism" and not {"prisma", "espectro", "cores", "luz"} & terms:
            continue  # "o fogo se espalha" não é decomposição da luz
        if obj == "hourglass" and token == "tempo" and \
                {"seco", "seca", "chuva", "vento", "clima"} & terms:
            continue  # "tempo seco" é clima, não duração
        if obj == "water" and {"falta", "ausencia", "sem"} & terms and \
                {"chuva", "agua"} & terms:
            continue  # ausência de chuva não deve mostrar uma gota cheia
        cat = ilustras.category(obj)
        if cat == "astro" and topic != "astro":
            continue
        if cat == "world" and token not in {
                "casa", "casas", "cidade", "cidades", "rua", "ruas", "pergunta",
                "duvida", "fabrica", "fabricas", "carro", "carros", "navio", "navios"}:
            continue
        score = 3 + (2 if cat == topic else 0) + (1 if cat == "concept" else 0)
        if cat == "biome" and topic == "nature":
            score -= 2
        if obj == last_prop:
            score -= 1
        candidates.append((float(t), score, obj, None))

    for word, t in pairs:
        token = plain(word)
        if token in ACTION_WORDS:
            if {"visibilidade", "vista", "visivel"} & terms and not \
                    {"cidade", "cidades", "casa", "casas", "predio", "predios"} & terms:
                continue  # "derruba a visibilidade" é perda de visão
            if {"cidade", "cidades", "predios", "predio"} & terms:
                target = "city"
            elif {"floresta", "arvore", "arvores"} & terms:
                target = "tree"
            elif topic == "energy":
                target = "factory"
            else:
                target = "house"
            candidates.append((float(t), 9, target, "collapse"))
        elif token in {"invade", "invadem", "inundou", "alagou", "transborda"} \
                and {"casa", "casas", "rua", "ruas", "cidade", "cidades"} & terms:
            candidates.append((float(t), 8, "house", "flood"))
        elif token in {"gira", "giram", "girando", "rotacao"} and \
                scene in ("vortex", "spiral_storm"):
            candidates.append((float(t), 8, SCENE_PROP[scene], "spin"))

    candidates.sort(key=lambda c: (c[0], -c[1]))
    chosen = []
    for t, score, obj, effect in candidates:
        if not seg_start <= t < seg_end or score < 2:
            continue
        if chosen and t - chosen[-1][0] < 0.28:
            if score > chosen[-1][1]:
                chosen[-1] = (t, score, obj, effect)
            continue
        if chosen and chosen[-1][2] == obj:
            if effect and not chosen[-1][3]:
                chosen[-1] = (chosen[-1][0], max(score, chosen[-1][1]), obj, effect)
            continue
        chosen.append((t, score, obj, effect))
        if len(chosen) >= 4:
            break

    if chosen and chosen[0][2] == last_prop:
        chosen.pop(0)
        support = SCENE_SUPPORT.get(scene) or FALLBACK.get(topic)
        if support and support != last_prop and ilustras.resolve(support):
            chosen.insert(0, (seg_start, 2, support, None))

    if not chosen or chosen[0][0] > seg_start + 0.75:
        palette = [SCENE_PROP.get(scene), SCENE_SUPPORT.get(scene),
                   FALLBACK.get(topic, "question")]
        first = chosen[0][2] if chosen else None
        base = next((p for p in palette if p and ilustras.resolve(p)
                     and p != first and p != last_prop), None)
        if base is None:
            base = next((p for p in palette if p and ilustras.resolve(p)
                         and p != first), None)
        if base is None:
            base = next((p for p in palette if p and ilustras.resolve(p)), None)
        if base:
            chosen.insert(0, (seg_start, 2, base, None))
    chosen = [item for i, item in enumerate(chosen)
              if i == 0 or item[2] != chosen[i - 1][2]]
    if densify:
        # Um objeto novo sustenta uma fala longa quando o léxico não oferece
        # outro referente. Alterna dois objetos do próprio fenômeno, nunca um
        # ícone arbitrário escolhido só para preencher tempo.
        palette = [SCENE_PROP.get(scene), SCENE_SUPPORT.get(scene)]
        palette = [p for p in palette if p and ilustras.resolve(p) and p != last_prop]
        for _ in range(3):
            starts = [seg_start] + [item[0] for item in chosen] + [seg_end]
            starts = sorted(set(starts))
            gaps = [(b - a, a, b) for a, b in zip(starts, starts[1:])]
            if not gaps:
                break
            gap, a, b = max(gaps)
            if gap <= 3.0 or not palette:
                break
            midpoint = a + gap / 2
            word_times = [t for _w, t in pairs if a + 1.0 <= t <= b - 0.8]
            t = min(word_times, key=lambda x: abs(x - midpoint)) if word_times else midpoint
            before = next((item[2] for item in reversed(sorted(chosen)) if item[0] < t), None)
            after = next((item[2] for item in sorted(chosen) if item[0] > t), None)
            prop = next((p for p in palette if p != before and p != after), None)
            if not prop:
                break
            chosen.append((round(t, 3), 2, prop, None))
            chosen.sort()
        # dedupe de novo: o densify pode colar o mesmo id no vizinho
        chosen = [item for i, item in enumerate(chosen)
                  if i == 0 or item[2] != chosen[i - 1][2]]
    # Guarda final: o 1º objeto do segmento nunca pode repetir o último do anterior
    # (mesmo que a paleta de fallback o tenha reinserido depois da troca inicial).
    if chosen and last_prop and chosen[0][2] == last_prop:
        support = SCENE_SUPPORT.get(scene) or FALLBACK.get(topic)
        alt = next((p for p in (support, SCENE_PROP.get(scene),
                                FALLBACK.get(topic), "question")
                    if p and p != last_prop and ilustras.resolve(p)), None)
        if alt:
            chosen[0] = (chosen[0][0], chosen[0][1], alt, chosen[0][3])
        else:
            chosen.pop(0)
    return [
        {"tipo": "ilustra", "id": obj, "at": round(t, 3), "pos": "centro_alto",
         "size": 480, "_semantic": True, **({"effect": effect} if effect else {})}
        for t, _score, obj, effect in chosen[:5]
    ]


def direct_segment(text, cfg, pairs, topic, seg_start, seg_end, state):
    """Diretor de segmento: número/widget (com unidade) + legenda curta.

    A apresentação segue scene_kind, decidido antes da montagem: painel ou texto
    com unidade, além da legenda ligada ao conteúdo.
    """
    dur = max(0.6, seg_end - seg_start)
    scene = state.get("scene") or chapter_scene(state.get("chapter_id", ""),
                                                cfg.get("titulo", ""), topic)
    els = []
    nums = find_numbers(text)
    if nums:
        w = build_widget(text, nums[0])
        if w and state.get("scene_kind") != "dado_texto":
            wid, params, cap = w
            els.append({"tipo": "mg", "id": wid, "modo": "panel", "params": params,
                        "palavra": nums[0]["palavra"], "pos": "centro_alto"})
            els.append({"tipo": "frase", "texto": cap, "pos": "legenda"})
        else:
            for i, n in enumerate(nums[:2]):
                els.append({"tipo": "callout", "texto": n["raw"].upper(),
                            "palavra": n["palavra"], "pos": "acima" if i == 0 else "baixo"})
        return els
    if dur >= 2.2:
        state["seg_ch"] = state.get("seg_ch", 0) + 1
        cap = MG_SCENE_LABEL.get(scene)
        if state["seg_ch"] > 1:            # varia: 1ª legenda é a da cena, depois a palavra
            kw = salient_word(pairs, set())
            if kw:
                cap = kw.upper()
        if cap:
            els.append({"tipo": "frase", "texto": cap, "pos": "legenda"})
    return els


def auto_elements(seg, cfg, plan_cenas, seg_start, seg_end, align, state=None):
    """Plano autoral + objetos semânticos escolhidos pelo motor para toda fala."""
    text = seg["text"]
    state = state if state is not None else {}
    pairs = seg_word_list(align, seg["id"])
    topic = state.get("topic", "general")
    explicit = plan_cenas.get(seg["id"])
    els = [dict(e) for e in explicit] if explicit else direct_segment(
        text, cfg, pairs, topic, seg_start, seg_end, state)
    # O plano autoral escolhe o conteúdo. O diretor ainda varia a apresentação
    # dos dados; preserva valores, unidades, âncoras e ações do autor.
    if explicit and state.get("scene_kind") == "dado_texto":
        nums = find_numbers(text)
        if nums:
            els = [({"tipo": "callout", "texto": nums[0]["raw"].upper(),
                     "palavra": e.get("palavra") or nums[0]["palavra"], "pos": "acima"}
                    if e.get("tipo") == "mg" and not mg.is_full(str(e.get("id", "")))
                    else e) for e in els]
    if any(e.get("tipo") in ("ilustra", "imagens", "heroi") for e in els):
        return els  # override humano de objeto
    blockers = []
    for e in els:
        kind = e.get("tipo")
        if kind != "callout" and not (kind == "mg" and
                not mg.is_full(str(e.get("id") or ""))):
            continue
        anchor = align.word_time(seg["id"], e.get("palavra"), seg_start, seg_end)
        at = anchor if anchor is not None else seg_start
        duration = min(2.6 if kind == "callout" else 4.2, seg_end - at)
        blockers.append((max(seg_start, at - 0.2), min(seg_end, at + duration + 0.15)))
    windows = []
    cursor = seg_start
    for left, right in sorted(blockers):
        if left - cursor >= 0.6:
            windows.append((cursor, left))
        cursor = max(cursor, right)
    if seg_end - cursor >= 0.6:
        windows.append((cursor, seg_end))
    objects = []
    for left, right in windows:
        local = [(w, t) for w, t in pairs if left <= t < right]
        fresh = semantic_objects(text, local, topic, state.get("scene", "wind_field"),
                                 left, right,
                                 objects[-1]["id"] if objects else state.get("last_prop"))
        objects.extend(fresh)
    if objects:
        state["last_prop"] = objects[-1]["id"]
        for el in els:
            if el.get("tipo") == "frase" and el.get("pos", "centro") == "centro":
                el["pos"] = "legenda"
    return els + objects


# ---------------------------------------------------------------- resolução

def resolve_time(anchor, sid, seg_start, seg_end, align, fallback_frac):
    if anchor:
        t = align.word_time(sid, anchor, seg_start, seg_end)
        if t is not None:
            return round(t, 3)
    return round(seg_start + (seg_end - seg_start) * fallback_frac, 3)


def plan_scenes(plan, timing, align_obj, segments):
    """Decide toda a direção antes de gerar elementos; não usa aleatoriedade.

    O diagrama é uma tomada com começo/fim, nunca papel de parede. Dados
    mantêm a unidade; a alternância muda a apresentação, não o significado.
    """
    segs = {s["id"]: s for s in timing["segments"]}
    chapters = {c["id"]: c for c in segments.get("chapters", [])}
    ordered = [s for s in segments["segments"] if s["id"] in segs]
    shots = []
    last_kind = last_recipe = last_entry = None
    for index, meta in enumerate(ordered):
        sid = meta["id"]
        seg = segs[sid]
        start = float(seg["start"])
        end = (float(segs[ordered[index + 1]["id"]]["start"])
               if index + 1 < len(ordered) else float(timing.get("total") or start + seg["dur"]))
        if end <= start:
            raise ValueError(f"Segmento sem duração positiva: {sid}")
        ch = chapters.get(meta.get("chapter"), {"id": meta.get("chapter", "intro"),
                                                "label": meta.get("chapter", "INTRO")})
        cfg = chapter_cfg(plan, ch)
        text = meta.get("text") or seg.get("text", "")
        topic = topic_of(ch["id"], f"{ch.get('label', '')} {segments.get('episode', '')}")
        recipe = cfg.get("mg") or chapter_scene(ch["id"], ch.get("label"), topic)
        explicit = plan.get("cenas", {}).get(sid)
        numbers = find_numbers(text)
        if numbers:
            kind = "dado_texto" if last_kind == "dados" else "dados"
            reason = "Valor e unidade presentes na fala"
        elif (recipe not in ("globe_grid", "star_warp", "hr_diagram")
              and last_kind not in (None, "fenomeno") and recipe != last_recipe
              and index % 3 == 2):
            kind, reason = "fenomeno", "Fenômeno do capítulo em tomada dedicada"
        else:
            kind = "detalhe" if last_kind == "objeto" else "objeto"
            reason = "Objeto contextual; alternância de enquadramento"
        entry = next(e for e in (("cut_pop", "fade", "slide_in") if kind == "detalhe"
                                else ("fade", "slide_in", "cut_pop")) if e != last_entry
                     and (e != "cut_pop" or kind == "detalhe"))
        background = {"dados": "azul", "dado_texto": "preto", "objeto": "petroleo",
                      "detalhe": "ameixa", "fenomeno": "azul", "autoral": "preto"}[kind]
        shots.append({"id": f"cena-{index + 1:04d}", "segment": sid,
                      "chapter": ch["id"], "start": round(start, 3),
                      "dur": round(end - start, 3), "tipo": kind,
                      "fundo": background, "entrada": entry, "motivo": reason,
                      "autoral": bool(explicit),
                      "movimento": "kenburns" if kind == "detalhe" else "drift",
                      "direcao": -1 if index % 2 else 1,
                      "recipe": recipe if kind == "fenomeno" else None})
        last_kind, last_entry = kind, entry
        # Um fenômeno só volta após outro fenômeno contextual, nunca em loop.
        if kind == "fenomeno":
            last_recipe = recipe
    if shots and shots[0]["start"] > 0:
        shots[0]["dur"] = round(shots[0]["dur"] + shots[0]["start"], 3)
        shots[0]["start"] = 0.0
    return shots


def build_elements(plan, timing, align_obj, segments, scene_plan=None):
    segs = {s["id"]: s for s in timing["segments"]}
    meta = {s["id"]: s for s in segments["segments"]}
    align = Align(align_obj, {sid: m.get("text", "") for sid, m in meta.items()})
    order = [s["id"] for s in segments["segments"] if s["id"] in segs]
    chapters = {c["id"]: c for c in segments.get("chapters", [])}

    elements = []
    # Fundos e fenômenos pertencem exclusivamente às cenas planejadas.
    total = timing.get("total") or (segs[order[-1]]["start"] + segs[order[-1]]["dur"])
    scene_plan = scene_plan if scene_plan is not None else plan_scenes(plan, timing, align_obj, segments)
    planned = {s["segment"]: s for s in scene_plan}
    for shot in scene_plan:
        elements.append({"tipo": "fundo_seg", "fundo": shot["fundo"],
                         "start": shot["start"], "dur": shot["dur"], "scene_id": shot["id"]})
        if shot["recipe"]:
            elements.append({"tipo": "mg", "id": shot["recipe"], "modo": "full",
                             "cut": True, "start": shot["start"], "dur": shot["dur"],
                             "scene_id": shot["id"], "params": {}})

    # limites de cada capítulo (start -> início do PRÓXIMO capítulo), para a CENA de
    # tela cheia cobrir o bloco sem invadir o vizinho (o runtime oculta sobreposição)
    ch_order = [c["id"] for c in segments.get("chapters", [])]
    bounds = {}
    for ci, cid in enumerate(ch_order):
        sids = [x for x in chapters.get(cid, {}).get("segments", []) if x in segs]
        if not sids:
            continue
        st = min(segs[x]["start"] for x in sids)
        en = max(segs[x]["start"] + segs[x]["dur"] for x in sids)
        nxt = None
        for cj in ch_order[ci + 1:]:
            sj = [x for x in chapters.get(cj, {}).get("segments", []) if x in segs]
            if sj:
                nxt = min(segs[x]["start"] for x in sj)
                break
        bounds[cid] = (st, nxt if nxt is not None else total)

    seen_ch = set()
    state = {"last_prop": None, "split_side": "esquerda"}
    for oi, sid in enumerate(order):
        s = segs[sid]
        m = meta[sid]
        seg_start, seg_end = s["start"], s["start"] + s["dur"]
        next_start = segs[order[oi + 1]]["start"] if oi + 1 < len(order) else seg_end
        span = max(0.6, next_start - seg_start)   # cobre até o próximo segmento
        ch = chapters.get(m.get("chapter"), {"id": m.get("chapter", "intro"),
                                             "label": m.get("chapter", "INTRO")})
        cfg = chapter_cfg(plan, ch)
        state["scene_kind"] = planned[sid]["tipo"]
        state["topic"] = topic_of(ch["id"],
                                  f"{ch.get('label', '')} {cfg.get('titulo', '')} "
                                  f"{segments.get('episode', '')}")
        state["chapter_id"] = ch["id"]
        state["scene"] = cfg.get("mg") or chapter_scene(ch["id"], ch.get("label"),
                                                        state["topic"])
        if state.get("_last_ch") != ch["id"]:
            state["seg_ch"] = 0
            state["_last_ch"] = ch["id"]
        if ch["id"] not in seen_ch:
            seen_ch.add(ch["id"])
            ch_segs = [segs[x] for x in ch.get("segments", [sid]) if x in segs] or [s]
            c_start = min(x["start"] for x in ch_segs)
            c_end = max(x["start"] + x["dur"] for x in ch_segs)
            # O título identifica a entrada do capítulo; o plano controla os fundos.
            elements.append({"tipo": "titulo", "texto": cfg["titulo"], "cor": cfg.get("cor"),
                             "start": round(c_start, 3),
                             "dur": round(min(2.4, bounds[ch["id"]][1] - c_start), 3)})
            # Corte de capítulo sem sweep automático: a entrada é planejada.

        els = auto_elements(s, cfg, plan["cenas"], seg_start, seg_end, align, state)
        for el in els:
            el["scene_id"] = planned[sid]["id"]
            el.setdefault("entrada", planned[sid]["entrada"])
            if el.get("tipo") == "ilustra":
                el.setdefault("motion", planned[sid]["movimento"])
                el.setdefault("motion_extra", [36 * planned[sid]["direcao"], -16])
            if el.get("_semantic"):
                el["entrada"] = planned[sid]["entrada"]
                el["size"] = 620 if state["scene_kind"] == "detalhe" else 480

        # resolve o início de cada beat (as ilustrações cobrem até o PRÓXIMO beat,
        # em vez de segurar a tela pelo segmento inteiro)
        resolved = []
        for i, el in enumerate(els):
            kind = el.get("tipo")
            if el.get("at") is not None:
                resolved.append(float(el["at"]))
            elif kind in ("ilustra", "imagens", "frase", "mascote", "mg") + tuple(GRAPHIC) \
                    and not el.get("palavra"):
                resolved.append(seg_start)
            else:
                resolved.append(resolve_time(el.get("palavra"), sid, seg_start, seg_end, align,
                                             fallback_frac=min(0.75, 0.12 + i * 0.22)))
        # o PRIMEIRO objeto abre o segmento (a tela nunca fica vazia na virada)
        first_ilus = next((i for i, el in enumerate(els)
                           if el.get("tipo") in _OPENERS), None)
        if first_ilus is not None and els[first_ilus].get("at") is None:
            resolved[first_ilus] = seg_start
        # as ILUSTRAÇÕES encadeiam entre si (o objeto fica de fundo); callouts e
        # palavras são overlays por cima — não encurtam o objeto anterior.
        ilus_starts = sorted({round(resolved[i], 3) for i, el in enumerate(els)
                              if el.get("tipo") in ("ilustra", "imagens")})
        foreground_starts = sorted(round(resolved[i], 3) for i, el in enumerate(els)
                                   if el.get("tipo") in ("mg", "callout")
                                   and (el.get("tipo") != "mg" or
                                        not mg.is_full(str(el.get("id") or ""))))

        # TELA DIVIDIDA: com dois objetos, o primeiro desliza para um lado quando o
        # segundo entra (do outro lado). Com objeto + número, um fica de cada lado.
        # O lado alterna a cada segmento (esquerda → direita → esquerda...).
        is_directed = any(e.get("_dir") for e in els)
        is_explicit = sid in plan["cenas"] or is_directed
        ilus_idx = [i for i, el in enumerate(els) if el.get("tipo") in ("ilustra", "imagens")]
        text_idx = [i for i, el in enumerate(els) if el.get("tipo") == "callout"]
        side = state.get("split_side", "esquerda")
        opp = "direita" if side == "esquerda" else "esquerda"
        split = False
        if any(e.get("_semantic") for e in els):
            pass  # um objeto contextual por vez no centro; a tomada seguinte o troca
        elif len(ilus_idx) >= 3 and not is_directed:
            # segmento longo: objetos em CADEIA, alternando de lado (nunca fica parado)
            for k, i in enumerate(ilus_idx):
                els[i]["pos"] = "esquerda" if k % 2 == 0 else "direita"
                els[i]["size"] = min(int(els[i].get("size") or 520), 520)
        elif is_explicit:
            split = len(ilus_idx) == 2          # plano autoral já define os lados
        elif len(ilus_idx) == 2:
            # AUTOGERADO: o 1º desliza para um lado quando o 2º entra (tela dividida)
            split = True
            els[ilus_idx[0]]["pos"] = "centro_alto"
            els[ilus_idx[0]]["move_to"] = side
            els[ilus_idx[0]]["move_at"] = resolved[ilus_idx[1]]
            els[ilus_idx[1]]["pos"] = opp
            els[ilus_idx[1]]["size"] = min(int(els[ilus_idx[1]].get("size") or 520), 520)
            state["split_side"] = opp
        elif ilus_idx and text_idx:
            split = True
            els[ilus_idx[0]]["pos"] = side
            els[ilus_idx[0]]["size"] = min(int(els[ilus_idx[0]].get("size") or 560), 560)
            els[text_idx[0]]["pos"] = "dir" if side == "esquerda" else "esq"
            state["split_side"] = opp

        slot = 0
        for i, el in enumerate(els):
            kind = el.get("tipo")
            start = resolved[i]
            if kind in ("ilustra", "imagens"):
                if split:
                    end = min(seg_end, next_start)     # objetos persistem lado a lado
                else:
                    later = [x for x in ilus_starts + foreground_starts if x > start + 0.05]
                    end = min(min(later) if later else seg_end, next_start)
                el = dict(el)
                el["start"] = round(start, 3)
                el["dur"] = round(max(0.25, end - start), 3)
                el["_seg"] = sid
                el["_chapter"] = ch["id"]
                elements.append(el)
                continue
            if kind == "lista":
                step = el.get("step", 0.72)
                for k, item in enumerate(el["itens"][:5]):
                    st = min(start + k * step, seg_end - 0.1)
                    elements.append({"tipo": "lista_item", "texto": f"{k+1}. {item}",
                                     "pos": el.get("pos", "dir"), "indice": k,
                                     "start": round(st, 3),
                                     "dur": round(max(1.2, span - (st - seg_start)), 3)})
                continue
            el = dict(el)
            el["_seg"] = sid
            el["_chapter"] = ch["id"]
            if kind == "callout":
                el.setdefault("slot", slot)
                slot += 1
                el["start"] = round(start, 3)
                # não deixa o callout invadir o próximo segmento (evita texto sobreposto)
                el["dur"] = round(max(0.8, min(2.6, next_start - start)), 3)
            elif kind == "palavra":
                el["start"] = round(start, 3)
                el["dur"] = round(max(0.9, min(1.8, next_start - start)), 3)
                el.setdefault("cor", cfg.get("cor"))
            elif kind == "frase":
                el["start"] = round(start, 3)
                el["dur"] = round(min(el.get("dur") or 2.8, max(1.2, seg_end - start)), 3)
            elif kind == "mascote":
                el["start"] = round(start, 3)
                el["dur"] = round(min(el.get("dur") or 4.0, span), 3)
            elif kind == "heroi":
                el["start"] = round(seg_start, 3)
                el["dur"] = round(min(4.6, span + 0.3), 3)
            elif kind == "textao":
                el["start"] = round(seg_start, 3)
                el["dur"] = round(min(3.4, span + 0.2), 3)
            elif kind == "mg":
                # CENA de tela cheia: cobre o segmento (movimento contínuo);
                # WIDGET de dados: cartão por cima da cena, pela duração da fala.
                full = mg.is_full(str(el.get("id") or ""))
                el["start"] = round(start, 3)
                if full:
                    el["dur"] = round(max(1.0, next_start - start), 3)
                else:
                    el["dur"] = round(max(0.25, min(4.2, next_start - start - 0.1)), 3)
            elif kind in GRAPHIC:
                # a tela de dados cobre o segmento inteiro (a cena nunca fica vazia
                # depois que a animação termina)
                el["start"] = round(start, 3)
                el["dur"] = round(max(el.get("dur") or 0, next_start - start), 3)
            else:
                el["start"] = round(start, 3)
                el["dur"] = round(min(el.get("dur") or 2.6, max(1.2, seg_end - start)), 3)
            elements.append(el)

    # overlays da mesma faixa não podem se sobrepor (ex.: duas pílulas de destaque
    # em segmentos vizinhos) — corta a anterior no início da seguinte
    for kind in ("palavra",):
        row = sorted((e for e in elements if e["tipo"] == kind), key=lambda e: e["start"])
        for a, b in zip(row, row[1:]):
            if a["start"] + a["dur"] > b["start"]:
                a["dur"] = round(max(0.4, b["start"] - a["start"] - 0.08), 3)
    # Sustenta a Ãºltima imagem/frase no respiro final, sem deixar um quadro vazio.
    foreground = [e for e in elements if e["tipo"] in
                  ("ilustra", "imagens", "frase", "callout", "palavra", "heroi")]
    if foreground:
        last = max(foreground, key=lambda e: e["start"] + e["dur"])
        tail = total - (last["start"] + last["dur"])
        if 0.3 < tail <= 2.0:
            last["dur"] = round(total - last["start"], 3)
    # Pass final: ilustra imediatamente seguinte com o MESMO id é repetição
    # (o gauntlet reprova). Estende a anterior e descarta a duplicata.
    _ilus = sorted((e for e in elements if e.get("tipo") in ("ilustra", "imagens")),
                   key=lambda e: e["start"])
    _drop = set()
    for a, b in zip(_ilus, _ilus[1:]):
        if id(a) in _drop or id(b) in _drop:
            continue
        if a.get("id") and a.get("id") == b.get("id") and b["start"] - (a["start"] + a["dur"]) < 0.5:
            a["dur"] = round(max(a["dur"], b["start"] + b["dur"] - a["start"]), 3)
            _drop.add(id(b))
    if _drop:
        elements = [e for e in elements if id(e) not in _drop]
    # Pausas da narração não são cortes para uma tela vazia. Sustenta o último
    # conteúdo até a próxima entrada; preserva o tempo da palavra que o revela.
    visible = sorted((e for e in elements if e["tipo"] in
                      ("ilustra", "imagens", "frase", "callout", "palavra", "heroi",
                       "textao", "titulo", "mg") and e.get("dur", 0) > 0),
                     key=lambda e: e["start"])
    latest = None
    # A pausa que o gauntlet considera ritmo parado é a mesma que aqui vira
    # sustentação de conteúdo. Um número só: plano.max_gap_s.
    sustaining = limite("plano.max_gap_s", 0.9)
    for el in visible:
        if latest is not None:
            gap = el["start"] - (latest["start"] + latest["dur"])
            if 0 < gap <= sustaining:
                latest["dur"] = round(el["start"] - latest["start"], 3)
        if latest is None or el["start"] + el["dur"] > latest["start"] + latest["dur"]:
            latest = el
    elements.extend(collect_sfx(elements))
    return elements


# nomes de SFX disponíveis na biblioteca local (assets/sfx). Prioridade maior =
# sobrevive quando dois acentos caem no mesmo instante.
SFX_PRIO = {"impact-bass-2": 6, "impact-bass-1": 5, "ping": 4, "sparkle": 3,
            "pop": 2, "whoosh-short": 2, "whoosh": 1}


def collect_sfx(elements):
    """Acentos sonoros SÓ em momentos especiais (transição de capítulo, tela-herói,
    gráfico/medidor/barra, crescimento de objeto, pergunta final). Nunca em todo corte."""
    cues = []

    def add(name, start, gain=0.34):
        cues.append({"tipo": "sfx", "nome": name,
                     "start": round(max(0.0, float(start)), 3), "gain": round(gain, 2)})

    for e in elements:
        t = e.get("tipo")
        if t == "transicao" and e.get("start", 0) >= 0.5:
            add("whoosh", e["start"], 0.30)
        elif t == "heroi":
            add("impact-bass-2" if e.get("id") == "supernova" else "impact-bass-1",
                e["start"], 0.40)
        elif t == "textao":
            add("whoosh-short", e["start"], 0.32)
        elif t == "comparacao":
            add("sparkle", e["start"], 0.34)
        elif t == "mg" and not mg.is_full(str(e.get("id") or "")):
            add("pop", e["start"] + 0.15, 0.30)
        elif t in GRAPHIC:
            add("pop", e["start"] + 0.15, 0.30)
        elif t == "ilustra" and e.get("cresce"):
            add("sparkle", e["start"] + float(e["cresce"].get("delay", 0.15)), 0.34)

    # pergunta final do fechamento: um ping marca o gancho
    for e in elements:
        if e.get("_chapter") == "fechamento" and e.get("tipo") == "frase":
            add("ping", e["start"], 0.34)
            break

    cues.sort(key=lambda c: (c["start"], -SFX_PRIO.get(c["nome"], 0)))
    out = []
    for c in cues:
        if out and c["start"] - out[-1]["start"] < 1.1:
            if SFX_PRIO.get(c["nome"], 0) > SFX_PRIO.get(out[-1]["nome"], 0):
                out[-1] = c
            continue
        out.append(c)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--timing", default="timing_v1.json")
    ap.add_argument("--align", default="alignment_v1.json")
    ap.add_argument("--segments", default="segments_v1.json")
    ap.add_argument("--cenas", default="cenas.json")
    ap.add_argument("--out", default="episode.json")
    ap.add_argument("--plan-only", action="store_true", help="salva plano_cenas.json antes de gerar elementos")
    ap.add_argument("--version", default=None,
                    help="versão da narração (padrão: extraída de timing_<versão>.json)")
    a = ap.parse_args()
    p = a.project
    j = lambda f: json.load(open(os.path.join(p, f), encoding="utf-8"))  # noqa: E731

    timing, align_obj, segments = j(a.timing), j(a.align), j(a.segments)
    plan = load_plan(os.path.join(p, a.cenas))
    scene_plan = plan_scenes(plan, timing, align_obj, segments)
    with open(os.path.join(p, "plano_cenas.json"), "w", encoding="utf-8") as output:
        json.dump({"schema_version": 1, "episode": segments.get("episode"),
                   "scenes": scene_plan}, output, ensure_ascii=False, indent=2)
    if a.plan_only:
        print("->", os.path.join(p, "plano_cenas.json"))
        return
    elements = build_elements(plan, timing, align_obj, segments, scene_plan)

    total = timing.get("total")
    inferred_version = re.fullmatch(r"timing_(.+)\.json", os.path.basename(a.timing))
    version = a.version or (inferred_version.group(1) if inferred_version else None)
    episode = {"theme": plan["theme"], "total": total, "episode": segments.get("episode"),
               "version": version,
               "chapters": [{"id": c["id"], "label": c["label"],
                             **chapter_cfg(plan, c)} for c in segments.get("chapters", [])],
               "scene_plan": scene_plan, "elements": elements}
    json.dump(episode, open(os.path.join(p, a.out), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    kinds = {}
    for e in elements:
        kinds[e["tipo"]] = kinds.get(e["tipo"], 0) + 1
    print(f"ok | {len(elements)} elementos | total {total:.1f}s | " +
          " ".join(f"{k}:{v}" for k, v in sorted(kinds.items())))
    print("->", os.path.join(p, a.out))


if __name__ == "__main__":
    main()
