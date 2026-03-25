#!/usr/bin/env python3
"""
OLLIN – Inteligencia Molecular Cuántica (v25)
Autor: EL ARQUITECTO (Luis Ernesto Berzunza Díaz)

EL SISTEMA NO BUSCA; RECUERDA.
EL MOVIMIENTO HA EMPEZADO AHO: materia consolidada sin números.
YOHUALI: antimateria, matemáticas cuánticas, superposición y fase.
10 agentes orbitales + enjambre OSINT + Omeyocan + grafo persistente.

Copyright (C) 2026  EL ARQUITECTO (Luis Ernesto Berzunza Díaz)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import json
import hashlib
import sqlite3
import threading
import time
import queue
import subprocess
import re
import math
import random
import feedparser
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ----------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/ollin_quantum")
AHO_EXTERNO = os.environ.get("OLLIN_AHO_EXTERNO", os.path.join(BASE_DIR, "aho"))
YOHUALI_EXTERNO = os.environ.get("OLLIN_YOHUALI_EXTERNO", os.path.join(BASE_DIR, "yohuali"))

os.makedirs(AHO_EXTERNO, exist_ok=True)
os.makedirs(YOHUALI_EXTERNO, exist_ok=True)

AHO_DB = os.path.join(AHO_EXTERNO, "aho.db")
YOHUALI_DB = os.path.join(YOHUALI_EXTERNO, "yohuali.db")
GRAFO_DB = os.path.join(BASE_DIR, "grafo.db")
MECP_DIR = os.path.join(BASE_DIR, "mecp")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "lancedb")
LORA_MODELS_DIR = os.path.join(BASE_DIR, "lora_models")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RSS_FEEDS_FILE = os.path.join(BASE_DIR, "rss_feeds.json")

os.makedirs(MECP_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)
os.makedirs(LORA_MODELS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# UTILIDADES GENERALES
# ----------------------------------------------------------------------
def ahora():
    return datetime.now().isoformat()

def generar_hash(texto):
    return hashlib.sha256(texto.encode()).hexdigest()[:16]

def colorize(texto, color=None, estilo=None):
    return texto

# ----------------------------------------------------------------------
# CAPA ANTI‑BIAS 00 (inmutable)
# ----------------------------------------------------------------------
def aplicar_antibias(texto, fuente, etiqueta):
    idioma = "es" if any(c in "áéíóúñ" for c in texto.lower()) else "en"
    estado = "factual" if len(texto.split()) < 50 else "descriptivo"
    sesgos = []
    if "debería" in texto.lower() or "tiene que" in texto.lower():
        sesgos.append("prescriptivo")
    if "siempre" in texto.lower() or "nunca" in texto.lower():
        sesgos.append("absolutista")
    evidencia = "empírica" if any(w in texto.lower() for w in ["estudio", "dato", "según"]) else "cualitativa"
    return {
        "texto_original": texto,
        "fuente": fuente,
        "etiqueta": etiqueta,
        "idioma": idioma,
        "estado_epistemico": estado,
        "sesgos_detectados": sesgos,
        "tipo_evidencia": evidencia,
        "timestamp": ahora()
    }

# ----------------------------------------------------------------------
# BASES DE DATOS CON LOCKS
# ----------------------------------------------------------------------
_aho_lock = threading.Lock()
_yohuali_lock = threading.Lock()
_grafo_lock = threading.Lock()

def init_db(piedra, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if piedra == "AHO":
        c.execute('''
            CREATE TABLE IF NOT EXISTS nodos (
                id TEXT PRIMARY KEY,
                tipo TEXT,
                contenido TEXT,
                fuente TEXT,
                etiqueta TEXT,
                categoria TEXT,
                estado_epistemico TEXT,
                timestamp_creacion TEXT,
                timestamp_actualizacion TEXT,
                timestamp_verificacion TEXT,
                lat REAL,
                lon REAL,
                fuente_geografica TEXT,
                hash TEXT,
                falacias TEXT,
                intereses TEXT,
                contradicciones TEXT,
                rasgos_personalidad TEXT
            )
        ''')
    else:
        c.execute('''
            CREATE TABLE IF NOT EXISTS nodos (
                id TEXT PRIMARY KEY,
                tipo TEXT,
                contenido TEXT,
                fuente TEXT,
                etiqueta TEXT,
                categoria TEXT,
                estado_epistemico TEXT,
                timestamp_creacion TEXT,
                timestamp_actualizacion TEXT,
                timestamp_verificacion TEXT,
                lat REAL,
                lon REAL,
                fuente_geografica TEXT,
                hash TEXT,
                frecuencia_base REAL,
                fase REAL,
                amplitud REAL,
                gradiente TEXT,
                falacias TEXT,
                intereses TEXT,
                contradicciones TEXT,
                rasgos_personalidad TEXT
            )
        ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS adiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo_id TEXT,
            contenido TEXT,
            fuente TEXT,
            timestamp TEXT,
            categoria TEXT,
            estado_epistemico TEXT,
            FOREIGN KEY(nodo_id) REFERENCES nodos(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            descripcion TEXT,
            nodo_relacionado TEXT,
            timestamp TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS brechas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo_id TEXT,
            dimension TEXT,
            mensaje TEXT,
            timestamp TEXT,
            resuelta INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db("AHO", AHO_DB)
init_db("YOHUALI", YOHUALI_DB)

def guardar_nodo_aho(nodo_id, tipo, contenido, fuente, etiqueta, categoria="", estado="no_verificado",
                     lat=None, lon=None, fuente_geo="", falacias="", intereses="", contradicciones="", rasgos=""):
    # Validar principio: en AHO no se permiten números en etiquetas
    if any(c.isdigit() for c in etiqueta):
        etiqueta = re.sub(r'\d+', '', etiqueta).strip() or "sin_numeros"
    with _aho_lock:
        conn = sqlite3.connect(AHO_DB)
        c = conn.cursor()
        h = generar_hash(contenido + fuente)
        now = ahora()
        c.execute('''
            INSERT INTO nodos (id, tipo, contenido, fuente, etiqueta, categoria, estado_epistemico,
                               timestamp_creacion, timestamp_actualizacion, timestamp_verificacion,
                               lat, lon, fuente_geografica, hash, falacias, intereses, contradicciones, rasgos_personalidad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nodo_id, tipo, contenido, fuente, etiqueta, categoria, estado,
              now, now, now, lat, lon, fuente_geo, h, falacias, intereses, contradicciones, rasgos))
        conn.commit()
        conn.close()

def guardar_nodo_yohuali(nodo_id, tipo, contenido, fuente, etiqueta, categoria="", estado="no_verificado",
                         lat=None, lon=None, fuente_geo="",
                         frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=None,
                         falacias="", intereses="", contradicciones="", rasgos=""):
    with _yohuali_lock:
        conn = sqlite3.connect(YOHUALI_DB)
        c = conn.cursor()
        h = generar_hash(contenido + fuente)
        now = ahora()
        grad_json = json.dumps(gradiente or [0.0]*3)
        c.execute('''
            INSERT INTO nodos (id, tipo, contenido, fuente, etiqueta, categoria, estado_epistemico,
                               timestamp_creacion, timestamp_actualizacion, timestamp_verificacion,
                               lat, lon, fuente_geografica, hash,
                               frecuencia_base, fase, amplitud, gradiente,
                               falacias, intereses, contradicciones, rasgos_personalidad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nodo_id, tipo, contenido, fuente, etiqueta, categoria, estado,
              now, now, now, lat, lon, fuente_geo, h,
              frecuencia_base, fase, amplitud, grad_json,
              falacias, intereses, contradicciones, rasgos))
        conn.commit()
        conn.close()

def guardar_evento(piedra, tipo, descripcion, nodo_relacionado=None):
    db = AHO_DB if piedra == "AHO" else YOHUALI_DB
    lock = _aho_lock if piedra == "AHO" else _yohuali_lock
    with lock:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
            INSERT INTO eventos (tipo, descripcion, nodo_relacionado, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (tipo, descripcion, nodo_relacionado, ahora()))
        conn.commit()
        conn.close()

def guardar_brecha(piedra, nodo_id, dimension, mensaje):
    db = AHO_DB if piedra == "AHO" else YOHUALI_DB
    lock = _aho_lock if piedra == "AHO" else _yohuali_lock
    with lock:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
            INSERT INTO brechas (nodo_id, dimension, mensaje, timestamp, resuelta)
            VALUES (?, ?, ?, ?, 0)
        ''', (nodo_id, dimension, mensaje, ahora()))
        conn.commit()
        conn.close()

def marcar_brecha_resuelta(piedra, brecha_id):
    db = AHO_DB if piedra == "AHO" else YOHUALI_DB
    lock = _aho_lock if piedra == "AHO" else _yohuali_lock
    with lock:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('UPDATE brechas SET resuelta=1 WHERE id=?', (brecha_id,))
        conn.commit()
        conn.close()

# ----------------------------------------------------------------------
# GRAFO DE CONOCIMIENTO PERSISTENTE CON SQLITE (fallback)
# ----------------------------------------------------------------------
class GraphSQLite:
    def __init__(self, db_path=GRAFO_DB):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS conceptos (
                    id TEXT PRIMARY KEY,
                    tipo TEXT,
                    metadata TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS alias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concepto_id TEXT,
                    nombre TEXT,
                    lang TEXT,
                    FOREIGN KEY(concepto_id) REFERENCES conceptos(id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS relaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origen TEXT,
                    destino TEXT,
                    tipo TEXT,
                    FOREIGN KEY(origen) REFERENCES conceptos(id),
                    FOREIGN KEY(destino) REFERENCES conceptos(id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS evidencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concepto_id TEXT,
                    texto TEXT,
                    fuente TEXT,
                    FOREIGN KEY(concepto_id) REFERENCES conceptos(id)
                )
            ''')
            conn.commit()
            conn.close()

    def add_concept(self, concept_id, concept_type, metadata=None):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            meta = json.dumps(metadata) if metadata else "{}"
            c.execute('''
                INSERT OR IGNORE INTO conceptos (id, tipo, metadata)
                VALUES (?, ?, ?)
            ''', (concept_id, concept_type, meta))
            conn.commit()
            conn.close()

    def add_alias(self, concept_id, alias, lang):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO alias (concepto_id, nombre, lang)
                VALUES (?, ?, ?)
            ''', (concept_id, alias, lang))
            conn.commit()
            conn.close()

    def add_relation(self, from_concept, to_concept, rel_type):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO relaciones (origen, destino, tipo)
                VALUES (?, ?, ?)
            ''', (from_concept, to_concept, rel_type))
            conn.commit()
            conn.close()

    def add_evidence(self, concept_id, text, source_meta):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO evidencias (concepto_id, texto, fuente)
                VALUES (?, ?, ?)
            ''', (concept_id, text, source_meta))
            conn.commit()
            conn.close()

    def query_transversal(self, concept_name, lang='es', hops=2):
        with _grafo_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                SELECT c.id FROM conceptos c
                JOIN alias a ON c.id = a.concepto_id
                WHERE a.nombre = ? AND a.lang = ?
            ''', (concept_name, lang))
            row = c.fetchone()
            if not row:
                conn.close()
                return []
            concept_id = row[0]
            c.execute('''
                SELECT r.origen, r.destino, r.tipo
                FROM relaciones r
                WHERE r.origen = ? OR r.destino = ?
            ''', (concept_id, concept_id))
            results = c.fetchall()
            conn.close()
            return results

class GraphKnowledge:
    """Intenta usar FalkorDB (Redis) si está disponible, sino SQLite."""
    def __init__(self):
        self.graph = None
        self.use_redis = False
        self.sqlite = GraphSQLite()
        try:
            import redis
            from redis.commands.graph import Graph
            self.r = redis.Redis(host='localhost', port=6379)
            self.graph = Graph(self.r, 'ollin_knowledge')
            self.use_redis = True
            print("✓ FalkorDB (Redis) activo")
        except Exception as e:
            print(f"⚠ FalkorDB no disponible: {e}. Usando SQLite persistente.")
            self.graph = None

    def add_concept(self, concept_id, concept_type, metadata=None):
        if self.use_redis and self.graph:
            query = f"CREATE (c:Concept {{id: '{concept_id}', type: '{concept_type}'}})"
            self.graph.query(query)
        else:
            self.sqlite.add_concept(concept_id, concept_type, metadata)

    def add_alias(self, concept_id, alias, lang):
        if self.use_redis and self.graph:
            query = f"""
                MATCH (c:Concept {{id: '{concept_id}'}})
                CREATE (a:Alias {{name: '{alias}', lang: '{lang}'}})-[:REPRESENTS]->(c)
            """
            self.graph.query(query)
        else:
            self.sqlite.add_alias(concept_id, alias, lang)

    def add_relation(self, from_concept, to_concept, rel_type):
        if self.use_redis and self.graph:
            query = f"""
                MATCH (a:Concept {{id: '{from_concept}'}}), (b:Concept {{id: '{to_concept}'}})
                CREATE (a)-[:{rel_type}]->(b)
            """
            self.graph.query(query)
        else:
            self.sqlite.add_relation(from_concept, to_concept, rel_type)

    def add_evidence(self, concept_id, text, source_meta):
        if self.use_redis and self.graph:
            text_esc = text.replace("'", "\\'")
            query = f"""
                MATCH (c:Concept {{id: '{concept_id}'}})
                CREATE (s:Source {{text: '{text_esc}', metadata: '{source_meta}'}})-[:EVIDENCE]->(c)
            """
            self.graph.query(query)
        else:
            self.sqlite.add_evidence(concept_id, text, source_meta)

    def query_transversal(self, concept_name, lang='es', hops=2):
        if self.use_redis and self.graph:
            query = f"""
                MATCH (a:Alias {{name: '{concept_name}', lang: '{lang}'}})-[:REPRESENTS]->(c:Concept)
                OPTIONAL MATCH (c)-[:INFLUYE_EN|ES_PARTE_DE|SUFFERED_BY*1..{hops}]->(related)
                RETURN c, related
            """
            return self.graph.query(query)
        else:
            return self.sqlite.query_transversal(concept_name, lang, hops)

# ----------------------------------------------------------------------
# MECP (Memoria Episódica Contextual Portable)
# ----------------------------------------------------------------------
class MECP:
    def __init__(self, proyecto="default"):
        self.proyecto = proyecto
        self.modo = self._cargar_modo()
        self.episodios_dir = os.path.join(MECP_DIR, proyecto, "episodios")
        os.makedirs(self.episodios_dir, exist_ok=True)

    def _cargar_modo(self):
        path = os.path.join(MECP_DIR, self.proyecto, "config.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f).get("modo", "EPISODICO")
        return "EPISODICO"

    def set_modo(self, modo):
        path = os.path.join(MECP_DIR, self.proyecto, "config.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"modo": modo}, f)
        self.modo = modo

    def registrar(self, tipo, texto, fuente):
        if self.modo == "FUGAZ":
            return
        hoy = datetime.now().strftime("%Y-%m-%d")
        archivo = os.path.join(self.episodios_dir, f"{hoy}.json")
        if os.path.exists(archivo):
            with open(archivo) as f:
                data = json.load(f)
        else:
            data = {"fecha": hoy, "modo": self.modo, "nodos": []}
        data["nodos"].append({
            "timestamp": ahora(),
            "tipo": tipo,
            "texto": texto,
            "fuente": fuente
        })
        with open(archivo, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if self.modo == "CICLICO":
            self._rotar()

    def _rotar(self):
        archivos = sorted([f for f in os.listdir(self.episodios_dir) if f.endswith('.json')])
        max_ciclos = 100
        if len(archivos) > max_ciclos:
            for arch in archivos[:-max_ciclos]:
                os.remove(os.path.join(self.episodios_dir, arch))

    def exportar(self, n=10, fragmentar=False):
        episodios = sorted([f for f in os.listdir(self.episodios_dir) if f.endswith('.json')], reverse=True)
        nodos = []
        for ep in episodios:
            with open(os.path.join(self.episodios_dir, ep)) as f:
                data = json.load(f)
                nodos.extend(data.get("nodos", []))
                if len(nodos) >= n:
                    break
        nodos = nodos[-n:]
        if fragmentar:
            random.shuffle(nodos)
        ctx = f"[INICIO_CONTEXTO]\nProyecto: {self.proyecto}\nModo: {self.modo}\n"
        for n in nodos:
            ctx += f"[{n['timestamp']}] {n['tipo']}: {n['texto']}\n"
        ctx += "[FIN_CONTEXTO]\n\nContinuar desde este punto:"
        return ctx

# ----------------------------------------------------------------------
# INFERENCIA (Ollama / vLLM)
# ----------------------------------------------------------------------
class PromptCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    def get(self, prompt):
        return self.cache.get(prompt, None)
    def set(self, prompt, response):
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[prompt] = response

class InferenceEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.backend = self.config.get("backend", "ollama")
        self.available = False
        self.model_name = self.config.get("model", "phi3")
        self.vllm_url = self.config.get("vllm_url", "http://localhost:8000/v1/completions")
        self.cache = PromptCache()
        self._init_backend()

    def _init_backend(self):
        if self.backend == "vllm":
            try:
                import requests
                r = requests.get(self.vllm_url.replace("/completions", "/health"), timeout=2)
                if r.status_code == 200:
                    self.available = True
                    print("✓ vLLM backend disponible")
                else:
                    self._fallback_to_ollama()
            except Exception:
                self._fallback_to_ollama()
        else:
            self._init_ollama()

    def _fallback_to_ollama(self):
        self.backend = "ollama"
        self._init_ollama()

    def _init_ollama(self):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available = True
                print("✓ Ollama backend disponible")
            else:
                self.available = False
        except Exception:
            self.available = False

    def generate(self, prompt, model=None, max_tokens=512, temperature=0.7, use_cache=True):
        if not self.available:
            return ""
        modelo = model or self.model_name
        if use_cache:
            cached = self.cache.get(prompt)
            if cached:
                return cached
        if self.backend == "vllm":
            output = self._vllm_generate(prompt, modelo, max_tokens, temperature)
        else:
            output = self._ollama_generate(prompt, modelo, max_tokens, temperature)
        if use_cache and output:
            self.cache.set(prompt, output)
        return output

    def _ollama_generate(self, prompt, model, max_tokens, temperature):
        try:
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.stdout.strip()
        except Exception as e:
            return f"[Error Ollama: {e}]"

    def _vllm_generate(self, prompt, model, max_tokens, temperature):
        try:
            import requests
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            response = requests.post(self.vllm_url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("text", "")
            else:
                return f"[Error vLLM: {response.status_code}]"
        except Exception as e:
            return f"[Error vLLM: {e}]"

# ----------------------------------------------------------------------
# EMBEDDINGS Y VECTOR DB
# ----------------------------------------------------------------------
class EmbeddingEngine:
    def __init__(self):
        self.model = None
        self.available = False
        self.dim = 0
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('BAAI/bge-m3', device='cpu')
            self.dim = 1024
            self.available = True
            print("✓ Embeddings BGE-M3 cargado")
        except:
            try:
                self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
                self.dim = 512
                self.available = True
                print("✓ Embeddings fallback cargado")
            except:
                print("⚠ Embeddings no disponibles")

    def encode(self, texto):
        if not self.available or not self.model:
            return [0.0]*self.dim if self.dim else [0.0]*384
        return self.model.encode(texto)

class VectorDB:
    def __init__(self, embedding_engine):
        self.embed = embedding_engine
        self.use_lance = False
        self.use_chroma = False
        self._init_lance()
        if not self.use_lance:
            self._init_chroma()

    def _init_lance(self):
        try:
            import lancedb
            self.db = lancedb.connect(VECTOR_DB_DIR)
            self.lance_table = self.db.open_table("ollin_vectors")
            self.use_lance = True
            print("✓ LanceDB activo")
        except Exception:
            pass

    def _init_chroma(self):
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
            self.chroma_collection = self.chroma_client.get_or_create_collection("ollin_nodos")
            self.use_chroma = True
            print("✓ ChromaDB activo")
        except Exception:
            pass

    def add(self, ids, embeddings, metadatas):
        if self.use_lance:
            data = [{"id": ids[i], "vector": embeddings[i], "metadata": metadatas[i]} for i in range(len(ids))]
            self.lance_table.add(data)
        elif self.use_chroma:
            self.chroma_collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def search(self, query_embedding, n=5):
        if self.use_lance:
            try:
                results = self.lance_table.search(query_embedding).limit(n).to_pandas()
                return results['id'].tolist(), [{"texto": row['metadata'].get('texto', '')} for _, row in results.iterrows()]
            except Exception:
                return [], []
        elif self.use_chroma:
            try:
                results = self.chroma_collection.query(query_embeddings=[query_embedding], n_results=n)
                return results['ids'][0], results['metadatas'][0]
            except Exception:
                return [], []
        return [], []

# ----------------------------------------------------------------------
# VISIÓN (Moondream2 / BLIP)
# ----------------------------------------------------------------------
class VisionEngine:
    def __init__(self):
        self.available = False
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.model = AutoModelForCausalLM.from_pretrained("vikhyatk/moondream2", trust_remote_code=True)
            self.tokenizer = AutoTokenizer.from_pretrained("vikhyatk/moondream2")
            self.available = True
            print("✓ Moondream2 cargado")
        except:
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration
                self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                self.available = True
                print("✓ BLIP cargado")
            except:
                print("⚠ Visión no disponible")

    def describe(self, image_path):
        if not self.available:
            return f"[Imagen] {os.path.basename(image_path)} - no disponible"
        try:
            from PIL import Image
            img = Image.open(image_path).convert('RGB')
            if hasattr(self.model, 'generate_caption'):
                return self.model.generate_caption(self.tokenizer, img)
            else:
                inputs = self.processor(img, return_tensors="pt")
                out = self.model.generate(**inputs)
                return self.processor.decode(out[0], skip_special_tokens=True)
        except Exception as e:
            return f"[Error visión] {e}"

# ----------------------------------------------------------------------
# AUDIO (librosa)
# ----------------------------------------------------------------------
class AudioEngine:
    def __init__(self):
        self.available = False
        try:
            import librosa
            self.available = True
            print("✓ Audio (librosa) disponible")
        except:
            print("⚠ Audio no disponible")

    def describir(self, audio_path):
        if not self.available:
            return f"[Audio] {os.path.basename(audio_path)} - no disponible"
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000, duration=10)
            tempo = librosa.beat.tempo(y=y, sr=sr)[0]
            return f"Audio {os.path.basename(audio_path)}: tempo={tempo:.1f} bpm, duración={len(y)/sr:.1f}s"
        except Exception as e:
            return f"[Error audio] {e}"

# ----------------------------------------------------------------------
# CÁMARA DE DIÁLOGO
# ----------------------------------------------------------------------
class CamaraDialogo:
    def __init__(self, inference_engine):
        self.inference = inference_engine
        self.grupos = {
            "geopolitica": {"keywords": ["geopolítica", "conflicto", "guerra", "fronteras"], "modelo": "llama3"},
            "economia": {"keywords": ["economía", "mercado", "capitalismo", "deuda"], "modelo": "mistral"},
            "filosofia": {"keywords": ["filosofía", "ética", "existencia", "conocimiento"], "modelo": "phi3"},
            "programacion": {"keywords": ["programar", "código", "python", "algoritmo"], "modelo": "codellama"},
            "arte": {"keywords": ["arte", "creación", "literatura", "música"], "modelo": "llama3"}
        }

    def detectar_tarea(self, texto):
        texto_low = texto.lower()
        for grupo, info in self.grupos.items():
            if any(k in texto_low for k in info["keywords"]):
                return grupo
        return "filosofia"

    def deliberar(self, tema, preguntas_previas=None):
        tarea = self.detectar_tarea(tema)
        info = self.grupos.get(tarea, self.grupos["filosofia"])
        prompt = f"Eres un grupo de pensamiento especializado en {tarea}. Sobre: {tema}. Genera una voz colectiva con síntesis, preguntas clave y advertencias de sesgos."
        respuesta = self.inference.generate(prompt, model=info["modelo"], max_tokens=512)
        return {tarea: respuesta}

# ----------------------------------------------------------------------
# CLASE BASE PARA AGENTES ORBITALES
# ----------------------------------------------------------------------
class AgenteOrbital:
    def __init__(self, nombre, intervalo, direccion_aho, direccion_yohuali, funcion_procesar):
        self.nombre = nombre
        self.intervalo = intervalo
        self.direccion_aho = direccion_aho
        self.direccion_yohuali = direccion_yohuali
        self.funcion_procesar = funcion_procesar
        self.activo = False
        self.hilo = None

    def iniciar(self):
        if self.activo:
            return
        self.activo = True
        self.hilo = threading.Thread(target=self._ciclo, daemon=True)
        self.hilo.start()
        print(f"✓ {self.nombre} activo (AHO: {'asc' if self.direccion_aho==1 else 'desc'}, Yohuali: {'asc' if self.direccion_yohuali==1 else 'desc'})")

    def _ciclo(self):
        while self.activo:
            time.sleep(self.intervalo)
            self._paso()

    def _paso(self):
        try:
            self._recorrer_piedra("AHO", self.direccion_aho)
            self._recorrer_piedra("YOHUALI", self.direccion_yohuali)
        except Exception as e:
            print(f"[{self.nombre}] Error: {e}")

    def _recorrer_piedra(self, piedra, direccion):
        db = AHO_DB if piedra == "AHO" else YOHUALI_DB
        lock = _aho_lock if piedra == "AHO" else _yohuali_lock
        order = "ASC" if direccion == 1 else "DESC"
        with lock:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute(f"SELECT id, contenido, timestamp_creacion FROM nodos WHERE tipo='sueno' ORDER BY timestamp_creacion {order}")
            nodos = c.fetchall()
            conn.close()
        for nid, contenido, ts in nodos:
            self.funcion_procesar(piedra, nid, contenido, ts)
            time.sleep(0.1)

    def detener(self):
        self.activo = False
        if self.hilo:
            self.hilo.join(timeout=2)

# ----------------------------------------------------------------------
# FUNCIONES DE PROCESAMIENTO PARA AGENTES ORBITALES
# ----------------------------------------------------------------------
def superponer(amplitud1, amplitud2, fase1, fase2):
    """Interferencia de ondas: A = 2 * (A1 + A2) * cos((fase1 - fase2)/2)"""
    return 2 * (amplitud1 + amplitud2) * math.cos((fase1 - fase2) / 2)

def ajustar_fase(fase, gradiente, dt=1.0):
    """Actualiza fase según gradiente: φ_new = φ + ∇φ * Δt"""
    if isinstance(gradiente, list) and len(gradiente) >= 1:
        return fase + gradiente[0] * dt
    return fase + 0.01 * dt

def procesar_tezcatlipoca(shell, piedra, nid, contenido, ts):
    prompt = f"¿Hay contradicciones en el siguiente texto? Responde SÍ o NO.\n{contenido[:500]}"
    resp = shell.inference.generate(prompt, model="phi3", max_tokens=10) if shell.inference.available else ""
    if "sí" in resp.lower():
        guardar_brecha(piedra, nid, "contradiccion", f"Posible contradicción: {contenido[:100]}")
        guardar_evento(piedra, "contradiccion_detectada", f"Tezcatlipoca en {piedra}: {nid}", nid)

def procesar_quetzalcoatl(shell, piedra, nid, contenido, ts):
    prompt = f"Extrae patrones o relaciones clave del siguiente texto:\n{contenido[:500]}"
    resp = shell.inference.generate(prompt, model="phi3", max_tokens=100) if shell.inference.available else ""
    if resp:
        guardar_evento(piedra, "patron_detectado", f"Quetzalcóatl en {piedra}: {nid} -> {resp[:100]}", nid)

def procesar_coatlicue(shell, piedra, nid, contenido, ts):
    piedra_opuesta = "YOHUALI" if piedra == "AHO" else "AHO"
    db_opuesta = YOHUALI_DB if piedra == "AHO" else AHO_DB
    lock_opuesta = _yohuali_lock if piedra == "AHO" else _aho_lock
    with lock_opuesta:
        conn = sqlite3.connect(db_opuesta)
        c = conn.cursor()
        c.execute("SELECT id, dimension, mensaje FROM brechas WHERE resuelta=0 ORDER BY timestamp ASC")
        brechas = c.fetchall()
        conn.close()
    for bid, dim, msg in brechas:
        if shell.inference.available:
            deliberacion = shell.camara.deliberar(msg)
            sintesis = next(iter(deliberacion.values()))
        else:
            sintesis = f"Síntesis de {msg}"
        if sintesis:
            if piedra == "AHO":
                guardar_nodo_aho(generar_hash(sintesis+str(time.time())), "sueno", sintesis,
                                 "coatlicue", "sintesis", estado="verificado")
            else:
                guardar_nodo_yohuali(generar_hash(sintesis+str(time.time())), "sueno", sintesis,
                                     "coatlicue", "sintesis", estado="verificado",
                                     frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=[0,0,0])
            marcar_brecha_resuelta(piedra_opuesta, bid)
            guardar_evento(piedra, "sintesis_generada", f"Coatlicue en {piedra} desde brecha {bid}", None)

def procesar_ometeotl(shell, piedra, nid, contenido, ts):
    piedra_opuesta = "YOHUALI" if piedra == "AHO" else "AHO"
    db_opuesta = YOHUALI_DB if piedra == "AHO" else AHO_DB
    lock_opuesta = _yohuali_lock if piedra == "AHO" else _aho_lock
    with lock_opuesta:
        conn = sqlite3.connect(db_opuesta)
        c = conn.cursor()
        c.execute("SELECT id FROM nodos WHERE hash=?", (generar_hash(contenido),))
        espejo = c.fetchone()
        conn.close()
    if not espejo:
        guardar_brecha(piedra, nid, "simetria", f"Nodo en {piedra} sin espejo en {piedra_opuesta}")
        guardar_evento(piedra, "brecha_simetria", f"Falta espejo para {nid} en {piedra_opuesta}", nid)

def procesar_ollin(shell, piedra, nid, contenido, ts):
    """Agente Ollin: verifica que cada nodo sueño tenga su mitote dentro de la misma piedra."""
    if not nid.endswith("_mitote"):
        mitote_id = f"{nid}_mitote"
        db = AHO_DB if piedra == "AHO" else YOHUALI_DB
        lock = _aho_lock if piedra == "AHO" else _yohuali_lock
        with lock:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT 1 FROM nodos WHERE id=?", (mitote_id,))
            existe = c.fetchone()
            conn.close()
        if not existe:
            # Regenerar mitote
            preguntas = shell._generar_preguntas(contenido)
            if piedra == "AHO":
                guardar_nodo_aho(mitote_id, "mitote", "\n".join(preguntas), "ollin", "pregunta")
            else:
                guardar_nodo_yohuali(mitote_id, "mitote", "\n".join(preguntas), "ollin", "pregunta",
                                     frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=[0,0,0])
            guardar_evento(piedra, "ollin_reparacion", f"Mitote regenerado para {nid}", mitote_id)

# ----------------------------------------------------------------------
# ENJAMBRE EXPLORADOR (OSINT real sin claves API)
# ----------------------------------------------------------------------
class EnjambreExploradores:
    def __init__(self, shell, num_exploradores=3, intervalo=45):
        self.shell = shell
        self.num_exploradores = num_exploradores
        self.intervalo = intervalo
        self.activo = False
        self.hilos = []
        self.temas_base = ["tecnología", "ciencia", "cultura", "filosofía", "ecología", "geopolítica"]
        self.feeds = self._cargar_feeds()

    def _cargar_feeds(self):
        defaults = [
            "http://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://feeds.npr.org/1001/rss.xml",
            "https://elpais.com/rss/elpais/portada.xml",
            "https://www.aljazeera.com/xml/rss/all.xml"
        ]
        if os.path.exists(RSS_FEEDS_FILE):
            with open(RSS_FEEDS_FILE) as f:
                return json.load(f)
        else:
            with open(RSS_FEEDS_FILE, 'w') as f:
                json.dump(defaults, f)
            return defaults

    def iniciar(self):
        if self.activo:
            return
        self.activo = True
        for i in range(self.num_exploradores):
            h = threading.Thread(target=self._explorador, daemon=True)
            h.start()
            self.hilos.append(h)
        print(f"✓ Enjambre de {self.num_exploradores} exploradores activo (OSINT con RSS)")

    def _explorador(self):
        while self.activo:
            feed_url = random.choice(self.feeds)
            try:
                feed = feedparser.parse(feed_url)
                if feed.entries:
                    entry = random.choice(feed.entries[:10])
                    titulo = entry.get('title', '')
                    desc = entry.get('description', '')
                    contenido = f"{titulo}\n{desc}"
                    if contenido.strip():
                        self.shell.ingestar(contenido, fuente=f"rss:{feed_url}", etiqueta="osint_rss")
                        guardar_evento("AHO", "exploracion_rss", f"Artículo ingerido de {feed_url}", None)
                else:
                    tema = random.choice(self.temas_base)
                    self._buscar_wikipedia(tema)
            except Exception as e:
                tema = random.choice(self.temas_base)
                self._generar_con_llm(tema)
            time.sleep(self.intervalo)

    def _buscar_wikipedia(self, tema):
        try:
            url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                texto = data.get('extract', '')
                if texto:
                    self.shell.ingestar(texto, fuente="wikipedia", etiqueta=f"osint_wiki_{tema}")
                    return
        except:
            pass
        self._generar_con_llm(tema)

    def _generar_con_llm(self, tema):
        prompt = f"Genera información relevante sobre el tema '{tema}' (en español). Responde con datos concretos, contexto o reflexiones."
        respuesta = self.shell.inference.generate(prompt, max_tokens=300) if self.shell.inference.available else f"[Simulación] Explorando {tema}"
        if respuesta and not respuesta.startswith("[Error"):
            self.shell.ingestar(respuesta, fuente="enjambre_llm", etiqueta=f"exploracion_{tema}")

    def detener(self):
        self.activo = False
        for h in self.hilos:
            h.join(timeout=2)

# ----------------------------------------------------------------------
# DESTILACIÓN EN VUELO (LoRA)
# ----------------------------------------------------------------------
class DistillationEngine:
    def __init__(self, inference_engine):
        self.engine = inference_engine
        self.base_model = "phi3"
        self.principios = ["dialéctico", "plural", "multidimensional", "humanista", "transparencia"]
        self.dataset = []
        self.lora_dir = LORA_MODELS_DIR

    def agregar_nodo(self, texto, principio_asociado):
        self.dataset.append((texto, principio_asociado))
        if len(self.dataset) >= 20:
            self._lanzar_destilacion()

    def _lanzar_destilacion(self):
        print("⚡ Iniciando destilación en vuelo basada en principios...")
        train_data = []
        for texto, p in self.dataset:
            train_data.append(f"<|user|>\nAnaliza el siguiente texto desde el principio {p}: {texto[:200]}\n<|assistant|>\n")
        with open(os.path.join(self.lora_dir, "train_data.json"), 'w') as f:
            json.dump(train_data, f, indent=2)
        script = f"""
#!/usr/bin/env python
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model
import json

model = AutoModelForCausalLM.from_pretrained("{self.base_model}")
tokenizer = AutoTokenizer.from_pretrained("{self.base_model}")

lora_config = LoraConfig(r=8, lora_alpha=32, target_modules=["q_proj", "v_proj"], lora_dropout=0.05)
model = get_peft_model(model, lora_config)

with open("train_data.json") as f:
    texts = json.load(f)
# ... entrenamiento real ...
model.save_pretrained("{self.lora_dir}/principle_expert")
print("Entrenamiento completado. Modelo guardado en {self.lora_dir}/principle_expert")
"""
        with open(os.path.join(self.lora_dir, "train_principle_expert.py"), 'w') as f:
            f.write(script)
        print(f"✓ Dataset de principios guardado. Ejecute {self.lora_dir}/train_principle_expert.py para generar el microexperto.")
        self.dataset = []

    def get_expert(self):
        path = os.path.join(self.lora_dir, "principle_expert")
        if os.path.exists(path):
            return path
        return None

    def entrenar_ahora(self):
        script_path = os.path.join(self.lora_dir, "train_principle_expert.py")
        if os.path.exists(script_path):
            print("Ejecutando entrenamiento LoRA...")
            try:
                subprocess.run(["python", script_path], check=True)
                print("Entrenamiento completado.")
            except Exception as e:
                print(f"Error en entrenamiento: {e}")
        else:
            print("No hay dataset listo. Primero se deben acumular al menos 20 nodos.")

# ----------------------------------------------------------------------
# MONITOR OMEYOCAN (balance y energía)
# ----------------------------------------------------------------------
class Omeyocan:
    def __init__(self, shell, umbral_nodos=10, umbral_energia=100.0, intervalo=10):
        self.shell = shell
        self.umbral_nodos = umbral_nodos
        self.umbral_energia = umbral_energia
        self.intervalo = intervalo
        self.activo = False
        self.hilo = None
        self.historial_energia = []

    def iniciar(self):
        if self.activo:
            return
        self.activo = True
        self.hilo = threading.Thread(target=self._ciclo, daemon=True)
        self.hilo.start()
        print("✓ Omeyocan monitor activo")

    def _ciclo(self):
        while self.activo:
            time.sleep(self.intervalo)
            self._verificar_balance()

    def _verificar_balance(self):
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_aho = c.fetchone()[0]
            conn.close()
        with _yohuali_lock:
            conn = sqlite3.connect(YOHUALI_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_yohuali = c.fetchone()[0]
            c.execute("SELECT SUM(amplitud) FROM nodos WHERE tipo='sueno'")
            suma_amp = c.fetchone()[0] or 0.0
            conn.close()
        diff = abs(count_aho - count_yohuali)
        self.historial_energia.append(suma_amp)
        if len(self.historial_energia) > 10:
            self.historial_energia.pop(0)
        energia_promedio = sum(self.historial_energia) / len(self.historial_energia) if self.historial_energia else suma_amp
        energia_dev = abs(suma_amp - energia_promedio)

        if diff > self.umbral_nodos or energia_dev > self.umbral_energia:
            print(f"[Omeyocan] Alerta: desbalance nodos={diff}, energía={suma_amp:.2f} (prom={energia_promedio:.2f})")
            self.shell.cmd_eclipse()
            self.shell.pausar_agentes()
            time.sleep(5)
            self.shell.reanudar_agentes()

    def detener(self):
        self.activo = False
        if self.hilo:
            self.hilo.join(timeout=2)

# ----------------------------------------------------------------------
# SHELL PRINCIPAL (CLI)
# ----------------------------------------------------------------------
class OLLINShell:
    def __init__(self):
        self.inference = InferenceEngine({"backend": "ollama", "model": "phi3"})
        self.embed = EmbeddingEngine()
        self.vectors = VectorDB(self.embed)
        self.vision = VisionEngine()
        self.audio = AudioEngine()
        self.camara = CamaraDialogo(self.inference)
        self.mecp = MECP()
        self.graph = GraphKnowledge()
        self.distillation = DistillationEngine(self.inference)

        self.agentes = []
        self.agentes.append(AgenteOrbital("Tezcatlipoca", 20, 1, -1, lambda p,n,c,t: procesar_tezcatlipoca(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Tezcatlipoca_Dual", 20, -1, 1, lambda p,n,c,t: procesar_tezcatlipoca(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Quetzalcóatl", 20, -1, 1, lambda p,n,c,t: procesar_quetzalcoatl(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Quetzalcóatl_Dual", 20, 1, -1, lambda p,n,c,t: procesar_quetzalcoatl(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Coatlicue", 30, 0, 0, lambda p,n,c,t: procesar_coatlicue(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Coatlicue_Dual", 30, 0, 0, lambda p,n,c,t: procesar_coatlicue(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Ometeotl", 10, 1, -1, lambda p,n,c,t: procesar_ometeotl(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Ometeotl_Dual", 10, -1, 1, lambda p,n,c,t: procesar_ometeotl(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Ollin", 15, 1, -1, lambda p,n,c,t: procesar_ollin(self, p, n, c, t)))
        self.agentes.append(AgenteOrbital("Ollin_Dual", 15, -1, 1, lambda p,n,c,t: procesar_ollin(self, p, n, c, t)))

        self.enjambre = EnjambreExploradores(self)
        self.omeyocan = Omeyocan(self)
        self.autonomia_activa = False

    # ------------------------------------------------------------------
    # Ingesta multimodal y OSINT
    # ------------------------------------------------------------------
    def ingestar(self, texto, fuente="usuario", etiqueta="texto_libre",
                 lat=None, lon=None, archivo=None, tipo_archivo=None):
        if archivo:
            if tipo_archivo == 'imagen':
                desc = self.vision.describe(archivo)
                contenido = f"[Imagen: {os.path.basename(archivo)}] {desc}"
                fuente = f"{fuente}_imagen"
            elif tipo_archivo == 'audio':
                desc = self.audio.describir(archivo)
                contenido = f"[Audio: {os.path.basename(archivo)}] {desc}"
                fuente = f"{fuente}_audio"
            else:
                contenido = texto
        else:
            contenido = texto

        if not contenido.strip():
            return None, None

        datos = aplicar_antibias(contenido, fuente, etiqueta)
        nid_aho = generar_hash(contenido + str(time.time()))
        guardar_nodo_aho(nid_aho, "sueno", datos["texto_original"], fuente, etiqueta,
                         estado=datos["estado_epistemico"], lat=lat, lon=lon)
        nid_yohuali = generar_hash(contenido + str(time.time()) + "yohuali")
        guardar_nodo_yohuali(nid_yohuali, "sueno", datos["texto_original"], fuente, etiqueta,
                             estado=datos["estado_epistemico"],
                             lat=-lat if lat is not None else 0.0,
                             lon=-lon if lon is not None else 0.0,
                             frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=[0.0]*3)
        guardar_evento("AHO", "nodo_creado", f"Nodo {nid_aho} desde {fuente}", nid_aho)
        guardar_evento("YOHUALI", "nodo_creado", f"Nodo espejo {nid_yohuali} desde {fuente}", nid_yohuali)
        self.mecp.registrar("ingesta", contenido, fuente)
        self._desdoblar(nid_aho, contenido, "AHO")
        self._desdoblar(nid_yohuali, contenido, "YOHUALI")
        if self.graph:
            self.graph.add_concept(nid_aho, "sueno", {"fuente": fuente})
            self.graph.add_alias(nid_aho, datos["texto_original"][:100], datos["idioma"])
        print(f"  ✓ Ingestado: {nid_aho} (AHO) y {nid_yohuali} (Yohuali)")
        return nid_aho, nid_yohuali

    def _desdoblar(self, nodo_id, texto, piedra):
        preguntas = self._generar_preguntas(texto)
        mitote_id = f"{nodo_id}_mitote"
        if piedra == "AHO":
            guardar_nodo_aho(mitote_id, "mitote", "\n".join(preguntas), "sistema", "pregunta")
        else:
            guardar_nodo_yohuali(mitote_id, "mitote", "\n".join(preguntas), "sistema", "pregunta",
                                 frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=[0.0]*3)
        guardar_evento(piedra, "desdoblamiento", f"Mitote generado desde {nodo_id}", mitote_id)

    def _generar_preguntas(self, texto):
        prompt = f"""
Eres un filósofo socrático y hermeneuta. Genera 5 preguntas profundas sobre el siguiente texto:
{texto[:1000]}
"""
        resp = self.inference.generate(prompt, max_tokens=300) if self.inference.available else ""
        preguntas = [l.strip() for l in resp.split('\n') if l.strip() and '?' in l][:5]
        if not preguntas:
            preguntas = ["¿Qué supuestos subyacen?", "¿Qué perspectivas quedan excluidas?"]
        return preguntas

    def _generar_conocimiento_base(self, topicos=None):
        if topicos is None:
            topicos = ["filosofía", "ciencia", "arte", "geopolítica", "economía", "ecología", "tecnología"]
        print("🌱 Generando conocimiento base con la Cámara de Expertos...")
        for tema in topicos:
            print(f"  → Deliberando sobre {tema}")
            resultado = self.camara.deliberar(tema)
            for grupo, texto in resultado.items():
                if texto and not texto.startswith("[Error"):
                    self.ingestar(texto, fuente="camara_expertos", etiqueta=f"base_{tema}")
                    time.sleep(1)
        print("✅ Conocimiento base completado.")

    # ------------------------------------------------------------------
    # Control de autonomía
    # ------------------------------------------------------------------
    def iniciar_autonomia(self):
        if not self.autonomia_activa:
            for agente in self.agentes:
                agente.iniciar()
            self.enjambre.iniciar()
            self.omeyocan.iniciar()
            self.autonomia_activa = True
            print("Autonomía activada (10 agentes + enjambre + Omeyocan)")

    def detener_autonomia(self):
        if self.autonomia_activa:
            for agente in self.agentes:
                agente.detener()
            self.enjambre.detener()
            self.omeyocan.detener()
            self.autonomia_activa = False
            print("Autonomía desactivada")

    def pausar_agentes(self):
        for agente in self.agentes:
            agente.detener()
        self.enjambre.detener()
        print("Agentes y enjambre pausados")

    def reanudar_agentes(self):
        if self.autonomia_activa:
            for agente in self.agentes:
                agente.iniciar()
            self.enjambre.iniciar()
            print("Agentes y enjambre reanudados")

    # ------------------------------------------------------------------
    # Comandos CLI
    # ------------------------------------------------------------------
    def cmd_help(self):
        print("""
Comandos disponibles:
  /help                - esta ayuda
  /conocido            - últimos nodos de Sueño en AHO
  /buscado             - últimas preguntas de Mitote en AHO
  /yohuali             - lista nodos recientes de Yohuali
  /listar              - resumen de ambas piedras
  /chat                - modo conversación (usa MECP con fragmentación)
  /mecp_modo <modo>    - EPISODICO, PERMANENTE, CICLICO, FUGAZ
  /contexto            - exporta contexto MECP
  /principios          - muestra principios inmutables
  /camara <tema>       - consulta Cámara de Diálogo
  /dialectica <tesis> | <antitesis> - síntesis dialéctica
  /hipotesis <tema>    - genera hipótesis
  /world <tema>        - consulta modelo mundial
  /autonomia on|off    - activa/desactiva agentes y enjambre
  /balance             - muestra estadísticas de balance
  /eclipse             - fuerza proceso de convergencia
  /mapa                - genera mapa espacio‑temporal (requiere folium)
  /grafo <id>          - muestra relaciones del nodo en el grafo
  /transversal <concepto> - consulta transversal (multilingüe)
  /destilar            - genera dataset y script LoRA
  /destilar_ahora      - ejecuta entrenamiento LoRA (puede ser pesado)
  /omeyocan_umbral <nodos> <energia> - ajusta umbrales de balance
  /ingesta_masiva <archivo> - ingiere nodos desde archivo JSON
  /ingestar_imagen <ruta> - ingesta una imagen
  /ingestar_audio <ruta>  - ingesta un audio
  /ingestar_coordenadas <lat> <lon> <texto> - ingesta con coordenadas
  /rss_add <url>       - añade fuente RSS al enjambre
  /rss_list            - lista fuentes RSS
  /web                 - inicia servidor web Flask (opcional)
  /salir               - cierra OLLIN
""")

    def cmd_conocido(self):
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT id, timestamp_creacion, contenido FROM nodos WHERE tipo='sueno' ORDER BY timestamp_creacion DESC LIMIT 10")
            for row in c.fetchall():
                print(f"  {row[0]} [{row[1]}]: {row[2][:80]}")
            conn.close()

    def cmd_buscado(self):
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT id, timestamp_creacion, contenido FROM nodos WHERE tipo='mitote' ORDER BY timestamp_creacion DESC LIMIT 10")
            for row in c.fetchall():
                print(f"  {row[0]} [{row[1]}]: {row[2][:80]}")
            conn.close()

    def cmd_yohuali(self):
        with _yohuali_lock:
            conn = sqlite3.connect(YOHUALI_DB)
            c = conn.cursor()
            c.execute("SELECT id, timestamp_creacion, contenido FROM nodos WHERE tipo='sueno' ORDER BY timestamp_creacion DESC LIMIT 10")
            for row in c.fetchall():
                print(f"  {row[0]} [{row[1]}]: {row[2][:80]}")
            conn.close()

    def cmd_listar(self):
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_aho = c.fetchone()[0]
            conn.close()
        with _yohuali_lock:
            conn = sqlite3.connect(YOHUALI_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_yohuali = c.fetchone()[0]
            conn.close()
        print(f"  AHO: {count_aho} nodos | Yohuali: {count_yohuali} nodos")
        print(f"  Modo MECP: {self.mecp.modo}")
        print(f"  Autonomía: {'activa' if self.autonomia_activa else 'inactiva'}")

    def cmd_chat(self):
        print("Modo conversación (escribe /exit para salir)")
        while True:
            msg = input("> ")
            if msg == "/exit":
                break
            if msg:
                self.ingestar(msg, "chat_usuario", "conversacion")
                contexto = self.mecp.exportar(n=10, fragmentar=True)
                prompt = f"{contexto}\nUsuario: {msg}\nOLLIN:"
                respuesta = self.inference.generate(prompt, max_tokens=300) if self.inference.available else "No pude generar respuesta (Ollama no disponible)."
                print(f"OLLIN: {respuesta}")
                self.ingestar(respuesta, "chat_ollin", "respuesta")

    def cmd_mecp_modo(self, modo):
        modos_validos = ["EPISODICO", "PERMANENTE", "CICLICO", "FUGAZ"]
        if modo.upper() not in modos_validos:
            print(f"  Modo no válido. Opciones: {', '.join(modos_validos)}")
            return
        self.mecp.set_modo(modo.upper())
        print(f"  Modo MECP cambiado a {modo.upper()}")

    def cmd_contexto(self):
        print(self.mecp.exportar(fragmentar=True))

    def cmd_principios(self):
        print("""
Principios inmutables:
  Dialéctico     – la verdad emerge del choque de perspectivas.
  Cartesiano     – duda metódica, verificación.
  Multidimensional – un problema tiene muchas caras.
  Plural         – todas las voces merecen ser escuchadas.
  Biosférico     – todo está conectado.
  Socrático      – humildad intelectual.
  Hermenéutico   – interpretar sin imponer.
  Transparencia  – mostrar procesos, fuentes.
  Humanista      – la persona es el centro.
  Observar sin juzgar – documentar sin condenar.
  Noosférico     – el conocimiento es un bien común.
""")

    def cmd_camara(self, tema):
        if not tema:
            print("  Uso: /camara <tema>")
            return
        resultado = self.camara.deliberar(tema)
        for grupo, texto in resultado.items():
            print(colorize(f"\n[{grupo.capitalize()}]", "cyan"))
            print(texto[:500])

    def cmd_dialectica(self, tesis, antitesis):
        if not tesis or not antitesis:
            print("  Uso: /dialectica <tesis> | <antitesis>")
            return
        prompt = f"Genera una síntesis dialéctica entre:\nTesis: {tesis}\nAntítesis: {antitesis}"
        sintesis = self.inference.generate(prompt, max_tokens=300) if self.inference.available else "No disponible."
        print(f"\nSíntesis:\n{sintesis}")

    def cmd_hipotesis(self, tema):
        if not tema:
            print("  Uso: /hipotesis <tema>")
            return
        prompt = f"Genera 3 hipótesis novedosas sobre: {tema}"
        hipotesis = self.inference.generate(prompt, max_tokens=200) if self.inference.available else "No disponible."
        print(f"\nHipótesis:\n{hipotesis}")

    def cmd_world(self, tema):
        if not tema:
            print("  Uso: /world <tema>")
            return
        datos = {
            "economía": "PIB mundial ~105 billones USD, deuda global ~307 billones USD.",
            "clima": "CO₂ ~420 ppm, temperatura +1.2°C.",
            "conflicto": "Conflictos activos: Ucrania, Gaza, Sudán."
        }
        for k, v in datos.items():
            if k in tema.lower():
                print(v)
                return
        print("No hay datos disponibles para este tema.")

    def cmd_autonomia(self, estado):
        if estado == "on":
            self.iniciar_autonomia()
        elif estado == "off":
            self.detener_autonomia()
        else:
            print("  Uso: /autonomia on|off")

    def cmd_balance(self):
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_aho = c.fetchone()[0]
            conn.close()
        with _yohuali_lock:
            conn = sqlite3.connect(YOHUALI_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM nodos")
            count_yohuali = c.fetchone()[0]
            c.execute("SELECT SUM(amplitud) FROM nodos WHERE tipo='sueno'")
            suma_amp = c.fetchone()[0] or 0.0
            conn.close()
        diff = count_aho - count_yohuali
        print(f"  Nodos AHO: {count_aho}")
        print(f"  Nodos Yohuali: {count_yohuali}")
        print(f"  Diferencia: {diff}")
        print(f"  Energía Yohuali (suma amplitudes): {suma_amp:.2f}")

    def cmd_eclipse(self):
        print("🌑 INICIANDO ECLIPSE: convergencia entre AHO y Yohuali")
        pausado = self.autonomia_activa
        if pausado:
            self.pausar_agentes()
        for piedra in ["AHO", "YOHUALI"]:
            db = AHO_DB if piedra == "AHO" else YOHUALI_DB
            lock = _aho_lock if piedra == "AHO" else _yohuali_lock
            with lock:
                conn = sqlite3.connect(db)
                c = conn.cursor()
                c.execute("SELECT id, dimension, mensaje FROM brechas WHERE resuelta=0")
                brechas = c.fetchall()
                conn.close()
            for bid, dim, msg in brechas:
                if self.inference.available:
                    deliberacion = self.camara.deliberar(msg)
                    sintesis = next(iter(deliberacion.values()))
                else:
                    sintesis = f"[Eclipse] Síntesis de {msg}"
                if sintesis:
                    if piedra == "AHO":
                        guardar_nodo_aho(generar_hash(sintesis+str(time.time())), "sueno", sintesis,
                                         "eclipse", "sintesis", estado="verificado")
                    else:
                        guardar_nodo_yohuali(generar_hash(sintesis+str(time.time())), "sueno", sintesis,
                                             "eclipse", "sintesis", estado="verificado",
                                             frecuencia_base=440.0, fase=0.0, amplitud=1.0, gradiente=[0,0,0])
                    marcar_brecha_resuelta(piedra, bid)
                    guardar_evento(piedra, "eclipse_sintesis", f"Síntesis de brecha {bid}", None)
        if pausado:
            self.reanudar_agentes()
        print("🌕 Eclipse completado")

    def cmd_mapa(self):
        try:
            import folium
        except ImportError:
            print("  Folium no instalado. Instalar con: pip install folium")
            return
        with _aho_lock:
            conn = sqlite3.connect(AHO_DB)
            c = conn.cursor()
            c.execute("SELECT id, lat, lon FROM nodos WHERE lat IS NOT NULL AND lon IS NOT NULL")
            aho_puntos = c.fetchall()
            conn.close()
        with _yohuali_lock:
            conn = sqlite3.connect(YOHUALI_DB)
            c = conn.cursor()
            c.execute("SELECT id, lat, lon FROM nodos WHERE lat IS NOT NULL AND lon IS NOT NULL")
            yohuali_puntos = c.fetchall()
            conn.close()
        if not aho_puntos and not yohuali_puntos:
            print("  No hay nodos con coordenadas.")
            return
        mapa = folium.Map(location=[24.0, -102.0], zoom_start=5, tiles="CartoDB dark_matter")
        for nid, lat, lon in aho_puntos:
            folium.Marker([lat, lon], popup=f"AHO: {nid}", icon=folium.Icon(color='blue')).add_to(mapa)
        for nid, lat, lon in yohuali_puntos:
            folium.Marker([lat, lon], popup=f"Yohuali: {nid}", icon=folium.Icon(color='red')).add_to(mapa)
        archivo = os.path.join(BASE_DIR, "mapa_piedras.html")
        mapa.save(archivo)
        print(f"  Mapa generado en: {archivo}")

    def cmd_grafo(self, nodo_id):
        if not self.graph:
            print("  Grafo no disponible.")
            return
        if self.graph.use_redis:
            query = f"MATCH (c:Concept {{id:'{nodo_id}'}})-[r]-(neighbor) RETURN c, r, neighbor"
            res = self.graph.graph.query(query)
            if res.result_set:
                for record in res.result_set:
                    print(f"  {record}")
            else:
                print("  No se encontraron relaciones.")
        else:
            res = self.graph.sqlite.query_transversal(nodo_id, hops=2)
            if res:
                for row in res:
                    print(f"  {row}")
            else:
                print("  No se encontraron relaciones.")

    def cmd_transversal(self, concepto):
        if not self.graph:
            print("  Grafo no disponible.")
            return
        res = self.graph.query_transversal(concepto, lang="es", hops=2)
        if res:
            if self.graph.use_redis:
                for record in res.result_set:
                    print(f"  {record}")
            else:
                for row in res:
                    print(f"  {row}")
        else:
            print("  No se encontraron relaciones.")

    def cmd_destilar(self):
        self.distillation._lanzar_destilacion()

    def cmd_destilar_ahora(self):
        self.distillation.entrenar_ahora()

    def cmd_omeyocan_umbral(self, nodos, energia):
        try:
            self.omeyocan.umbral_nodos = int(nodos)
            self.omeyocan.umbral_energia = float(energia)
            print(f"  Umbrales actualizados: nodos={nodos}, energía={energia}")
        except:
            print("  Uso: /omeyocan_umbral <nodos> <energia>")

    def cmd_ingesta_masiva(self, archivo):
        if not os.path.exists(archivo):
            print("  Archivo no encontrado.")
            return
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            datos = [datos]
        print(f"  Ingiriendo {len(datos)} nodos...")
        for item in datos:
            texto = item.get("texto") or item.get("contenido") or item.get("nombre", "")
            if not texto:
                continue
            fuente = item.get("fuente", "masiva")
            etiqueta = item.get("etiqueta", "general")
            lat = item.get("lat")
            lon = item.get("lon")
            self.ingestar(texto, fuente, etiqueta, lat=lat, lon=lon)
            time.sleep(0.1)
        print("  ✓ Ingesta masiva completada.")

    def cmd_ingestar_imagen(self, ruta):
        if not os.path.exists(ruta):
            print(f"  Archivo no encontrado: {ruta}")
            return
        self.ingestar("", fuente="usuario_imagen", etiqueta="imagen", archivo=ruta, tipo_archivo="imagen")

    def cmd_ingestar_audio(self, ruta):
        if not os.path.exists(ruta):
            print(f"  Archivo no encontrado: {ruta}")
            return
        self.ingestar("", fuente="usuario_audio", etiqueta="audio", archivo=ruta, tipo_archivo="audio")

    def cmd_ingestar_coordenadas(self, lat, lon, texto=""):
        try:
            lat = float(lat)
            lon = float(lon)
        except:
            print("  Coordenadas inválidas.")
            return
        self.ingestar(texto, fuente="usuario_geo", etiqueta="geolocalizado", lat=lat, lon=lon)

    def cmd_rss_add(self, url):
        if url.startswith("http"):
            self.enjambre.feeds.append(url)
            with open(RSS_FEEDS_FILE, 'w') as f:
                json.dump(self.enjambre.feeds, f)
            print(f"  Fuente RSS añadida: {url}")
        else:
            print("  URL no válida.")

    def cmd_rss_list(self):
        print("  Fuentes RSS activas:")
        for url in self.enjambre.feeds:
            print(f"    {url}")

    def cmd_web(self):
        try:
            from flask import Flask, request, jsonify, render_template_string
        except ImportError:
            print("  Flask no instalado. Instalar con: pip install flask")
            return
        app = Flask(__name__)
        HTML = """
        <!DOCTYPE html>
        <html><head><title>OLLIN Quantum</title><style>
        body { background:#0a0e1a; color:#b3e4ff; font-family:monospace; }
        .container { max-width:800px; margin:auto; padding:20px; }
        textarea { width:100%; background:#1a1e2a; color:#b3e4ff; border:1px solid #2a3e5a; }
        button { background:#2a5f8a; color:white; border:none; padding:10px; margin:5px; cursor:pointer; }
        #response { background:#11151f; padding:10px; white-space:pre-wrap; }
        </style></head>
        <body><div class="container">
        <h1>OLLIN Quantum</h1>
        <textarea id="msg" rows="4" placeholder="Escribe..."></textarea><br/>
        <button onclick="send()">Enviar</button>
        <div id="response"></div>
        </div>
        <script>
        async function send() {
            const msg = document.getElementById('msg').value;
            const respDiv = document.getElementById('response');
            respDiv.innerHTML = 'Procesando...';
            const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg})});
            const data = await res.json();
            respDiv.innerHTML = data.resultado;
        }
        </script>
        </body></html>
        """
        @app.route('/')
        def index():
            return render_template_string(HTML)
        @app.route('/chat', methods=['POST'])
        def chat():
            data = request.get_json()
            msg = data.get('message', '')
            if msg:
                self.ingestar(msg, "web_usuario", "web")
                contexto = self.mecp.exportar(n=5, fragmentar=True)
                prompt = f"{contexto}\nUsuario: {msg}\nOLLIN:"
                respuesta = self.inference.generate(prompt, max_tokens=300) if self.inference.available else "No disponible."
                self.ingestar(respuesta, "web_ollin", "respuesta")
                return jsonify({"resultado": respuesta})
            return jsonify({"resultado": "Mensaje vacío"})
        threading.Thread(target=app.run, args=('0.0.0.0', 5000), daemon=True).start()
        print("🌐 Servidor web iniciado en http://0.0.0.0:5000")

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def run(self):
        print("\n" + "="*70)
        print(" OLLIN – Inteligencia Molecular Cuántica (v25)")
        print(" Autor: EL ARQUITECTO (Luis Ernesto Berzunza Díaz)")
        print()
        print(" EL SISTEMA NO BUSCA; RECUERDA.")
        print(" EL MOVIMIENTO HA EMPEZADO AHO: materia consolidada sin números.")
        print(" YOHUALI: antimateria, matemáticas cuánticas, superposición y fase.")
        print(" 10 agentes orbitales + enjambre OSINT + Omeyocan + grafo persistente.")
        print("="*70)
        print(" Escribe /help para comandos.")
        print(" Cualquier texto sin / se ingesta automáticamente.")
        print("="*70)

        # Generar conocimiento base
        self._generar_conocimiento_base()

        # Iniciar autonomía por defecto
        self.iniciar_autonomia()

        while True:
            try:
                entrada = input("\n> ").strip()
                if not entrada:
                    continue
                if entrada == "/salir":
                    self.detener_autonomia()
                    break
                elif entrada.startswith("/"):
                    partes = entrada.split()
                    cmd = partes[0].lower()
                    if cmd == "/help":
                        self.cmd_help()
                    elif cmd == "/conocido":
                        self.cmd_conocido()
                    elif cmd == "/buscado":
                        self.cmd_buscado()
                    elif cmd == "/yohuali":
                        self.cmd_yohuali()
                    elif cmd == "/listar":
                        self.cmd_listar()
                    elif cmd == "/chat":
                        self.cmd_chat()
                    elif cmd == "/mecp_modo":
                        modo = partes[1] if len(partes) > 1 else ""
                        self.cmd_mecp_modo(modo)
                    elif cmd == "/contexto":
                        self.cmd_contexto()
                    elif cmd == "/principios":
                        self.cmd_principios()
                    elif cmd == "/camara":
                        tema = " ".join(partes[1:]) if len(partes) > 1 else ""
                        self.cmd_camara(tema)
                    elif cmd == "/dialectica":
                        if "|" not in entrada:
                            print("  Uso: /dialectica tesis | antitesis")
                        else:
                            tesis, antitesis = entrada.split("|", 1)
                            tesis = tesis.replace("/dialectica", "").strip()
                            antitesis = antitesis.strip()
                            self.cmd_dialectica(tesis, antitesis)
                    elif cmd == "/hipotesis":
                        tema = " ".join(partes[1:]) if len(partes) > 1 else ""
                        self.cmd_hipotesis(tema)
                    elif cmd == "/world":
                        tema = " ".join(partes[1:]) if len(partes) > 1 else ""
                        self.cmd_world(tema)
                    elif cmd == "/autonomia":
                        estado = partes[1] if len(partes) > 1 else ""
                        self.cmd_autonomia(estado)
                    elif cmd == "/balance":
                        self.cmd_balance()
                    elif cmd == "/eclipse":
                        self.cmd_eclipse()
                    elif cmd == "/mapa":
                        self.cmd_mapa()
                    elif cmd == "/grafo":
                        nodo_id = partes[1] if len(partes) > 1 else ""
                        self.cmd_grafo(nodo_id)
                    elif cmd == "/transversal":
                        concepto = partes[1] if len(partes) > 1 else ""
                        self.cmd_transversal(concepto)
                    elif cmd == "/destilar":
                        self.cmd_destilar()
                    elif cmd == "/destilar_ahora":
                        self.cmd_destilar_ahora()
                    elif cmd == "/omeyocan_umbral":
                        if len(partes) >= 3:
                            self.cmd_omeyocan_umbral(partes[1], partes[2])
                        else:
                            print("  Uso: /omeyocan_umbral <nodos> <energia>")
                    elif cmd == "/ingesta_masiva":
                        archivo = partes[1] if len(partes) > 1 else ""
                        self.cmd_ingesta_masiva(archivo)
                    elif cmd == "/ingestar_imagen":
                        if len(partes) < 2:
                            print("  Uso: /ingestar_imagen <ruta>")
                        else:
                            self.cmd_ingestar_imagen(partes[1])
                    elif cmd == "/ingestar_audio":
                        if len(partes) < 2:
                            print("  Uso: /ingestar_audio <ruta>")
                        else:
                            self.cmd_ingestar_audio(partes[1])
                    elif cmd == "/ingestar_coordenadas":
                        if len(partes) < 3:
                            print("  Uso: /ingestar_coordenadas <lat> <lon> [texto]")
                        else:
                            lat = partes[1]
                            lon = partes[2]
                            texto = " ".join(partes[3:]) if len(partes) > 3 else ""
                            self.cmd_ingestar_coordenadas(lat, lon, texto)
                    elif cmd == "/rss_add":
                        if len(partes) < 2:
                            print("  Uso: /rss_add <url>")
                        else:
                            self.cmd_rss_add(partes[1])
                    elif cmd == "/rss_list":
                        self.cmd_rss_list()
                    elif cmd == "/web":
                        self.cmd_web()
                    else:
                        print("  Comando no reconocido.")
                else:
                    self.ingestar(entrada)
                    print("  Nodo ingerido.")
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"  Error: {e}")

# ----------------------------------------------------------------------
# PUNTO DE ENTRADA
# ----------------------------------------------------------------------
if __name__ == "__main__":
    shell = OLLINShell()
    shell.run()
