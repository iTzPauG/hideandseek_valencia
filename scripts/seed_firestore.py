#!/usr/bin/env python3
"""
Seed Firestore with exact MetroValencia data.
Station list matches exactly the official lines provided.
Lines are the source of truth — station.lines is derived from them.
Coordinates from OpenStreetMap/Wikidata.
"""
import asyncio
from google.cloud import firestore

PROJECT_ID = "hidenseekpau"

# ── LINES (exact station order from official list) ────────────────────────────
# Station IDs are slugified station names
LINES_DEF = [
    # L1: no Palau de Congressos (GTFS: Empalme→Beniferri direct)
    {"id": "1", "name": "Línia 1", "color": "#FFD700", "stations": [
        "betera","horta_vella","masies","seminari_ceu","moncada_alfara","massarrojos",
        "rocafort","godella","burjassot_godella","burjassot","empalme",
        "beniferri","campanar","turia","angel_guimera","placa_espanya","jesus",
        "patraix","safranar","sant_isidre","valencia_sud","paiporta","picanya",
        "torrent","collegi_vedat","realon","sant_ramon","picassent","omet","espioca",
        "font_almaguer","alginet","ausias_march_carlet","carlet","benimodo",
        "l_alcudia","montortal","masalaves","alberic","castello",
    ]},
    # L2: no Ll.Llarga (that's L4 branch)
    {"id": "2", "name": "Línia 2", "color": "#CC44CC", "stations": [
        "lliria","benaguasil","fondo_benaguasil","pobla_vallbona","gallipont_torre_virrey",
        "eliana","montesol","el_clot","entrepins","la_vallesa","la_canyada","font_barranc",
        "fuente_jarro","santa_rita","paterna","campament","carolines_fira",
        "benimamet","cantereria","empalme","beniferri","campanar","turia","angel_guimera",
        "placa_espanya","jesus","patraix","safranar","sant_isidre",
        "valencia_sud","paiporta","picanya","torrent","torrent_avinguda",
    ]},
    {"id": "3", "name": "Línia 3", "color": "#E74C3C", "stations": [
        "rafelbunyol","pobla_farnals","massamagrell","museros","albalat_sorells","foios",
        "meliana","almassera","alboraya_peris","alboraya_palmaret","machado","benimaclet",
        "facultats","alameda","colon","xativa","angel_guimera","av_cid","nou_octubre",
        "mislata","mislata_almassil","faitanar","quart_poblet","salt_aigua","manises","rosas","aeroport",
    ]},
    # L4 has 3 terminal branches — represented as separate segment groups
    # Branch 1: Mas del Rosari → À Punt → Vicent Andrés → Fira → ... → La Cadena → Cabanyal → Dr.Lluch
    {"id": "4", "name": "Línia 4", "color": "#2980B9", "stations": [
        "mas_rosari","la_coma","tomas_valiente","santa_gemma","a_punt",
        "vicent_andres","empalme","palau_congressos","garbi","benicalap",
        "transits","marxalenes","reus","sagunt","pont_fusta","trinitat",
        "benimaclet","vicent_zaragoza","univ_politecnica","la_carrasca",
        "tarongers","betero","la_cadena",
    ]},
    # L4b: Ll.Llarga → À Punt
    {"id": "4b", "name": "Línia 4 (ramal Ll.Llarga)", "color": "#2980B9", "stations": [
        "ll_llarga","a_punt",
    ]},
    # L4d: Vicent Andrés Estellés → Fira València (third terminal)
    {"id": "4d", "name": "Línia 4 (ramal Fira)", "color": "#2980B9", "stations": [
        "vicent_andres","fira_valencia",
    ]},
    # L4 coastal loop: La Cadena→Cabanyal→Dr.Lluch→Platja les Arenes→Platja Malva-rosa→La Cadena
    {"id": "4c", "name": "Línia 4 (ramal costero)", "color": "#2980B9", "stations": [
        "la_cadena","cabanyal","dr_lluch","platja_les_arenes","platja_malva_rosa","la_cadena",
    ]},
    {"id": "5", "name": "Línia 5", "color": "#27AE60", "stations": [
        "aeroport","rosas","manises","salt_aigua","quart_poblet","faitanar",
        "mislata_almassil","mislata","nou_octubre","av_cid","angel_guimera",
        "xativa","colon","alameda","aragon","amistat","ayora","maritim",
    ]},
    # L6 full coastal loop:
    # Tossal→...→La Cadena→Cabanyal→Dr.Lluch→Canyamelar→Grau→Francesc Cubells→Marítim
    # →Francesc Cubells→Grau→Canyamelar→Platja les Arenes→Platja Malva-rosa→La Cadena
    {"id": "6", "name": "Línia 6", "color": "#8E44AD", "stations": [
        "tossal_rei","sant_miquel_reis","estadi_ciutat","orriols","alfauir","trinitat",
        "benimaclet","vicent_zaragoza","univ_politecnica","la_carrasca","tarongers",
        "betero","la_cadena","cabanyal","dr_lluch",
        "canyamelar","grau_marina","francesc_cubells","maritim",
        "francesc_cubells","grau_marina","canyamelar",
        "platja_les_arenes","platja_malva_rosa","la_cadena",
    ]},
    # L7: exact GTFS — Torrent Avinguda→Marítim, has Bailén not Àngel Guimerà/Xàtiva
    {"id": "7", "name": "Línia 7", "color": "#E67E22", "stations": [
        "maritim","ayora","amistat","aragon","alameda","colon","bailen",
        "jesus","patraix","safranar","sant_isidre","valencia_sud","paiporta",
        "picanya","torrent","torrent_avinguda",
    ]},
    # L8: exact GTFS
    {"id": "8", "name": "Línia 8", "color": "#3498DB", "stations": [
        "maritim","francesc_cubells","grau_marina","neptu",
    ]},
    # L9: exact GTFS — includes roses
    {"id": "9", "name": "Línia 9", "color": "#795548", "stations": [
        "riba_roja","masia_traver","valencia_la_vella","la_presa","la_cova",
        "rosas","manises","salt_aigua","quart_poblet","faitanar","mislata_almassil",
        "mislata","nou_octubre","av_cid","angel_guimera","xativa","colon","alameda",
        "facultats","benimaclet","machado","alboraya_palmaret","alboraya_peris",
    ]},
    # L10: GTFS + 3 manual additions
    {"id": "10", "name": "Línia 10", "color": "#2ECC71", "stations": [
        "alacant","russafa","amado_granell","quatre_carreres","ciutat_arts",
        "oceanografic","moreres","natzaret",
    ]},
]

# ── COORDINATES (lat, lon) per station id ─────────────────────────────────────
# Sourced from OpenStreetMap. Stations shared between lines have one entry.
COORDS = {
    # From official MetroValencia GTFS (metrovalencia.es/google_transit_feed/google_transit.zip)
    "aeroport":           (39.4923668, -0.4749194),
    "alacant":            (39.4635830, -0.3773890),
    "alameda":            (39.4731560, -0.3653167),
    "albalat_sorells":    (39.5452652, -0.3482889),
    "alberic":            (39.1170502, -0.5235260),
    "alboraya_palmaret":  (39.4956627, -0.3552222),
    "alboraya_peris":     (39.5007629, -0.3523278),
    "alfauir":            (39.4892998, -0.3660330),
    "alginet":            (39.2629395, -0.4748860),
    "almassera":          (39.5122566, -0.3542667),
    "amado_granell":      (39.4593730, -0.3651100),
    "amistat":            (39.4703331, -0.3503945),
    "aragon":             (39.4726257, -0.3581167),
    "ausias_march_carlet":(39.2495575, -0.4919772),
    "av_cid":             (39.4682198, -0.3975750),
    "ayora":              (39.4664268, -0.3429694),
    "benaguasil":         (39.5988808, -0.5839278),
    "benicalap":          (39.4900284, -0.3909278),
    "beniferri":          (39.4910316, -0.3993369),
    "benimaclet":         (39.4848518, -0.3623333),
    "benimodo":           (39.2162933, -0.5196195),
    "benimamet":          (39.5018768, -0.4194111),
    "burjassot":          (39.5084152, -0.4067361),
    "burjassot_godella":  (39.5135307, -0.4119972),
    "betera":             (39.5906067, -0.4575306),
    "campament":          (39.4958458, -0.4353230),
    "campanar":           (39.4846306, -0.3950361),
    "campus":             (39.5072212, -0.4174583),
    "cantereria":         (39.5023804, -0.4120722),
    "carlet":             (39.2267990, -0.5249417),
    "castello":           (39.0840073, -0.5160139),
    "carolines_fira":     (39.4987373, -0.4254194),
    "ciudad_arts":        (39.4525920, -0.3532160),  # fallback
    "ciutat_arts":        (39.4525920, -0.3532160),
    "collegi_vedat":      (39.4231339, -0.4606528),
    "colon":              (39.4701462, -0.3709278),
    "dr_lluch":           (39.4693069, -0.3281528),
    "el_clot":            (39.5498657, -0.5279861),
    "empalme":            (39.4995766, -0.4021083),
    "entrepins":          (39.5433350, -0.5139540),
    "estadi_ciutat":      (39.4949188, -0.3655420),
    "facultats":          (39.4780045, -0.3619055),
    "faitanar":           (39.4776192, -0.4331833),
    "foios":              (39.5372238, -0.3538694),
    "font_almaguer":      (39.2894058, -0.4640861),
    "fuente_jarro":       (39.5111732, -0.4645167),
    "torre_virrey":       (39.5686646, -0.5419167),
    "garbi":              (39.4922905, -0.3945111),
    "godella":            (39.5195045, -0.4144556),
    "grau_marina":        (39.4631004, -0.3294720),
    "grau_canyamelar":    (39.4665222, -0.3279320),
    "horta_vella":        (39.5819321, -0.4431444),
    "jesus":              (39.4592018, -0.3845417),
    "eliana":             (39.5618324, -0.5359194),
    "la_cadena":          (39.4752045, -0.3293750),
    "la_canyada":         (39.5268059, -0.4871222),
    "la_carrasca":        (39.4796600, -0.3448250),
    "la_coma":            (39.5215721, -0.4317070),
    "la_vallesa":         (39.5378418, -0.4979778),
    "pobla_farnals":      (39.5794182, -0.3304361),
    "pobla_vallbona":     (39.5827637, -0.5622778),
    "lliria":             (39.6228409, -0.5902778),
    "machado":            (39.4924316, -0.3587945),
    "manises":            (39.4895897, -0.4590654),
    "maritim":            (39.4649391, -0.3382370),
    "mas_rosari":         (39.5249596, -0.4358250),
    "masies":             (39.5665817, -0.4053778),
    "masalaves":          (39.1438065, -0.5187611),
    "massamagrell":       (39.5705605, -0.3330333),
    "massarrojos":        (39.5366096, -0.4028778),
    "meliana":            (39.5280304, -0.3518195),
    "mislata":            (39.4738235, -0.4183055),
    "mislata_almassil":   (39.4760094, -0.4243695),
    "moncada_alfara":     (39.5435295, -0.3884611),
    "montesol":           (39.5555725, -0.5316972),
    "montortal":          (39.1737976, -0.5158861),
    "moreres":            (39.4501500, -0.3384080),
    "museros":            (39.5615768, -0.3408556),
    "natzaret":           (39.4498890, -0.3346740),
    "neptu":              (39.4632530, -0.3258508),
    "nou_octubre":        (39.4706573, -0.4076306),
    "oceanografic":       (39.4520380, -0.3473420),
    "omet":               (39.3532448, -0.4736870),
    "orriols":            (39.4931488, -0.3676636),
    "paiporta":           (39.4322624, -0.4180611),
    "palau_congressos":   (39.4971809, -0.4001417),
    "paterna":            (39.4988098, -0.4419720),
    "patraix":            (39.4564514, -0.3905083),
    "picanya":            (39.4331207, -0.4371583),
    "picassent":          (39.3630371, -0.4648583),
    "placa_espanya":      (39.4662018, -0.3816333),
    "pont_fusta":         (39.4817810, -0.3731806),
    "primat_reig":        (39.4862709, -0.3677639),
    "quart_poblet":       (39.4810867, -0.4418806),
    "quatre_carreres":    (39.4524470, -0.3601250),
    "rafelbunyol":        (39.5885239, -0.3310583),
    "realon":             (39.3939056, -0.4640138),
    "riba_roja":          (39.5433350, -0.5594444),
    "masia_traver":       (39.5380554, -0.5466667),
    "valencia_la_vella":  (39.5304832, -0.5342070),
    "la_presa":           (39.5172234, -0.5158333),
    "la_cova":            (39.4988899, -0.4844444),
    # L1 extra stations from GTFS
    "espioca":            (39.3218842, -0.4667472),
    "l_alcudia":          (39.1938133, -0.5102639),
    # L2 extra stations from GTFS
    "fondo_benaguasil":   (39.5927238, -0.5780805),
    "gallipont_torre_virrey": (39.5686646, -0.5419167),
    "font_barranc":       (39.5168998, -0.4716618),
    "ll_llarga":          (39.5098991, -0.4304472),
    # L4 Mas del Rosari branch
    "mas_rosari":         (39.5249596, -0.4358250),
    "la_coma":            (39.5215721, -0.4317070),
    "tomas_valiente":     (39.5197716, -0.4256361),
    "santa_gemma":        (39.5151405, -0.4226220),
    "a_punt":             (39.5122032, -0.4247490),
    "campus":             (39.5072212, -0.4174583),
    "sant_joan":          (39.5052910, -0.4163240),
    "la_granja":          (39.5040321, -0.4124780),
    # L7 Bailén
    "bailen":             (39.4639778, -0.3794222),
    # L9 roses (correct spelling)
    "rocafort":           (39.5287094, -0.4075778),
    "rosas":              (39.4926491, -0.4672361),
    "russafa":            (39.4639130, -0.3695310),
    "safranar":           (39.4545708, -0.3983833),
    "salt_aigua":         (39.4848328, -0.4505682),
    "sant_isidre":        (39.4510345, -0.4028028),
    "sant_joan":          (39.5052910, -0.4163240),
    "sant_miquel_reis":   (39.4972191, -0.3684950),
    "sant_ramon":         (39.3848648, -0.4672611),
    "santa_rita":         (39.5056572, -0.4551055),
    "seminari_ceu":       (39.5499878, -0.3897444),
    "tarongers":          (39.4781380, -0.3396222),
    "tomas_valiente":     (39.5197716, -0.4256361),
    "torrent":            (39.4346466, -0.4609861),
    "torrent_avinguda":   (39.4318123, -0.4728333),
    "tossal_rei":         (39.4959526, -0.3725370),
    "turia":              (39.4788666, -0.3912055),
    "univ_politecnica":   (39.4813156, -0.3505000),
    "valencia_sud":       (39.4408112, -0.4106472),
    "v_andres_estelles":  (39.5085602, -0.4198840),
    "vicent_andres":      (39.5085602, -0.4198840),
    "vicent_zaragoza":    (39.4833717, -0.3579472),
    "xativa":             (39.4671860, -0.3773750),
    "a_punt":             (39.5122032, -0.4247490),
    "angel_guimera":      (39.4703026, -0.3850361),
    "joaquin_sorolla":    (39.4639778, -0.3794222),  # Bailén/Joaquín Sorolla
    "serradora":          (39.4752045, -0.3293750),  # approx near La Cadena
    "eugenia_vines":      (39.4689293, -0.3257278),
    "les_arenes":         (39.4736900, -0.3257278),
    "mediterrani":        (39.4760094, -0.3060000),  # approx
    "tvv":                (39.5060000, -0.3960000),  # approx
    "santa_gemma":        (39.5151405, -0.4226220),
    # Real tram stations from GTFS
    "cabanyal":           (39.4728546, -0.3275833),
    "betero":             (39.4765930, -0.3342028),
    "tarongers":          (39.4781380, -0.3396222),
    "trinitat":           (39.4862709, -0.3677639),
    "sagunt":             (39.4864998, -0.3749722),
    "reus":               (39.4859657, -0.3817070),
    "marxalenes":         (39.4879723, -0.3838369),
    "transits":           (39.4895630, -0.3872583),
    "florista":           (39.4944344, -0.3968167),
    "la_granja":          (39.5040321, -0.4124780),
    "fira_valencia":      (39.5041428, -0.4254944),
    "platja_malva_rosa":  (39.4736900, -0.3257278),
    "platja_les_arenes":  (39.4689293, -0.3257278),
    "canyamelar":         (39.4665222, -0.3279320),
    "francesc_cubells":   (39.4632454, -0.3339730),
    "oceanografic":       (39.4520380, -0.3473420),
    "moreres":            (39.4501500, -0.3384080),
    "natzaret":           (39.4498890, -0.3346740),
}

# Station display names
NAMES = {
    "betera": "Bétera", "horta_vella": "Horta Vella", "masies": "Masies",
    "seminari_ceu": "Seminari-CEU", "moncada_alfara": "Moncada-Alfara",
    "massarrojos": "Massarrojos", "rocafort": "Rocafort", "godella": "Godella",
    "burjassot_godella": "Burjassot-Godella", "burjassot": "Burjassot",
    "empalme": "Empalme", "palau_congressos": "Palau de Congressos",
    "beniferri": "Beniferri", "campanar": "Campanar", "turia": "Túria",
    "angel_guimera": "Àngel Guimerà", "placa_espanya": "Plaça Espanya",
    "joaquin_sorolla": "Joaquín Sorolla", "jesus": "Jesús", "patraix": "Patraix",
    "safranar": "Safranar", "sant_isidre": "Sant Isidre", "valencia_sud": "València Sud",
    "paiporta": "Paiporta", "picanya": "Picanya", "torrent": "Torrent",
    "collegi_vedat": "Col·legi El Vedat", "realon": "Realón", "sant_ramon": "Sant Ramon",
    "picassent": "Picassent", "omet": "Omet", "font_almaguer": "Font Almaguer",
    "alginet": "Alginet", "ausias_march_carlet": "Ausiàs March", "carlet": "Carlet",
    "benimodo": "Benimodo", "montortal": "Montortal", "masalaves": "Masalavés",
    "alberic": "Alberic", "castello": "Castelló",
    "lliria": "Llíria", "benaguasil": "Benaguasil", "pobla_vallbona": "La Pobla de Vallbona",
    "torre_virrey": "Torre del Virrey", "eliana": "L'Eliana", "montesol": "Montesol",
    "el_clot": "El Clot", "entrepins": "Entrepins", "la_vallesa": "La Vallesa",
    "la_canyada": "La Canyada", "fuente_jarro": "Fuente del Jarro", "santa_rita": "Santa Rita",
    "paterna": "Paterna", "campament": "Campament", "carolines_fira": "Les Carolines-Fira",
    "benimamet": "Benimàmet", "cantereria": "Cantereria", "torrent_avinguda": "Torrent Avinguda",
    "rafelbunyol": "Rafelbunyol", "pobla_farnals": "La Pobla de Farnals",
    "massamagrell": "Massamagrell", "museros": "Museros", "albalat_sorells": "Albalat dels Sorells",
    "foios": "Foios", "meliana": "Meliana", "almassera": "Almàssera",
    "alboraya_peris": "Alboraya-Peris Aragó", "alboraya_palmaret": "Alboraya-Palmaret",
    "machado": "Machado", "benimaclet": "Benimaclet", "facultats": "Facultats",
    "alameda": "Alameda", "colon": "Colón", "xativa": "Xàtiva",
    "av_cid": "Av. del Cid", "nou_octubre": "Nou d'Octubre", "mislata": "Mislata",
    "mislata_almassil": "Mislata-Almassil", "faitanar": "Faitanar",
    "quart_poblet": "Quart de Poblet", "manises": "Manises", "salt_aigua": "Salt de l'Aigua",
    "rosas": "Rosas", "aeroport": "Aeroport",
    "mas_rosari": "Mas del Rosari", "la_coma": "La Coma", "tomas_valiente": "Tomás y Valiente",
    "santa_gemma": "Santa Gemma-Parc Científic UV", "tvv": "TVV",
    "v_andres_estelles": "V. Andrés Estellés", "a_punt": "À Punt", "campus": "Campus",
    "sant_joan": "Sant Joan", "vicent_andres": "Vicent Andrés Estellés",
    "benicalap": "Benicalap", "garbi": "Garbí", "pont_fusta": "Pont de Fusta",
    "primat_reig": "Primat Reig", "vicent_zaragoza": "Vicente Zaragozá",
    "univ_politecnica": "Universitat Politècnica", "la_carrasca": "La Carrasca",
    "tarongers": "Tarongers", "serradora": "Serradora", "la_cadena": "La Cadena",
    "eugenia_vines": "Eugènia Viñes", "les_arenes": "Les Arenes",
    "mediterrani": "Mediterrani", "grau_marina": "Grau-La Marina", "dr_lluch": "Dr. Lluch",
    "maritim": "Marítim", "ayora": "Ayora", "amistat": "Amistat", "aragon": "Aragón",
    "tossal_rei": "Tossal del Rei", "sant_miquel_reis": "Sant Miquel dels Reis",
    "estadi_ciutat": "Estadi Ciutat de València", "orriols": "Orriols", "alfauir": "Alfauir",
    "grau_canyamelar": "Grau-Canyamelar", "neptu": "Neptú",
    "riba_roja": "Riba-roja de Túria",
    "natzaret": "Natzaret", "moreres": "Moreres", "quatre_carreres": "Quatre Carreres",
    "ciutat_arts": "Ciutat de les Arts i les Ciències", "oceanografic": "Oceanogràfic",
    "amado_granell": "Amado Granell-Montolivet", "russafa": "Russafa", "alacant": "Alacant",
    "cabanyal": "Cabanyal", "betero": "Beteró", "tarongers": "Tarongers - Ernest Lluch",
    "trinitat": "Trinitat", "sagunt": "Sagunt", "reus": "Reus",
    "marxalenes": "Marxalenes", "transits": "Trànsits", "florista": "Florista",
    "la_granja": "La Granja", "fira_valencia": "Fira València",
    "platja_malva_rosa": "Platja Malva-rosa", "platja_les_arenes": "Platja les Arenes",
    "canyamelar": "Canyamelar", "francesc_cubells": "Francesc Cubells",
    "oceanografic": "Oceanogràfic", "moreres": "Moreres", "natzaret": "Natzaret",
    "masia_traver": "Masia de Traver", "valencia_la_vella": "València la Vella",
    "la_presa": "La Presa", "la_cova": "La Cova",
    "espioca": "Espioca", "l_alcudia": "L'Alcúdia",
    "fondo_benaguasil": "Fondo de Benaguasil", "gallipont_torre_virrey": "Gallipont - Torre del Virrey",
    "font_barranc": "Font del Barranc", "ll_llarga": "Ll. Llarga - Terramelar",
    "bailen": "Bailén",
    "mas_rosari": "Mas del Rosari", "la_coma": "La Coma",
    "tomas_valiente": "Tomás y Valiente", "santa_gemma": "Santa Gemma-Parc Científic UV",
    "a_punt": "À Punt", "campus": "Campus", "sant_joan": "Sant Joan", "la_granja": "La Granja",
}


def build_station_lines():
    """Build {station_id: [line_ids]} from LINES_DEF. Sub-lines (4b,4c) count as their parent."""
    result = {}
    for line in LINES_DEF:
        # Normalize: 4b→4, 4c→4
        display_id = line["id"].rstrip("abcdefgh")
        for sid in line["stations"]:
            result.setdefault(sid, [])
            if display_id not in result[sid]:
                result[sid].append(display_id)
    return result


async def seed():
    db = firestore.AsyncClient(project=PROJECT_ID)
    
    # Clear existing data
    print("Clearing existing stations...")
    stations_ref = db.collection("metro_stations")
    async for doc in stations_ref.stream():
        await doc.reference.delete()
    
    print("Clearing existing lines...")
    lines_ref = db.collection("metro_lines")
    async for doc in lines_ref.stream():
        await doc.reference.delete()
    
    station_lines = build_station_lines()

    # Build station docs
    stations = []
    for sid, lines in station_lines.items():
        if sid not in COORDS:
            print(f"  WARNING: no coords for {sid}")
            continue
        lat, lon = COORDS[sid]
        stations.append({
            "id": sid,
            "name": NAMES.get(sid, sid),
            "lat": lat,
            "lon": lon,
            "lines": sorted(lines, key=lambda x: int(x.rstrip("abcd"))),
        })

    print(f"Seeding {len(stations)} stations...")
    for st in stations:
        await db.collection("metro_stations").document(st["id"]).set(st)

    print(f"Seeding {len(LINES_DEF)} lines...")
    for line in LINES_DEF:
        # Normalize: 4b→4, 4c→4, 4d→4 (remove trailing letters)
        display_id = line["id"].rstrip("abcdefgh")
        await db.collection("metro_lines").document(line["id"]).set({
            "id": display_id,
            "name": line["name"],
            "color": line["color"],
            "station_ids": line["stations"],
        })

    print("✅ Seed complete!")
    # Print verification for key stations
    for sid in ["colon", "angel_guimera", "xativa", "benimaclet", "alameda"]:
        print(f"  {NAMES[sid]}: lines {station_lines.get(sid, [])}")


if __name__ == "__main__":
    asyncio.run(seed())
