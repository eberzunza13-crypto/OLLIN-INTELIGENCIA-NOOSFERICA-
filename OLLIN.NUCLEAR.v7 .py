#!/usr/bin/env python3
"""
OLLIN SISTEMA NUCLEAR NOOSFÉRICO v7
Arquitectura Orbital Dual con Cámara de Diálogo (grupos/subgrupos),
activación por contexto (MoE sin pesos), Blind Spot Detector,
MECP integrada y acumulación sin jerarquías.
LEBD – Luis Ernesto Berzunza Díaz
"""

import os
import sys
import json
import hashlib
import subprocess
import re
import threading
import time
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# ----------------------------------------------------------------------
# Importaciones opcionales
# ----------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠ No se pudo importar sentence-transformers o numpy.")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from PIL import Image
    from transformers import BlipProcessor, BlipForConditionalGeneration
    BLIP_AVAILABLE = True
except ImportError:
    BLIP_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from flask import Flask, render_template, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from colorama import init, Fore, Style
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore: RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style: BRIGHT = DIM = NORMAL = RESET_ALL = ''

# ----------------------------------------------------------------------
# Configuración de rutas (ahora incluye MECP)
# ----------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/ollin_nuclear")
AHO_DIR = os.path.join(BASE_DIR, "aho")
SUENO_DIR = os.path.join(AHO_DIR, "sueno")
MITOTE_DIR = os.path.join(AHO_DIR, "mitote")
OMETEOTL_DIR = os.path.join(AHO_DIR, "ometeotl")
OMETEOTL_CONOCIDO = os.path.join(OMETEOTL_DIR, "conocido")
OMETEOTL_BUSCADO = os.path.join(OMETEOTL_DIR, "buscado")
OMETEOTL_DUAL = os.path.join(OMETEOTL_DIR, "dual")
OLLIN_DIR = os.path.join(AHO_DIR, "ollin")
OLLIN_ORBITA = os.path.join(OLLIN_DIR, "orbita")
OLLIN_ESTADOS = os.path.join(OLLIN_DIR, "estados")
OLLIN_DUAL = os.path.join(OLLIN_DIR, "dual")
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")
PRINCIPIOS_DB = os.path.join(BASE_DIR, "principios_violaciones.db")
MECP_DIR = os.path.join(BASE_DIR, "mecp")  # Memoria Episódica Contextual Portable
os.makedirs(MECP_DIR, exist_ok=True)

for d in [SUENO_DIR, MITOTE_DIR, OMETEOTL_CONOCIDO, OMETEOTL_BUSCADO, OMETEOTL_DUAL,
          OLLIN_ORBITA, OLLIN_ESTADOS, OLLIN_DUAL, PROYECTOS_DIR, MECP_DIR]:
    os.makedirs(d, exist_ok=True)

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

MEMORIA_DIR = os.path.expanduser("~/.ollin")
MEMORIA_ARCHIVO = os.path.join(MEMORIA_DIR, "contexto.json")
os.makedirs(MEMORIA_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Bases de datos
# ----------------------------------------------------------------------
def init_principios_db():
    conn = sqlite3.connect(PRINCIPIOS_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS violaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo_id TEXT,
            principio TEXT,
            descripcion TEXT,
            timestamp TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS estadisticas (
            principio TEXT PRIMARY KEY,
            total_violaciones INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_principios_db()

# ----------------------------------------------------------------------
# Modelo de embeddings (multilingüe)
# ----------------------------------------------------------------------
modelo_embeddings = None
if EMBEDDINGS_AVAILABLE:
    try:
        modelo_embeddings = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        print("✓ Modelo de embeddings multilingüe cargado (512 dimensiones)")
    except Exception as e:
        print(f"⚠ Error cargando modelo multilingüe: {e}. Usando all-MiniLM-L6-v2.")
        try:
            modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            print("✓ Modelo de embeddings cargado (384 dimensiones)")
        except Exception as e2:
            print(f"⚠ Error cargando modelo: {e2}")
            modelo_embeddings = None

# ----------------------------------------------------------------------
# ChromaDB
# ----------------------------------------------------------------------
chroma_client = None
collection = None
if CHROMADB_AVAILABLE:
    try:
        chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
        collection = chroma_client.get_or_create_collection("ollin_nodos")
        print("✓ ChromaDB activo (búsqueda semántica disponible)")
    except Exception as e:
        print(f"⚠ Error inicializando ChromaDB: {e}")

# ----------------------------------------------------------------------
# Utilidades generales
# ----------------------------------------------------------------------
def generar_hash(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()[:16]

def ahora():
    return datetime.now().isoformat()

def colorize(texto, color=None, estilo=None):
    if not COLORS_AVAILABLE:
        return texto
    if color:
        texto = getattr(Fore, color.upper(), '') + texto
    if estilo:
        texto = getattr(Style, estilo.upper(), '') + texto
    texto += Style.RESET_ALL
    return texto

# ----------------------------------------------------------------------
# Capa AntiBias 00 (inmutable)
# ----------------------------------------------------------------------
def aplicar_capa_antibias(texto: str, fuente: str, etiqueta: str) -> Dict:
    idioma = "es" if any(c in "áéíóúñ" for c in texto.lower()) else "en"
    estado = "factual" if len(texto.split()) < 50 else "descriptivo"
    sesgos = []
    if "debería" in texto.lower() or "tiene que" in texto.lower():
        sesgos.append("prescriptivo")
    if "siempre" in texto.lower() or "nunca" in texto.lower():
        sesgos.append("absolutista")
    evidencia = "empírica" if any(w in texto.lower() for w in ["estudio", "dato", "según", "investigación"]) else "cualitativa"
    return {
        "texto_original": texto,
        "fuente": fuente,
        "etiqueta": etiqueta,
        "idioma": idioma,
        "estado_epistemico": estado,
        "sesgos_detectados": sesgos,
        "tipo_evidencia": evidencia,
        "fecha_procesamiento": ahora()
    }

# ----------------------------------------------------------------------
# Nodos con acumulación
# ----------------------------------------------------------------------
def crear_nodo(texto: str, fuente: str, etiqueta: str, metadata: Dict = None) -> Tuple[str, Dict, Dict]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nodo_id = f"{timestamp}_{generar_hash(texto[:50])}"
    nodo_sueno = {
        "id": nodo_id,
        "tipo": "sueno",
        "conocido": {
            "descripcion": texto,
            "fuente": fuente,
            "etiqueta": etiqueta,
            "fecha": ahora(),
            "hash": generar_hash(texto + fuente),
            "adiciones": [],
            "epistemic_status": metadata.get("estado_epistemico", "no_verificado") if metadata else "no_verificado",
            "sesgos": metadata.get("sesgos_detectados", []) if metadata else [],
            "evidencia": metadata.get("tipo_evidencia", "cualitativa") if metadata else "cualitativa"
        }
    }
    nodo_mitote = {
        "id": nodo_id,
        "tipo": "mitote",
        "buscado": {
            "preguntas": [],
            "sugerencias": [],
            "analisis": None,
            "historial_analisis": []
        }
    }
    return nodo_id, nodo_sueno, nodo_mitote

def guardar_nodo(nodo_id: str, nodo_sueno: Dict, nodo_mitote: Dict):
    with open(os.path.join(SUENO_DIR, f"{nodo_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(nodo_sueno, f, ensure_ascii=False, indent=2)
    with open(os.path.join(MITOTE_DIR, f"{nodo_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(nodo_mitote, f, ensure_ascii=False, indent=2)

def cargar_nodo_sueno(nodo_id: str) -> Optional[Dict]:
    path = os.path.join(SUENO_DIR, f"{nodo_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_nodo_mitote(nodo_id: str) -> Optional[Dict]:
    path = os.path.join(MITOTE_DIR, f"{nodo_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def actualizar_nodo_con_adiciones(nodo_id: str, texto_nuevo: str, fuente_nueva: str, metadata: Dict = None):
    nodo = cargar_nodo_sueno(nodo_id)
    if not nodo:
        return False
    adicion = {
        "texto": texto_nuevo,
        "fuente": fuente_nueva,
        "fecha": ahora(),
        "hash": generar_hash(texto_nuevo + fuente_nueva),
        "epistemic_status": metadata.get("estado_epistemico", "no_verificado") if metadata else "no_verificado",
        "sesgos": metadata.get("sesgos_detectados", []) if metadata else [],
        "evidencia": metadata.get("tipo_evidencia", "cualitativa") if metadata else "cualitativa"
    }
    nodo["conocido"]["adiciones"].append(adicion)
    with open(os.path.join(SUENO_DIR, f"{nodo_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(nodo, f, ensure_ascii=False, indent=2)
    return True

# ----------------------------------------------------------------------
# Ometeotl y OLLIN (registros)
# ----------------------------------------------------------------------
def registrar_en_ometeotl(nodo_id: str, tipo: str, datos: Dict, vector=None):
    if tipo == "sueno":
        path = os.path.join(OMETEOTL_CONOCIDO, f"{nodo_id}.json")
    elif tipo == "mitote":
        path = os.path.join(OMETEOTL_BUSCADO, f"{nodo_id}.json")
    else:
        return
    if vector is None:
        dim = 512 if modelo_embeddings and hasattr(modelo_embeddings, 'get_sentence_embedding_dimension') else 384
        vector = [0.0]*dim
    else:
        if hasattr(vector, 'tolist'):
            vector = vector.tolist()
    registro = {
        "id": nodo_id,
        "tipo": tipo,
        "fecha": ahora(),
        "hash_original": datos.get("hash", ""),
        "vector": vector[:]
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

def actualizar_dual_ometeotl(nodo_id: str, vector_sueno, vector_mitote):
    if vector_sueno is None or vector_mitote is None:
        diff = [0.0]*384
        norma = 0.0
    else:
        if not isinstance(vector_sueno, np.ndarray):
            vector_sueno = np.array(vector_sueno)
        if not isinstance(vector_mitote, np.ndarray):
            vector_mitote = np.array(vector_mitote)
        diff = (vector_sueno - vector_mitote).tolist()
        norma = float(np.linalg.norm(vector_sueno - vector_mitote))
    registro_dual = {
        "id": nodo_id,
        "fecha": ahora(),
        "diferencia": diff,
        "norma_diferencia": norma,
        "equilibrio": "ok" if norma < 0.5 else "desbalanceado"
    }
    with open(os.path.join(OMETEOTL_DUAL, f"{nodo_id}.json"), 'w') as f:
        json.dump(registro_dual, f, ensure_ascii=False, indent=2)

def registrar_orbita(ciclo: str, nodo_id: str, accion: str):
    registro = {
        "ciclo": ciclo,
        "nodo": nodo_id,
        "accion": accion,
        "fecha": ahora(),
        "hash": generar_hash(ciclo + nodo_id + accion)
    }
    with open(os.path.join(OLLIN_ORBITA, f"{ciclo}_{nodo_id}.json"), 'w') as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

def guardar_estado_ollin(estado: Dict):
    with open(os.path.join(OLLIN_ESTADOS, f"{estado['id']}.json"), 'w') as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

def actualizar_dual_ollin(estado_actual: Dict, estado_dual: Dict):
    dual = {
        "fecha": ahora(),
        "estado_actual": estado_actual.get("hash", ""),
        "estado_dual": estado_dual.get("hash", ""),
        "diferencia": "simétrica"
    }
    with open(os.path.join(OLLIN_DUAL, f"{estado_actual['id']}.json"), 'w') as f:
        json.dump(dual, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------
# Cámara de Diálogo (grupos, subgrupos, MoE contextual)
# ----------------------------------------------------------------------
class CamaraDialogo:
    """
    Grupos de pensamiento con subgrupos de sabios vivos y fallecidos.
    Activación por palabras clave (MoE sin pesos).
    """
    def __init__(self, ollama_interface):
        self.ollama = ollama_interface
        self.grupos = self._cargar_grupos()

    def _cargar_grupos(self) -> Dict:
        return {
            "geopolitica": {
                "keywords": ["geopolítica", "conflicto", "guerra", "fronteras", "hegemonía", "imperio", "nación", "territorio"],
                "descripcion": "Análisis de relaciones internacionales, poder territorial y geopolítica global.",
                "subgrupos": {
                    "vivos": ["Noam Chomsky", "John Mearsheimer", "Zbigniew Brzezinski", "Henry Kissinger"],
                    "fallecidos": ["Carl von Clausewitz", "Sun Tzu", "Maquiavelo"]
                }
            },
            "economia": {
                "keywords": ["economía", "mercado", "capitalismo", "deuda", "inflación", "trabajo", "finanzas"],
                "descripcion": "Economía política, macroeconomía, sistemas económicos.",
                "subgrupos": {
                    "vivos": ["Yanis Varoufakis", "Thomas Piketty", "Mariana Mazzucato", "Joseph Stiglitz"],
                    "fallecidos": ["Karl Marx", "Adam Smith", "John Maynard Keynes"]
                }
            },
            "filosofia": {
                "keywords": ["filosofía", "ética", "existencia", "conocimiento", "verdad", "sentido"],
                "descripcion": "Reflexión filosófica sobre supuestos y valores.",
                "subgrupos": {
                    "vivos": ["Judith Butler", "Slavoj Žižek", "Byung-Chul Han", "Martha Nussbaum"],
                    "fallecidos": ["Sócrates", "Friedrich Nietzsche", "Simone de Beauvoir"]
                }
            },
            "ecologia": {
                "keywords": ["ecología", "clima", "medio ambiente", "sostenibilidad", "recursos", "biosfera"],
                "descripcion": "Perspectivas ecológicas y ambientales.",
                "subgrupos": {
                    "vivos": ["Vandana Shiva", "Naomi Klein", "James Lovelock", "Timothy Morton"],
                    "fallecidos": ["Rachel Carson", "Aldo Leopold"]
                }
            },
            "arte": {
                "keywords": ["arte", "cultura", "estética", "creación", "expresión", "música", "pintura"],
                "descripcion": "Arte como fuente de conocimiento y crítica.",
                "subgrupos": {
                    "vivos": ["Frida Kahlo", "Banksy", "Ai Weiwei", "Marina Abramović"],
                    "fallecidos": ["Leonardo da Vinci", "Vincent van Gogh", "Mozart"]
                }
            },
            "ciencia": {
                "keywords": ["ciencia", "tecnología", "investigación", "método", "innovación", "física", "biología"],
                "descripcion": "Epistemología científica y avances tecnológicos.",
                "subgrupos": {
                    "vivos": ["Donna Haraway", "Stephen Hawking", "Richard Dawkins", "Mario Molina"],
                    "fallecidos": ["Galileo Galilei", "Isaac Newton", "Albert Einstein", "Marie Curie"]
                }
            },
            "indigena": {
                "keywords": ["indígena", "originario", "cosmovisión", "territorio", "tradición", "ancestral"],
                "descripcion": "Saberes ancestrales y perspectivas indígenas.",
                "subgrupos": {
                    "vivos": ["Winona LaDuke", "Ailton Krenak", "Rigoberta Menchú"],
                    "fallecidos": ["Nezahualcóyotl", "Pachacútec", "Tupac Amaru"]
                }
            },
            "feminismo": {
                "keywords": ["feminismo", "género", "patriarcado", "mujeres", "interseccionalidad", "disidencia"],
                "descripcion": "Teorías feministas y estudios de género.",
                "subgrupos": {
                    "vivos": ["Judith Butler", "Silvia Federici", "Angela Davis", "Rita Segato"],
                    "fallecidos": ["Simone de Beauvoir", "Virginia Woolf", "Audre Lorde"]
                }
            }
        }

    def grupos_relevantes(self, texto: str) -> List[str]:
        """Devuelve lista de grupos cuyas keywords aparecen en el texto."""
        texto_low = texto.lower()
        return [nombre for nombre, info in self.grupos.items()
                if any(kw in texto_low for kw in info["keywords"])]

    def deliberar(self, tema: str, preguntas_previas: List[str] = None) -> Dict:
        """Activa grupos relevantes y obtiene su voz colectiva."""
        grupos_act = self.grupos_relevantes(tema)
        if not grupos_act:
            grupos_act = ["filosofia", "ciencia"]  # fallback
        resultados = {}
        for grupo in grupos_act:
            info = self.grupos[grupo]
            # Construir prompt con subgrupos
            vivos = ", ".join(info["subgrupos"]["vivos"])
            fallecidos = ", ".join(info["subgrupos"]["fallecidos"])
            prompt = f"""
Eres un grupo de pensamiento que representa la perspectiva **{grupo}** ({info['descripcion']}).

Subgrupo de sabios vivos: {vivos}
Subgrupo de sabios fallecidos (sus ideas trascienden): {fallecidos}

Sobre el tema: "{tema}"
Preguntas previas: {preguntas_previas if preguntas_previas else 'ninguna'}

Genera una **voz colectiva** que sintetice el análisis de este grupo.
Incluye:
- Una breve síntesis del grupo sobre el tema.
- 2-3 preguntas clave que este grupo considera esenciales.
- 1-2 advertencias sobre posibles sesgos o faltantes.

Devuelve solo el texto de la deliberación, sin encabezados.
"""
            respuesta = self.ollama._llamar_ollama(prompt)
            resultados[grupo] = respuesta
        return resultados

    def verificar_dimensiones_faltantes(self, tema: str, grupos_activos: List[str]) -> List[str]:
        """Revisa si hay grupos no activados que podrían ser relevantes."""
        todos = list(self.grupos.keys())
        faltantes = [g for g in todos if g not in grupos_activos]
        if not faltantes:
            return []
        # Opcional: preguntar al sistema si alguna dimensión faltante es crítica
        prompt = f"""
Tema: "{tema}"
Grupos ya considerados: {', '.join(grupos_activos)}
Grupos no considerados: {', '.join(faltantes)}

¿Algún grupo no considerado podría aportar una perspectiva crucial que cambie el análisis?
Responde solo con los nombres de los grupos que son imprescindibles, separados por coma. Si ninguno, responde "NINGUNO".
"""
        respuesta = self.ollama._llamar_ollama(prompt)
        if respuesta.strip().upper() != "NINGUNO":
            criticos = [g.strip() for g in respuesta.split(',') if g.strip() in faltantes]
            return criticos
        return []

# ----------------------------------------------------------------------
# Motor Dialéctico (sintetiza tesis y antítesis)
# ----------------------------------------------------------------------
class MotorDialectico:
    def __init__(self, ollama_interface):
        self.ollama = ollama_interface

    def sintetizar(self, tesis: str, antitesis: str) -> str:
        prompt = f"""
Actúa como un motor dialéctico. Dadas las siguientes tesis y antítesis, genera una síntesis que integre lo mejor de ambas,
señalando contradicciones y proponiendo una perspectiva superadora.

Tesis: {tesis}
Antítesis: {antitesis}

Síntesis:
"""
        return self.ollama._llamar_ollama(prompt)

# ----------------------------------------------------------------------
# Generador de Hipótesis con seguimiento
# ----------------------------------------------------------------------
class GeneradorHipotesis:
    def __init__(self, ollama_interface):
        self.ollama = ollama_interface
        self.hipotesis_db = os.path.join(BASE_DIR, "hipotesis.json")
        self.hipotesis = self._cargar()

    def _cargar(self) -> List[Dict]:
        if os.path.exists(self.hipotesis_db):
            with open(self.hipotesis_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _guardar(self):
        with open(self.hipotesis_db, 'w', encoding='utf-8') as f:
            json.dump(self.hipotesis, f, ensure_ascii=False, indent=2)

    def generar_para_tema(self, tema: str) -> List[str]:
        prompt = f"""
Eres un científico generador de hipótesis. Genera 3 hipótesis sobre el siguiente tema,
que sean novedosas, contrastables y relevantes para entender el fenómeno.
Cada hipótesis debe ser una frase concisa.

Tema: {tema}
"""
        respuesta = self.ollama._llamar_ollama(prompt)
        lineas = [l.strip() for l in respuesta.split('\n') if l.strip()]
        hipotesis = [l for l in lineas if '?' not in l][:3]
        for h in hipotesis:
            self.hipotesis.append({
                "texto": h,
                "fecha": ahora(),
                "estado": "pendiente",
                "tema": tema
            })
        self._guardar()
        return hipotesis

    def verificar_hipotesis(self, hipotesis_texto: str, nueva_evidencia: str) -> str:
        prompt = f"""
Evalúa la siguiente hipótesis con la nueva evidencia proporcionada.
Determina si la hipótesis es corroborada, refutada o sigue siendo incierta.
Explica brevemente.

Hipótesis: {hipotesis_texto}
Nueva evidencia: {nueva_evidencia}
"""
        resultado = self.ollama._llamar_ollama(prompt)
        for h in self.hipotesis:
            if h["texto"] == hipotesis_texto:
                h["estado"] = "verificada" if "corroborada" in resultado else ("refutada" if "refutada" in resultado else "incierta")
                h["ultima_evaluacion"] = resultado
                h["fecha_evaluacion"] = ahora()
                self._guardar()
                break
        return resultado

# ----------------------------------------------------------------------
# World Model (base simple de datos globales)
# ----------------------------------------------------------------------
class WorldModel:
    def __init__(self):
        self.data = self._cargar()

    def _cargar(self) -> Dict:
        return {
            "indicadores": {
                "pib_mundial": "~105 billones USD (2024)",
                "poblacion_mundial": "8.1 mil millones",
                "co2_atmosferico": "~420 ppm",
                "temperatura_global": "+1.2°C sobre niveles preindustriales"
            },
            "conflictos": [
                {"nombre": "Guerra en Ucrania", "inicio": "2022", "estado": "activo"},
                {"nombre": "Conflicto Israel-Palestina", "inicio": "1948", "estado": "activo"},
                {"nombre": "Crisis en Sudán", "inicio": "2023", "estado": "activo"}
            ],
            "economias": {
                "deuda_global": "~307 billones USD",
                "inflacion_mundial": "~5.8% (2024)"
            }
        }

    def consultar(self, tema: str) -> str:
        tema_low = tema.lower()
        if "pib" in tema_low or "economía" in tema_low:
            return f"PIB mundial: {self.data['indicadores']['pib_mundial']}. Deuda global: {self.data['economias']['deuda_global']}."
        elif "clima" in tema_low or "co2" in tema_low:
            return f"CO₂ atmosférico: {self.data['indicadores']['co2_atmosferico']}. Temperatura global: {self.data['indicadores']['temperatura_global']}."
        elif "conflicto" in tema_low or "guerra" in tema_low:
            conflictos = ", ".join([c["nombre"] for c in self.data["conflictos"]])
            return f"Conflictos activos destacados: {conflictos}."
        else:
            return "No hay datos específicos en el modelo para este tema."

# ----------------------------------------------------------------------
# MECP (Memoria Episódica Contextual Portable) integrada
# ----------------------------------------------------------------------
class MECP:
    def __init__(self, proyecto="default"):
        self.proyecto = proyecto
        self.modo = self._cargar_modo()
        self.episodios_dir = os.path.join(MECP_DIR, proyecto, "episodios")
        self.contexto_path = os.path.join(MECP_DIR, proyecto, "contexto.json")
        os.makedirs(self.episodios_dir, exist_ok=True)

    def _cargar_modo(self):
        path = os.path.join(MECP_DIR, self.proyecto, "config.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f).get("modo", "EPISODICO")
        return "EPISODICO"

    def set_modo(self, modo):
        path = os.path.join(MECP_DIR, self.proyecto, "config.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"modo": modo}, f)
        self.modo = modo

    def registrar_nodo(self, nodo: Dict):
        if self.modo == "FUGAZ":
            return
        hoy = datetime.now().strftime("%Y-%m-%d")
        archivo = os.path.join(self.episodios_dir, f"{hoy}.json")
        if os.path.exists(archivo):
            with open(archivo, 'r') as f:
                data = json.load(f)
        else:
            data = {"fecha": hoy, "modo": self.modo, "nodos": []}
        data["nodos"].append(nodo)
        with open(archivo, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if self.modo == "CICLICO":
            self._rotar()

    def _rotar(self):
        archivos = sorted([f for f in os.listdir(self.episodios_dir) if f.endswith('.json')])
        max_ciclos = 100  # configurable
        if len(archivos) > max_ciclos:
            for arch in archivos[:-max_ciclos]:
                os.remove(os.path.join(self.episodios_dir, arch))

    def exportar_contexto(self, n_ultimos=10) -> str:
        """Genera el prompt de contexto para inyectar en cualquier modelo."""
        episodios = sorted([f for f in os.listdir(self.episodios_dir) if f.endswith('.json')], reverse=True)
        nodos = []
        for ep in episodios:
            with open(os.path.join(self.episodios_dir, ep), 'r') as f:
                data = json.load(f)
                nodos.extend(data.get("nodos", []))
                if len(nodos) >= n_ultimos:
                    break
        nodos = nodos[-n_ultimos:]
        contexto = f"[INICIO_CONTEXTO]\nProyecto: {self.proyecto}\nModo: {self.modo}\n"
        for n in nodos:
            contexto += f"[{n.get('timestamp', '')}] {n.get('tipo', '')}: {n.get('texto', '')}\n"
        contexto += "[FIN_CONTEXTO]\n\nContinuar desde este punto:"
        return contexto

# ----------------------------------------------------------------------
# GapHunter unificado (usa Cámara, Dialéctica, Hipótesis, MECP)
# ----------------------------------------------------------------------
class GapHunter:
    def __init__(self):
        self.modelos = self._listar_modelos()
        self.modelo_principal = self.modelos[0] if self.modelos else None
        self.verificador = PrincipiosVerificador()
        self.camara = CamaraDialogo(self)
        self.dialectica = MotorDialectico(self)
        self.hipotesis_gen = GeneradorHipotesis(self)
        self.world = WorldModel()
        self.mecp = MECP()

    def _listar_modelos(self) -> List[str]:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            lineas = result.stdout.strip().split('\n')[1:]
            return [l.split()[0] for l in lineas if l.strip()]
        except:
            return []

    def _llamar_ollama(self, prompt: str, modelo: str = None) -> str:
        modelo_usar = modelo or self.modelo_principal
        if not modelo_usar:
            return ""
        try:
            cmd = ["ollama", "run", modelo_usar, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.stdout.strip()
        except Exception as e:
            return f"[Error: {e}]"

    def _generar_preguntas_mayeuticas(self, texto: str) -> List[str]:
        if not self.modelo_principal:
            return []
        prompt = f"Eres un filósofo socrático. Aplica la mayéutica para generar 3 preguntas que cuestionen el texto:\n{texto[:1000]}"
        respuesta = self._llamar_ollama(prompt)
        return [l.strip() for l in respuesta.split('\n') if l.strip() and '?' in l][:3]

    def _generar_preguntas_hermeneuticas(self, texto: str) -> List[str]:
        if not self.modelo_principal:
            return []
        prompt = f"Eres un hermeneuta. Genera 3 preguntas contextuales para interpretar el texto:\n{texto[:1000]}"
        respuesta = self._llamar_ollama(prompt)
        return [l.strip() for l in respuesta.split('\n') if l.strip() and '?' in l][:3]

    def analizar_con_filosofia(self, texto: str) -> Tuple[List[str], List[str]]:
        # 1. Preguntas mayéuticas y hermenéuticas
        may = self._generar_preguntas_mayeuticas(texto)
        her = self._generar_preguntas_hermeneuticas(texto)

        # 2. Deliberación de la Cámara de Diálogo
        deliberacion = self.camara.deliberar(texto)
        preguntas_camara = []
        for grupo, resp in deliberacion.items():
            # extraer preguntas de la respuesta
            for linea in resp.split('\n'):
                if '?' in linea:
                    preguntas_camara.append(linea.strip())

        # 3. Verificar dimensiones faltantes
        grupos_act = self.camara.grupos_relevantes(texto)
        faltantes = self.camara.verificar_dimensiones_faltantes(texto, grupos_act)
        if faltantes:
            # Si hay dimensiones críticas faltantes, las incluimos
            preguntas_faltantes = [f"¿Qué aportaría la perspectiva de {g} a este análisis?" for g in faltantes]
            preguntas_camara.extend(preguntas_faltantes)

        # 4. Unir todas las preguntas (sin duplicados)
        todas = list(dict.fromkeys(may + her + preguntas_camara))
        if len(todas) < 3:
            todas.extend(["¿Qué implicaciones tiene este contenido?", "¿Qué perspectivas quedan excluidas?"])

        # 5. Generar hipótesis y sugerencias
        hipotesis = self.hipotesis_gen.generar_para_tema(texto[:200])
        sugerencias = [f"Hipótesis: {h}" for h in hipotesis] if hipotesis else []
        datos_world = self.world.consultar(texto[:100])
        if datos_world:
            sugerencias.append(f"Datos del modelo mundial: {datos_world}")

        return todas[:5], sugerencias[:5]

    def procesar_nodo(self, nodo_sueno: Dict, corregir_principios=True) -> Dict:
        texto = nodo_sueno["conocido"]["descripcion"]
        preguntas, sugerencias = self.analizar_con_filosofia(texto)

        if corregir_principios:
            faltantes = self.verificador.verificar(texto, preguntas)
            if faltantes:
                for p in faltantes:
                    self.verificador.registrar_violacion(nodo_sueno["id"], p, "Falta en análisis")
                prompt_correccion = f"""
El análisis anterior no consideró los principios: {', '.join(faltantes)}.
Reescribe las preguntas y sugerencias para incluir estos principios.
Preguntas originales: {preguntas}
Sugerencias originales: {sugerencias}
"""
                respuesta = self._llamar_ollama(prompt_correccion)
                lineas = [l.strip() for l in respuesta.split('\n') if l.strip()]
                nuevas_preguntas = [l for l in lineas if '?' in l]
                nuevas_sugerencias = [l for l in lineas if '?' not in l]
                if nuevas_preguntas:
                    preguntas = nuevas_preguntas[:5]
                if nuevas_sugerencias:
                    sugerencias = nuevas_sugerencias[:5]

        nodo_mitote = {
            "id": nodo_sueno["id"],
            "tipo": "mitote",
            "buscado": {
                "preguntas": preguntas,
                "sugerencias": sugerencias,
                "analisis": f"Generado con Cámara de Diálogo + mayéutica/hermenéutica el {ahora()}"
            }
        }
        return nodo_mitote

# ----------------------------------------------------------------------
# PrincipiosVerificador (simplificado)
# ----------------------------------------------------------------------
class PrincipiosVerificador:
    def __init__(self):
        self.principios = {
            "dialectico": "La verdad emerge del choque de perspectivas.",
            "multidimensional": "Un problema tiene muchas caras.",
            "plural": "Todas las voces merecen ser escuchadas.",
            "cartesiano": "Duda metódica, verificación.",
            "biosferico": "Todo está conectado.",
            "socratico": "Humildad intelectual.",
            "hermeneutico": "Interpretar sin imponer.",
            "transparencia": "Mostrar procesos.",
            "humanista": "La persona es el centro.",
            "observar_sin_juzgar": "Documentar sin condenar."
        }

    def verificar(self, texto_analisis: str, preguntas_generadas: List[str]) -> List[str]:
        faltantes = []
        texto = (texto_analisis + " " + " ".join(preguntas_generadas)).lower()
        if "opuesto" not in texto and "contra" not in texto:
            faltantes.append("dialectico")
        if "multidimensional" not in texto and "diversas" not in texto and "múltiples" not in texto:
            faltantes.append("multidimensional")
        if "plural" not in texto and "diversas" not in texto:
            faltantes.append("plural")
        return faltantes

    def registrar_violacion(self, nodo_id: str, principio: str, descripcion: str):
        conn = sqlite3.connect(PRINCIPIOS_DB)
        c = conn.cursor()
        c.execute('''INSERT INTO violaciones (nodo_id, principio, descripcion, timestamp) VALUES (?, ?, ?, ?)''',
                  (nodo_id, principio, descripcion, ahora()))
        c.execute('''INSERT INTO estadisticas (principio, total_violaciones) VALUES (?, 1)
                     ON CONFLICT(principio) DO UPDATE SET total_violaciones = total_violaciones + 1''', (principio,))
        conn.commit()
        conn.close()

# ----------------------------------------------------------------------
# Ciclo Autónomo con Órbita Dual (Sueño y Mitote en direcciones opuestas)
# ----------------------------------------------------------------------
class CicloAutonomo:
    def __init__(self, shell):
        self.shell = shell
        self.activo = False
        self.frecuencia = 3600  # segundos
        self.hilo_sueno = None
        self.hilo_mitote = None
        self.direccion_sueno = 1
        self.direccion_mitote = -1
        self.indice_sueno = 0
        self.indice_mitote = 0

    def iniciar(self):
        if self.activo:
            return
        self.activo = True
        self.hilo_sueno = threading.Thread(target=self._recorrer_sueno, daemon=True)
        self.hilo_mitote = threading.Thread(target=self._recorrer_mitote, daemon=True)
        self.hilo_sueno.start()
        self.hilo_mitote.start()
        print(colorize("✓ Ciclo autónomo dual iniciado (Sueño y Mitote en órbitas opuestas).", "green"))

    def detener(self):
        self.activo = False
        if self.hilo_sueno:
            self.hilo_sueno.join(timeout=1)
        if self.hilo_mitote:
            self.hilo_mitote.join(timeout=1)
        print(colorize("✓ Ciclo autónomo dual detenido.", "yellow"))

    def _obtener_lista_nodos(self, directorio):
        archivos = sorted([f for f in os.listdir(directorio) if f.endswith('.json')])
        return archivos

    def _recorrer_sueno(self):
        while self.activo:
            time.sleep(self.frecuencia / 2)
            if not self.activo:
                break
            self._paso_sueno()

    def _recorrer_mitote(self):
        while self.activo:
            time.sleep(self.frecuencia / 2)
            if not self.activo:
                break
            self._paso_mitote()

    def _paso_sueno(self):
        nodos = self._obtener_lista_nodos(SUENO_DIR)
        if not nodos:
            return
        self.indice_sueno += self.direccion_sueno
        if self.indice_sueno >= len(nodos):
            self.indice_sueno = 0
        elif self.indice_sueno < 0:
            self.indice_sueno = len(nodos) - 1
        nodo_id = nodos[self.indice_sueno].replace('.json', '')
        nodo = cargar_nodo_sueno(nodo_id)
        if nodo:
            texto = nodo["conocido"]["descripcion"]
            preguntas, sugerencias = self.shell.gap.analizar_con_filosofia(texto)
            if preguntas:
                mitote_path = os.path.join(MITOTE_DIR, f"{nodo_id}.json")
                if os.path.exists(mitote_path):
                    with open(mitote_path, 'r', encoding='utf-8') as f:
                        mitote = json.load(f)
                    if "historial_analisis" not in mitote["buscado"]:
                        mitote["buscado"]["historial_analisis"] = []
                    mitote["buscado"]["historial_analisis"].append({
                        "fecha": ahora(),
                        "preguntas": preguntas,
                        "sugerencias": sugerencias,
                        "fuente": "orbita_sueno"
                    })
                    mitote["buscado"]["preguntas"] = list(dict.fromkeys(mitote["buscado"]["preguntas"] + preguntas))[:10]
                    with open(mitote_path, 'w', encoding='utf-8') as f:
                        json.dump(mitote, f, ensure_ascii=False, indent=2)
                    print(colorize(f"  [Órbita Sueño] Nodo {nodo_id} actualizado con nuevas preguntas.", "green"))

    def _paso_mitote(self):
        nodos = self._obtener_lista_nodos(MITOTE_DIR)
        if not nodos:
            return
        self.indice_mitote += self.direccion_mitote
        if self.indice_mitote >= len(nodos):
            self.indice_mitote = 0
        elif self.indice_mitote < 0:
            self.indice_mitote = len(nodos) - 1
        nodo_id = nodos[self.indice_mitote].replace('.json', '')
        mitote = cargar_nodo_mitote(nodo_id)
        if mitote and mitote["buscado"]["preguntas"]:
            pregunta = mitote["buscado"]["preguntas"][0]
            respuesta = self._responder_pregunta(pregunta, nodo_id)
            if respuesta:
                # Ingerir la respuesta como nuevo nodo (con acumulación)
                self.shell.ingestar_nodo(respuesta, fuente="orbita_mitote", etiqueta="respuesta_hipotesis", analizar=False)
                print(colorize(f"  [Órbita Mitote] Pregunta respondida para nodo {nodo_id}: {pregunta[:80]}...", "green"))

    def _responder_pregunta(self, pregunta: str, nodo_id: str) -> str:
        # Usar la Cámara de Diálogo para generar respuesta
        deliberacion = self.shell.gap.camara.deliberar(pregunta)
        # Obtener síntesis de los grupos activos
        if len(deliberacion) >= 2:
            grupos = list(deliberacion.keys())
            tesis = deliberacion[grupos[0]]
            antitesis = deliberacion[grupos[1]]
            sintesis = self.shell.gap.dialectica.sintetizar(tesis, antitesis)
        else:
            sintesis = next(iter(deliberacion.values())) if deliberacion else "No hay suficientes perspectivas."
        datos_world = self.shell.gap.world.consultar(pregunta)
        return f"{sintesis}\n\nInformación adicional del modelo mundial: {datos_world}"

# ----------------------------------------------------------------------
# Multimodal (simplificado)
# ----------------------------------------------------------------------
def procesar_imagen(ruta_imagen: str) -> str:
    if not BLIP_AVAILABLE:
        return f"[Imagen] {os.path.basename(ruta_imagen)} - descripción no disponible"
    # ... (código anterior)
    return "Descripción de imagen no implementada en esta versión simplificada"

def procesar_audio(ruta_audio: str) -> str:
    if not WHISPER_AVAILABLE:
        return f"[Audio] {os.path.basename(ruta_audio)} - transcripción no disponible"
    return "Transcripción no implementada"

def procesar_video(ruta_video: str) -> str:
    return f"[Video] {os.path.basename(ruta_video)} - procesamiento no implementado"

# ----------------------------------------------------------------------
# Shell principal (OLLIN v7)
# ----------------------------------------------------------------------
class OLLINShell:
    def __init__(self):
        self.memoria = self._cargar_memoria()
        self.proyecto_actual = self.memoria.get("proyecto_actual", "default")
        self.modo_swarm = self.memoria.get("modo_swarm", False)
        self.historial_chat = self.memoria.get("historial_chat", [])
        self.max_historial = self.memoria.get("max_historial", 20)
        self.gap = GapHunter()
        self.ciclo = self._cargar_ultimo_ciclo()
        self.autonomia = CicloAutonomo(self)
        self.web_thread = None
        self.estado_actual = "IDLE"
        self.mecp = MECP(self.proyecto_actual)  # MECP integrada

    def _cargar_memoria(self):
        if os.path.exists(MEMORIA_ARCHIVO):
            with open(MEMORIA_ARCHIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"version": 7, "proyecto_actual": "default", "modo_swarm": False, "historial_chat": [], "max_historial": 20}

    def _guardar_memoria(self):
        self.memoria["proyecto_actual"] = self.proyecto_actual
        self.memoria["modo_swarm"] = self.modo_swarm
        self.memoria["historial_chat"] = self.historial_chat
        self.memoria["max_historial"] = self.max_historial
        with open(MEMORIA_ARCHIVO, 'w', encoding='utf-8') as f:
            json.dump(self.memoria, f, ensure_ascii=False, indent=2)

    def _cargar_ultimo_ciclo(self):
        archivos = [f for f in os.listdir(OLLIN_ORBITA) if f.endswith('.json')]
        if archivos:
            ultimo = max(archivos)
            try:
                return int(ultimo.split('_')[0])
            except:
                pass
        return 0

    # --------------------------------------------------------------
    # Función de ingesta con Capa AntiBias, acumulación y MECP
    # --------------------------------------------------------------
    def ingestar_nodo(self, texto: str, fuente: str, etiqueta: str, analizar=True) -> Optional[str]:
        self.estado_actual = "INGESTA"
        if not texto.strip():
            return None

        datos_antibias = aplicar_capa_antibias(texto, fuente, etiqueta)
        texto_procesado = datos_antibias["texto_original"]
        fuente = datos_antibias["fuente"]
        etiqueta = datos_antibias["etiqueta"]

        # Buscar nodo similar para acumular
        nodo_existente = None
        if collection is not None and modelo_embeddings is not None:
            vector_consulta = modelo_embeddings.encode(texto_procesado)
            try:
                resultados = collection.query(query_embeddings=[vector_consulta.tolist()], n_results=1)
                if resultados['ids'][0]:
                    candidato_id = resultados['ids'][0][0]
                    similitud = resultados['distances'][0][0]
                    if similitud < 0.3:
                        nodo_existente = cargar_nodo_sueno(candidato_id)
            except Exception as e:
                print(colorize(f"⚠ Error en búsqueda de similitud: {e}", "yellow"))

        if nodo_existente:
            nodo_id = nodo_existente["id"]
            print(colorize(f"  Nodo similar encontrado: {nodo_id}. Acumulando información...", "cyan"))
            actualizar_nodo_con_adiciones(nodo_id, texto_procesado, fuente, datos_antibias)
            if analizar:
                nodo_sueno = cargar_nodo_sueno(nodo_id)
                nodo_mitote = self.gap.procesar_nodo(nodo_sueno, corregir_principios=True)
                with open(os.path.join(MITOTE_DIR, f"{nodo_id}.json"), 'w') as f:
                    json.dump(nodo_mitote, f, ensure_ascii=False, indent=2)
                if modelo_embeddings:
                    vector_sueno = modelo_embeddings.encode(nodo_sueno["conocido"]["descripcion"])
                    vector_mitote = modelo_embeddings.encode(" ".join(nodo_mitote["buscado"]["preguntas"]))
                    registrar_en_ometeotl(nodo_id, "mitote", nodo_mitote["buscado"], vector_mitote)
                    actualizar_dual_ometeotl(nodo_id, vector_sueno, vector_mitote)
            # Registrar en MECP
            nodo_mecp = {
                "timestamp": ahora(),
                "tipo": "asistente" if "autonomia" in fuente else "usuario",
                "texto": texto_procesado[:500],
                "fuente": fuente
            }
            self.mecp.registrar_nodo(nodo_mecp)
            return nodo_id
        else:
            nodo_id, nodo_sueno, nodo_mitote = crear_nodo(texto_procesado, fuente, etiqueta, datos_antibias)
            guardar_nodo(nodo_id, nodo_sueno, nodo_mitote)
            print(colorize(f"  ✓ Nuevo nodo {nodo_id} guardado en Sueño y Mitote.", "green"))

            vector_sueno = modelo_embeddings.encode(texto_procesado) if modelo_embeddings else None
            vector_mitote = vector_sueno.copy() if vector_sueno is not None else None

            registrar_en_ometeotl(nodo_id, "sueno", nodo_sueno["conocido"], vector_sueno)
            actualizar_dual_ometeotl(nodo_id, vector_sueno, vector_mitote)

            if collection is not None and vector_sueno is not None:
                try:
                    collection.add(
                        ids=[nodo_id],
                        embeddings=[vector_sueno.tolist()],
                        metadatas=[{"texto": texto_procesado[:500], "fuente": fuente, "etiqueta": etiqueta, "proyecto": self.proyecto_actual}]
                    )
                except Exception as e:
                    print(colorize(f"  ⚠ Error ChromaDB: {e}", "yellow"))

            if analizar:
                self.estado_actual = "ANALISIS"
                nodo_mitote_completo = self.gap.procesar_nodo(nodo_sueno, corregir_principios=True)
                with open(os.path.join(MITOTE_DIR, f"{nodo_id}.json"), 'w') as f:
                    json.dump(nodo_mitote_completo, f, ensure_ascii=False, indent=2)

                if modelo_embeddings and nodo_mitote_completo["buscado"]["preguntas"]:
                    texto_preguntas = " ".join(nodo_mitote_completo["buscado"]["preguntas"])
                    vector_mitote = modelo_embeddings.encode(texto_preguntas)
                    registrar_en_ometeotl(nodo_id, "mitote", nodo_mitote_completo["buscado"], vector_mitote)
                    actualizar_dual_ometeotl(nodo_id, vector_sueno, vector_mitote)
                else:
                    registrar_en_ometeotl(nodo_id, "mitote", nodo_mitote_completo["buscado"], vector_sueno)

            self.ciclo += 1
            registrar_orbita(str(self.ciclo), nodo_id, "ingesta")
            estado = {
                "id": f"ciclo_{self.ciclo}",
                "nodo": nodo_id,
                "vector": vector_sueno.tolist() if vector_sueno is not None else [0.0]*384,
                "hash": generar_hash(texto_procesado)
            }
            guardar_estado_ollin(estado)
            actualizar_dual_ollin(estado, {"hash": nodo_sueno["conocido"]["hash"]})
            self.estado_actual = "IDLE"

            # Registrar en MECP
            nodo_mecp = {
                "timestamp": ahora(),
                "tipo": "usuario" if not fuente.startswith("autonomia") else "asistente",
                "texto": texto_procesado[:500],
                "fuente": fuente
            }
            self.mecp.registrar_nodo(nodo_mecp)

            return nodo_id

    # --------------------------------------------------------------
    # Comandos básicos (similares a versiones anteriores)
    # --------------------------------------------------------------
    def cmd_ingesta(self, texto: str):
        fuente = input(colorize("  Fuente: ", "cyan")).strip()
        etiqueta = input(colorize("  Etiqueta: ", "cyan")).strip() or "documento"
        nodo_id = self.ingestar_nodo(texto, fuente, etiqueta, analizar=True)
        if nodo_id:
            print(colorize(f"  ✓ Nodo {nodo_id} procesado.", "green"))

    def cmd_conocido(self):
        archivos = sorted([f for f in os.listdir(SUENO_DIR) if f.endswith('.json')], reverse=True)
        if not archivos:
            print(colorize("  No hay nodos en Sueño.", "yellow"))
        else:
            print(colorize("\n  Últimos nodos (Sueño):", "blue"))
            for arch in archivos[:20]:
                with open(os.path.join(SUENO_DIR, arch), 'r') as f:
                    nodo = json.load(f)
                adiciones = len(nodo["conocido"].get("adiciones", []))
                ad_str = f" [+{adiciones}]" if adiciones else ""
                print(f"    - {nodo['id']} [{nodo['conocido']['etiqueta']}] de {nodo['conocido']['fuente']}{ad_str}")

    def cmd_buscado(self):
        archivos = sorted([f for f in os.listdir(MITOTE_DIR) if f.endswith('.json')], reverse=True)
        if not archivos:
            print(colorize("  No hay análisis en Mitote.", "yellow"))
        else:
            print(colorize("\n  Últimas preguntas abiertas (Mitote):", "blue"))
            for arch in archivos[:20]:
                with open(os.path.join(MITOTE_DIR, arch), 'r') as f:
                    nodo = json.load(f)
                preg = nodo.get("buscado", {}).get("preguntas", [])
                if preg:
                    print(f"    - {nodo['id']}: {preg[0][:80]}")

    def cmd_listar(self):
        suenos = len(os.listdir(SUENO_DIR))
        mitotes = len(os.listdir(MITOTE_DIR))
        print(colorize(f"\n  Estado del sistema:", "blue"))
        print(f"    Sueño: {suenos} nodos")
        print(f"    Mitote: {mitotes} nodos")
        if collection:
            try:
                print(f"    ChromaDB: {collection.count()} vectores")
            except:
                pass
        print(f"    Proyecto activo: {self.proyecto_actual}")
        print(f"    Modo MECP: {self.mecp.modo}")
        print(f"    Ciclo autónomo dual: {'activo' if self.autonomia.activo else 'inactivo'}")
        print(f"    Estado FSM: {self.estado_actual}")

    def cmd_contexto(self):
        """Exporta contexto de la MECP para inyectar en un modelo."""
        print(colorize("\n  Contexto exportable (MECP):", "blue"))
        print(self.mecp.exportar_contexto(n_ultimos=10))

    def cmd_camara(self, tema: str):
        """Consulta a la Cámara de Diálogo sobre un tema."""
        if not tema:
            print(colorize("  Uso: /camara <tema>", "red"))
            return
        resultado = self.gap.camara.deliberar(tema)
        print(colorize(f"\n  Deliberación de la Cámara de Diálogo sobre '{tema}':", "blue"))
        for grupo, texto in resultado.items():
            print(colorize(f"  [{grupo.capitalize()}]", "cyan"))
            print(f"    {texto[:500]}...")

    def cmd_autonomia(self, estado: str):
        if estado == "on":
            self.autonomia.iniciar()
        elif estado == "off":
            self.autonomia.detener()
        else:
            print(colorize("  Uso: /autonomia on|off", "red"))

    def cmd_mecp_modo(self, modo: str):
        modos_validos = ["EPISODICO", "PERMANENTE", "CICLICO", "FUGAZ"]
        if modo.upper() not in modos_validos:
            print(colorize(f"  Modo no válido. Opciones: {', '.join(modos_validos)}", "red"))
            return
        self.mecp.set_modo(modo.upper())
        print(colorize(f"  Modo MECP cambiado a {modo.upper()}", "green"))

    def cmd_chat(self):
        print(colorize("\nModo conversación (contexto infinito). Escribe /exit para salir.", "blue"))
        while True:
            try:
                mensaje = input(colorize("> ", "cyan")).strip()
                if mensaje == "/exit":
                    break
                if mensaje:
                    self.ingestar_nodo(mensaje, fuente=f"chat:{self.proyecto_actual}", etiqueta="conversacion", analizar=False)
                    # Construir prompt con contexto de MECP
                    contexto = self.mecp.exportar_contexto(n_ultimos=10)
                    prompt = f"{contexto}\nUsuario: {mensaje}\nOLLIN:"
                    respuesta = self.gap._llamar_ollama(prompt)
                    print(colorize(f"OLLIN: {respuesta}", "magenta"))
                    # Guardar respuesta también
                    self.ingestar_nodo(respuesta, fuente=f"ollin:chat", etiqueta="respuesta", analizar=False)
            except KeyboardInterrupt:
                print(colorize("\n  Saliendo del modo chat.", "yellow"))
                break

    def cmd_help(self):
        print(colorize("""
Comandos disponibles:

  ingesta <texto>     – Ingresar nuevo conocimiento
  conocido            – Ver últimos nodos de Sueño
  buscado             – Ver preguntas de Mitote
  listar              – Resumen del sistema

  /chat               – Modo conversación (usa MECP)
  /camara <tema>      – Consultar a la Cámara de Diálogo
  /autonomia on|off   – Activar ciclo dual
  /mecp_modo <modo>   – Cambiar modo de MECP (EPISODICO, PERMANENTE, CICLICO, FUGAZ)
  /contexto           – Exportar contexto MECP
  /help               – Mostrar esta ayuda
  salir               – Cerrar OLLIN
""", "cyan"))

    def run(self):
        print(colorize("\n" + "="*70, "blue"))
        print(colorize(" OLLIN SISTEMA NUCLEAR NOOSFÉRICO v7", "magenta"))
        print(colorize(" Cámara de Diálogo | Órbita Dual | MECP | Acumulación sin jerarquías", "blue"))
        print(colorize(" LEBD – Luis Ernesto Berzunza Díaz", "blue"))
        print(colorize("="*70, "blue"))
        print(" Escribe /help para ver comandos.")
        print(colorize("="*70, "blue") + "\n")

        while True:
            try:
                entrada = input(colorize("> ", "green")).strip()
                if not entrada:
                    continue
                if entrada == "salir":
                    self._guardar_memoria()
                    print(colorize("El movimiento ya empezó AHO", "magenta"))
                    break

                if entrada.startswith("/"):
                    partes = entrada.split()
                    cmd = partes[0].lower()
                    if cmd == "/help":
                        self.cmd_help()
                    elif cmd == "/chat":
                        self.cmd_chat()
                    elif cmd == "/camara":
                        tema = " ".join(partes[1:]) if len(partes) > 1 else ""
                        self.cmd_camara(tema)
                    elif cmd == "/autonomia":
                        estado = partes[1] if len(partes) > 1 else ""
                        self.cmd_autonomia(estado)
                    elif cmd == "/mecp_modo":
                        modo = partes[1] if len(partes) > 1 else ""
                        self.cmd_mecp_modo(modo)
                    elif cmd == "/contexto":
                        self.cmd_contexto()
                    else:
                        print(colorize(f"  Comando desconocido: {cmd}", "red"))
                else:
                    if entrada.startswith("ingesta "):
                        texto = entrada[8:].strip()
                        if texto:
                            self.cmd_ingesta(texto)
                        else:
                            print(colorize("  Error: texto vacío.", "red"))
                    elif entrada == "conocido":
                        self.cmd_conocido()
                    elif entrada == "buscado":
                        self.cmd_buscado()
                    elif entrada == "listar":
                        self.cmd_listar()
                    else:
                        print(colorize("  Comando no reconocido. Usa /help.", "red"))
            except KeyboardInterrupt:
                print(colorize("\n\nOLLIN interrumpido. Guardando estado...", "yellow"))
                self._guardar_memoria()
                break
            except Exception as e:
                print(colorize(f"  Error inesperado: {e}", "red"))

# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------
if __name__ == "__main__":
    shell = OLLINShell()
    shell.run()