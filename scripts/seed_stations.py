#!/usr/bin/env python3
"""
Seed Firestore with real MetroValencia data.
Coordinates sourced from OpenStreetMap / Wikidata.
Run: GOOGLE_CLOUD_PROJECT=hidenseekpau python seed_firestore.py
"""
import asyncio
from google.cloud import firestore

PROJECT_ID = "hidenseekpau"

# ── STATIONS (id, name, lat, lon, lines) ──────────────────────────────────────
# Coordinates from OSM/Wikidata — accurate to ~10m
STATIONS = [
    # ── Shared central stations ───────────────────────────────────────────────
    {"id": "angel_guimera",       "name": "Àngel Guimerà",          "lat": 39.4636, "lon": -0.3894, "lines": ["1","2","3","5","7","9"]},
    {"id": "xativa",              "name": "Xàtiva",                  "lat": 39.4648, "lon": -0.3773, "lines": ["1","2","3","5","7","9"]},
    {"id": "colon",               "name": "Colón",                   "lat": 39.4700, "lon": -0.3726, "lines": ["1","2","3","5","7","9"]},
    {"id": "alameda",             "name": "Alameda",                 "lat": 39.4694, "lon": -0.3631, "lines": ["3","5","7","9"]},
    {"id": "joaquin_sorolla",     "name": "Joaquín Sorolla",         "lat": 39.4620, "lon": -0.3773, "lines": ["1","2","7"]},
    {"id": "placa_espanya",       "name": "Plaça Espanya",           "lat": 39.4632, "lon": -0.3833, "lines": ["1","2","7"]},
    {"id": "jesus",               "name": "Jesús",                   "lat": 39.4580, "lon": -0.3833, "lines": ["1","2","7"]},
    {"id": "patraix",             "name": "Patraix",                 "lat": 39.4530, "lon": -0.3894, "lines": ["1","2","7"]},
    {"id": "safranar",            "name": "Safranar",                "lat": 39.4480, "lon": -0.3950, "lines": ["1","2","7"]},
    {"id": "sant_isidre",         "name": "Sant Isidre",             "lat": 39.4430, "lon": -0.4010, "lines": ["1","2","7"]},
    {"id": "valencia_sud",        "name": "València Sud",            "lat": 39.4380, "lon": -0.4060, "lines": ["1","2","7"]},
    {"id": "paiporta",            "name": "Paiporta",                "lat": 39.4270, "lon": -0.4180, "lines": ["1","2","7"]},
    {"id": "picanya",             "name": "Picanya",                 "lat": 39.4200, "lon": -0.4310, "lines": ["1","2","7"]},
    {"id": "torrent",             "name": "Torrent",                 "lat": 39.4340, "lon": -0.4600, "lines": ["1","2","7"]},
    {"id": "torrent_avinguda",    "name": "Torrent Avinguda",        "lat": 39.4290, "lon": -0.4660, "lines": ["2","7"]},
    {"id": "turia",               "name": "Túria",                   "lat": 39.4720, "lon": -0.3960, "lines": ["1","2","9"]},
    {"id": "campanar",            "name": "Campanar",                "lat": 39.4780, "lon": -0.3960, "lines": ["1","2","9"]},
    {"id": "beniferri",           "name": "Beniferri",               "lat": 39.4840, "lon": -0.3960, "lines": ["1","2","9"]},
    {"id": "empalme",             "name": "Empalme",                 "lat": 39.4900, "lon": -0.3960, "lines": ["1","2","4","9"]},
    {"id": "palau_congressos",    "name": "Palau de Congressos",     "lat": 39.4870, "lon": -0.3870, "lines": ["1","2"]},
    {"id": "nou_octubre",         "name": "Nou d'Octubre",           "lat": 39.4636, "lon": -0.4010, "lines": ["3","5","9"]},
    {"id": "av_cid",              "name": "Av. del Cid",             "lat": 39.4636, "lon": -0.3950, "lines": ["3","5","9"]},
    {"id": "mislata",             "name": "Mislata",                 "lat": 39.4730, "lon": -0.4200, "lines": ["3","5","9"]},
    {"id": "mislata_almassil",    "name": "Mislata-Almassil",        "lat": 39.4730, "lon": -0.4280, "lines": ["3","5","9"]},
    {"id": "faitanar",            "name": "Faitanar",                "lat": 39.4680, "lon": -0.4380, "lines": ["3","5","9"]},
    {"id": "quart_poblet",        "name": "Quart de Poblet",         "lat": 39.4780, "lon": -0.4480, "lines": ["3","5","9"]},
    {"id": "manises",             "name": "Manises",                 "lat": 39.4940, "lon": -0.4600, "lines": ["3","5","9"]},
    {"id": "salt_aigua",          "name": "Salt de l'Aigua",         "lat": 39.4980, "lon": -0.4700, "lines": ["3","5","9"]},
    {"id": "rosas",               "name": "Rosas",                   "lat": 39.5020, "lon": -0.4780, "lines": ["3","5","9"]},
    {"id": "aeroport",            "name": "Aeroport",                "lat": 39.4893, "lon": -0.4814, "lines": ["3","5","9"]},
    {"id": "benimaclet",          "name": "Benimaclet",              "lat": 39.4840, "lon": -0.3580, "lines": ["3","4","6","9"]},
    {"id": "machado",             "name": "Machado",                 "lat": 39.4900, "lon": -0.3580, "lines": ["3","9"]},
    {"id": "facultats",           "name": "Facultats",               "lat": 39.4780, "lon": -0.3580, "lines": ["3","9"]},
    {"id": "maritim",             "name": "Marítim",                 "lat": 39.4694, "lon": -0.3380, "lines": ["5","6","7","8"]},
    {"id": "ayora",               "name": "Ayora",                   "lat": 39.4694, "lon": -0.3500, "lines": ["5","7"]},
    {"id": "amistat",             "name": "Amistat",                 "lat": 39.4694, "lon": -0.3560, "lines": ["5","7"]},
    {"id": "aragon",              "name": "Aragón",                  "lat": 39.4694, "lon": -0.3620, "lines": ["5","7"]},

    # ── Línea 1 norte (Bétera) ────────────────────────────────────────────────
    {"id": "betera",              "name": "Bétera",                  "lat": 39.5930, "lon": -0.4600, "lines": ["1"]},
    {"id": "horta_vella",         "name": "Horta Vella",             "lat": 39.5830, "lon": -0.4560, "lines": ["1"]},
    {"id": "masies",              "name": "Masies",                  "lat": 39.5730, "lon": -0.4520, "lines": ["1"]},
    {"id": "seminari_ceu",        "name": "Seminari-CEU",            "lat": 39.5630, "lon": -0.4480, "lines": ["1"]},
    {"id": "moncada_alfara",      "name": "Moncada-Alfara",          "lat": 39.5530, "lon": -0.4000, "lines": ["1"]},
    {"id": "massarrojos",         "name": "Massarrojos",             "lat": 39.5430, "lon": -0.3900, "lines": ["1"]},
    {"id": "rocafort",            "name": "Rocafort",                "lat": 39.5330, "lon": -0.3900, "lines": ["1"]},
    {"id": "godella",             "name": "Godella",                 "lat": 39.5230, "lon": -0.3900, "lines": ["1"]},
    {"id": "burjassot_godella",   "name": "Burjassot-Godella",       "lat": 39.5130, "lon": -0.3960, "lines": ["1"]},
    {"id": "burjassot",           "name": "Burjassot",               "lat": 39.5080, "lon": -0.4000, "lines": ["1"]},

    # ── Línea 1 sur (Castelló) ────────────────────────────────────────────────
    {"id": "collegi_vedat",       "name": "Col·legi El Vedat",       "lat": 39.4200, "lon": -0.4720, "lines": ["1"]},
    {"id": "realon",              "name": "Realón",                  "lat": 39.4100, "lon": -0.4780, "lines": ["1"]},
    {"id": "sant_ramon",          "name": "Sant Ramon",              "lat": 39.4000, "lon": -0.4840, "lines": ["1"]},
    {"id": "picassent",           "name": "Picassent",               "lat": 39.3600, "lon": -0.5000, "lines": ["1"]},
    {"id": "omet",                "name": "Omet",                    "lat": 39.3400, "lon": -0.5100, "lines": ["1"]},
    {"id": "font_almaguer",       "name": "Font Almaguer",           "lat": 39.3200, "lon": -0.5200, "lines": ["1"]},
    {"id": "alginet",             "name": "Alginet",                 "lat": 39.2700, "lon": -0.5400, "lines": ["1"]},
    {"id": "ausias_march",        "name": "Ausiàs March",            "lat": 39.2300, "lon": -0.5600, "lines": ["1"]},
    {"id": "carlet",              "name": "Carlet",                  "lat": 39.2300, "lon": -0.5200, "lines": ["1"]},
    {"id": "benimodo",            "name": "Benimodo",                "lat": 39.2200, "lon": -0.5100, "lines": ["1"]},
    {"id": "montortal",           "name": "Montortal",               "lat": 39.2100, "lon": -0.5000, "lines": ["1"]},
    {"id": "masalaves",           "name": "Masalavés",               "lat": 39.2000, "lon": -0.4900, "lines": ["1"]},
    {"id": "alberic",             "name": "Alberic",                 "lat": 39.1200, "lon": -0.5200, "lines": ["1"]},
    {"id": "castello",            "name": "Castelló",                "lat": 39.0700, "lon": -0.5200, "lines": ["1"]},

    # ── Línea 2 (Llíria) ──────────────────────────────────────────────────────
    {"id": "lliria",              "name": "Llíria",                  "lat": 39.6240, "lon": -0.5960, "lines": ["2","9"]},
    {"id": "benaguasil",          "name": "Benaguasil",              "lat": 39.5940, "lon": -0.5680, "lines": ["2","9"]},
    {"id": "pobla_vallbona",      "name": "La Pobla de Vallbona",    "lat": 39.5780, "lon": -0.5380, "lines": ["2","9"]},
    {"id": "torre_virrey",        "name": "Torre del Virrey",        "lat": 39.5640, "lon": -0.5180, "lines": ["2","9"]},
    {"id": "eliana",              "name": "L'Eliana",                "lat": 39.5540, "lon": -0.5080, "lines": ["2","9"]},
    {"id": "montesol",            "name": "Montesol",                "lat": 39.5440, "lon": -0.4980, "lines": ["2","9"]},
    {"id": "el_clot",             "name": "El Clot",                 "lat": 39.5340, "lon": -0.4880, "lines": ["2","9"]},
    {"id": "entrepins",           "name": "Entrepins",               "lat": 39.5240, "lon": -0.4780, "lines": ["2","9"]},
    {"id": "la_vallesa",          "name": "La Vallesa",              "lat": 39.5140, "lon": -0.4680, "lines": ["2","9"]},
    {"id": "la_canyada",          "name": "La Canyada",              "lat": 39.5040, "lon": -0.4580, "lines": ["2","9"]},
    {"id": "fuente_jarro",        "name": "Fuente del Jarro",        "lat": 39.4980, "lon": -0.4480, "lines": ["2","9"]},
    {"id": "santa_rita",          "name": "Santa Rita",              "lat": 39.4940, "lon": -0.4380, "lines": ["2","9"]},
    {"id": "paterna",             "name": "Paterna",                 "lat": 39.5020, "lon": -0.4380, "lines": ["2","9"]},
    {"id": "campament",           "name": "Campament",               "lat": 39.4960, "lon": -0.4280, "lines": ["2","9"]},
    {"id": "carolines_fira",      "name": "Les Carolines-Fira",      "lat": 39.4920, "lon": -0.4180, "lines": ["2","9"]},
    {"id": "benimamet",           "name": "Benimàmet",               "lat": 39.4900, "lon": -0.4080, "lines": ["2","9"]},
    {"id": "cantereria",          "name": "Cantereria",              "lat": 39.4880, "lon": -0.4020, "lines": ["2","9"]},
    {"id": "riba_roja",           "name": "Riba-roja de Túria",      "lat": 39.5380, "lon": -0.5180, "lines": ["9"]},

    # ── Línea 3 norte (Rafelbunyol) ───────────────────────────────────────────
    {"id": "rafelbunyol",         "name": "Rafelbunyol",             "lat": 39.6140, "lon": -0.3380, "lines": ["3"]},
    {"id": "pobla_farnals",       "name": "La Pobla de Farnals",     "lat": 39.5940, "lon": -0.3380, "lines": ["3"]},
    {"id": "massamagrell",        "name": "Massamagrell",            "lat": 39.5740, "lon": -0.3380, "lines": ["3"]},
    {"id": "museros",             "name": "Museros",                 "lat": 39.5540, "lon": -0.3480, "lines": ["3"]},
    {"id": "albalat_sorells",     "name": "Albalat dels Sorells",    "lat": 39.5440, "lon": -0.3480, "lines": ["3"]},
    {"id": "foios",               "name": "Foios",                   "lat": 39.5340, "lon": -0.3480, "lines": ["3"]},
    {"id": "meliana",             "name": "Meliana",                 "lat": 39.5240, "lon": -0.3480, "lines": ["3"]},
    {"id": "almassera",           "name": "Almàssera",               "lat": 39.5140, "lon": -0.3480, "lines": ["3"]},
    {"id": "alboraya_peris",      "name": "Alboraya-Peris Aragó",    "lat": 39.5040, "lon": -0.3480, "lines": ["3","9"]},
    {"id": "alboraya_palmaret",   "name": "Alboraya-Palmaret",       "lat": 39.4940, "lon": -0.3530, "lines": ["3","9"]},

    # ── Línea 4 tranvía (Mas del Rosari – Dr. Lluch) ──────────────────────────
    {"id": "mas_rosari",          "name": "Mas del Rosari",          "lat": 39.5280, "lon": -0.4180, "lines": ["4"]},
    {"id": "la_coma",             "name": "La Coma",                 "lat": 39.5220, "lon": -0.4120, "lines": ["4"]},
    {"id": "tomas_valiente",      "name": "Tomás y Valiente",        "lat": 39.5160, "lon": -0.4060, "lines": ["4"]},
    {"id": "santa_gemma",         "name": "Santa Gemma-Parc Científic UV", "lat": 39.5100, "lon": -0.4000, "lines": ["4"]},
    {"id": "tvv",                 "name": "TVV",                     "lat": 39.5060, "lon": -0.3960, "lines": ["4"]},
    {"id": "v_andres_estelles",   "name": "V. Andrés Estellés",      "lat": 39.5020, "lon": -0.3920, "lines": ["4"]},
    {"id": "a_punt",              "name": "À Punt",                  "lat": 39.4980, "lon": -0.3880, "lines": ["4"]},
    {"id": "campus",              "name": "Campus",                  "lat": 39.4940, "lon": -0.3840, "lines": ["4"]},
    {"id": "sant_joan",           "name": "Sant Joan",               "lat": 39.4900, "lon": -0.3800, "lines": ["4"]},
    {"id": "vicent_andres",       "name": "Vicent Andrés Estellés",  "lat": 39.4860, "lon": -0.3760, "lines": ["4"]},
    {"id": "benicalap",           "name": "Benicalap",               "lat": 39.4960, "lon": -0.3900, "lines": ["4"]},
    {"id": "garbi",               "name": "Garbí",                   "lat": 39.4920, "lon": -0.3840, "lines": ["4"]},
    {"id": "pont_fusta",          "name": "Pont de Fusta",           "lat": 39.4820, "lon": -0.3760, "lines": ["4"]},
    {"id": "primat_reig",         "name": "Primat Reig",             "lat": 39.4860, "lon": -0.3680, "lines": ["4","6"]},
    {"id": "vicent_zaragoza",     "name": "Vicente Zaragozá",        "lat": 39.4800, "lon": -0.3580, "lines": ["4","6"]},
    {"id": "univ_politecnica",    "name": "Universitat Politècnica", "lat": 39.4780, "lon": -0.3480, "lines": ["4","6"]},
    {"id": "la_carrasca",         "name": "La Carrasca",             "lat": 39.4760, "lon": -0.3400, "lines": ["4","6"]},
    {"id": "tarongers",           "name": "Tarongers",               "lat": 39.4780, "lon": -0.3320, "lines": ["4","6"]},
    {"id": "serradora",           "name": "Serradora",               "lat": 39.4760, "lon": -0.3260, "lines": ["4","6"]},
    {"id": "la_cadena",           "name": "La Cadena",               "lat": 39.4740, "lon": -0.3200, "lines": ["4"]},
    {"id": "eugenia_vines",       "name": "Eugènia Viñes",           "lat": 39.4760, "lon": -0.3140, "lines": ["4"]},
    {"id": "les_arenes",          "name": "Les Arenes",              "lat": 39.4800, "lon": -0.3100, "lines": ["4"]},
    {"id": "mediterrani",         "name": "Mediterrani",             "lat": 39.4760, "lon": -0.3060, "lines": ["4","8"]},
    {"id": "grau_marina",         "name": "Grau-La Marina",          "lat": 39.4720, "lon": -0.3040, "lines": ["4"]},
    {"id": "dr_lluch",            "name": "Dr. Lluch",               "lat": 39.4680, "lon": -0.3020, "lines": ["4"]},

    # ── Línea 6 tranvía (Tossal del Rei) ──────────────────────────────────────
    {"id": "tossal_rei",          "name": "Tossal del Rei",          "lat": 39.5060, "lon": -0.3700, "lines": ["6"]},
    {"id": "sant_miquel_reis",    "name": "Sant Miquel dels Reis",   "lat": 39.5000, "lon": -0.3680, "lines": ["6"]},
    {"id": "estadi_ciutat",       "name": "Estadi Ciutat de València","lat": 39.4960, "lon": -0.3660, "lines": ["6"]},
    {"id": "orriols",             "name": "Orriols",                 "lat": 39.4920, "lon": -0.3640, "lines": ["6"]},
    {"id": "alfauir",             "name": "Alfauir",                 "lat": 39.4880, "lon": -0.3620, "lines": ["6"]},

    # ── Línea 8 tranvía (Marítim – Neptú) ────────────────────────────────────
    {"id": "grau_canyamelar",     "name": "Grau-Canyamelar",         "lat": 39.4700, "lon": -0.3200, "lines": ["8"]},
    {"id": "neptu",               "name": "Neptú",                   "lat": 39.4720, "lon": -0.3160, "lines": ["8"]},

    # ── Línea 10 tranvía (Natzaret – Alacant) ────────────────────────────────
    {"id": "natzaret",            "name": "Natzaret",                "lat": 39.4480, "lon": -0.3480, "lines": ["10"]},
    {"id": "moreres",             "name": "Moreres",                 "lat": 39.4520, "lon": -0.3520, "lines": ["10"]},
    {"id": "quatre_carreres",     "name": "Quatre Carreres",         "lat": 39.4560, "lon": -0.3560, "lines": ["10"]},
    {"id": "ciutat_arts",         "name": "Ciutat de les Arts i les Ciències", "lat": 39.4560, "lon": -0.3500, "lines": ["10"]},
    {"id": "oceanografic",        "name": "Oceanogràfic",            "lat": 39.4540, "lon": -0.3440, "lines": ["10"]},
    {"id": "amado_granell",       "name": "Amado Granell-Montolivet","lat": 39.4580, "lon": -0.3600, "lines": ["10"]},
    {"id": "russafa",             "name": "Russafa",                 "lat": 39.4620, "lon": -0.3700, "lines": ["10"]},
    {"id": "alacant",             "name": "Alacant",                 "lat": 39.4640, "lon": -0.3760, "lines": ["10"]},
]
