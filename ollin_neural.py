
"""
OLLIN v5.5 Neural - Arquitectura Cosmologica + 5 Capas Neurales
================================================================
Autor y titular : Luis Ernesto Berzunza Diaz
Ciudad de Mexico - 17 marzo 2026
Herramientas    : Claude Sonnet 4.6 - DeepSeek - Ollama

5 Capas Neurales (todas con fallback gracioso):
  C1. Encoder         -- sentence-transformers all-MiniLM-L6-v2
  C2. VectorStore     -- ChromaDB (busqueda por significado)
  C3. LLMLocal        -- Ollama llama3/mistral/phi3
  C4. Consolidador    -- scikit-learn K-Means en el Sueno
  C5. Grafo           -- networkx red semantica de nodos

Instalar:
  pip install -r requirements_neural.txt
  ollama pull llama3
  python ollin_neural.py
"""

from __future__ import annotations
import os, json, sqlite3, hashlib, uuid, threading, datetime, random, math
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

try: from dotenv import load_dotenv; load_dotenv()
except ImportError: pass

# ── Deteccion de capas disponibles ──────────────────────────
_ST=_CHROMA=_OLLAMA=_SK=_NX=_CLAUDE=_DEEPSEEK = False
_SentenceTransformer = None
_chromadb_mod = None
_ollama_mod = None
_KMeans = None
_np = None
_nx_mod = None

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    _ST = True
except ImportError: pass

try:
    import chromadb as _chromadb_mod
    _CHROMA = True
except ImportError: pass

try:
    import ollama as _ollama_mod
    _OLLAMA = True
except ImportError: pass

try:
    from sklearn.cluster import KMeans as _KMeans
    import numpy as _np
    _SK = True
except ImportError: pass

try:
    import networkx as _nx_mod
    _NX = True
except ImportError: pass

try: import anthropic as _ant; _CLAUDE = True
except ImportError: pass
try: import openai as _oai; _DEEPSEEK = True
except ImportError: pass


# ══════════════════════════════════════════════════════════════
# ENUMERACIONES Y CONSTANTES
# ══════════════════════════════════════════════════════════════

class Etiqueta(Enum):
    VERIFICADO="VERIFICADO"; CORROBORADO="CORROBORADO"; PLAUSIBLE="PLAUSIBLE"
    ESPECULATIVO="ESPECULATIVO"; CONTROVERTIDO="CONTROVERTIDO"
    OMISION_HISTORICA="OMISION_HISTORICA"; REVISADO="REVISADO"

class TipoMemoria(Enum):
    PERMANENTE="PERMANENTE"; CICLICA="CICLICA"; EFIMERA="EFIMERA"

CARPETAS = [
    "personajes_historicos","historia_universal","conocimiento_cientifico",
    "infraestructura_mundial","redes_poder","omisiones_historicas",
    "hipotesis_operativas","escenarios_posibles","perfilamiento_actores",
    "archivos_clasificados","datos_valores_numericos",
]
DIMS = ["ontologica","epistemologica","etica","politica","estetica","cosmologica","pragmatica"]
ETIQUETA_CLI = {
    "v":Etiqueta.VERIFICADO,"c":Etiqueta.CORROBORADO,"p":Etiqueta.PLAUSIBLE,
    "e":Etiqueta.ESPECULATIVO,"x":Etiqueta.CONTROVERTIDO,"o":Etiqueta.OMISION_HISTORICA,
}


# ══════════════════════════════════════════════════════════════
# NODO
# ══════════════════════════════════════════════════════════════

@dataclass
class Nodo:
    contenido:str; etiqueta:Etiqueta=Etiqueta.ESPECULATIVO
    carpeta:str="hipotesis_operativas"; memoria:TipoMemoria=TipoMemoria.PERMANENTE
    origen:str="EXTERNO"
    id:str=field(default_factory=lambda:str(uuid.uuid4())[:8])
    timestamp:str=field(default_factory=lambda:datetime.datetime.utcnow().isoformat())
    version_anterior:Optional[str]=None
    hash:str=field(init=False)

    def __post_init__(self):
        self.hash=hashlib.sha256(
            f"{self.contenido}{self.etiqueta.value}{self.timestamp}".encode()
        ).hexdigest()[:16]

    def espejo(self):
        return Nodo(contenido=self.contenido, etiqueta=self.etiqueta,
                    carpeta=self.carpeta, memoria=self.memoria,
                    origen=f"ESPEJO:{self.origen}", timestamp=self.timestamp,
                    id=f"{self.id}-ESP")

    def to_dict(self):
        return {"id":self.id,"contenido":self.contenido,"etiqueta":self.etiqueta.value,
                "carpeta":self.carpeta,"memoria":self.memoria.value,"origen":self.origen,
                "timestamp":self.timestamp,"hash":self.hash,"version_anterior":self.version_anterior}

@dataclass
class Experto:
    nombre:str; dominio:str; posicion:str; especialidad:str=""

@dataclass
class Sabio:
    nombre:str; tradicion:str; aporte:str


# ══════════════════════════════════════════════════════════════
# 46 EXPERTOS + 65 SABIOS
# ══════════════════════════════════════════════════════════════

EXPERTOS = [
    Experto("Huitzilin Cronica","Historia","estandar","Critica de fuentes y veracidad documental"),
    Experto("Xochitl Palabra","Historia","P3:voz_periferica","Historia oral y tradicion no escrita"),
    Experto("Dr. Olmedo Roca","Historia","estandar","Arqueologia y cultura material"),
    Experto("Contrahistoria","Historia","P1:oponente","Relato disidente y revisionismo critico"),
    Experto("Tlamatini Cero","Filosofia","P3:voz_periferica","Filosofia nahuatl y pensamiento mesoamericano"),
    Experto("Episteme Viva","Filosofia","P1:oponente","Epistemologia critica y teoria del conocimiento"),
    Experto("Logos Dual","Filosofia","estandar","Filosofia analitica y logica formal"),
    Experto("Dra. Tiempo Abierto","Filosofia","estandar","Fenomenologia y hermeneutica"),
    Experto("Dr. Numero Primo","Ciencias","estandar","Matematicas y teoria de la complejidad"),
    Experto("Cuanto Incierto","Ciencias","P1:oponente","Fisica cuantica e incertidumbre"),
    Experto("Dra. Estrella Fija","Ciencias","estandar","Astronomia y cosmologia fisica"),
    Experto("Dr. Codigo Vivo","Ciencias","estandar","Biologia computacional y sistemas complejos"),
    Experto("Mercado Libre","Economia","estandar","Economia neoclasica y teoria de mercados"),
    Experto("Dra. Raiz Comun","Economia","P3:voz_periferica","Economia del buen vivir y desarrollo comunitario"),
    Experto("Dr. Crisis Permanente","Economia","P1:oponente","Economia heterodoxa y critica al capitalismo"),
    Experto("Dr. Estado Nacion","Politica","estandar","Ciencia politica e instituciones"),
    Experto("Dra. Poder Subterraneo","Politica","estandar","Geopolitica y analisis de poder"),
    Experto("Sin Estado","Politica","P1:oponente","Teoria anarquista y critica al Estado"),
    Experto("Dra. Norma Viva","Derecho","estandar","Derecho constitucional y garantias"),
    Experto("Dr. Derecho Propio","Derecho","P3:voz_periferica","Derechos de pueblos originarios"),
    Experto("Dra. Sombra Legal","Derecho","P1:oponente","Criminologia critica y derecho penal"),
    Experto("Dr. Cuerpo Entero","Medicina","estandar","Medicina general e integrada"),
    Experto("Dra. Mente Profunda","Medicina","estandar","Psiquiatria y salud mental"),
    Experto("Curandera del Camino","Medicina","P3:voz_periferica","Medicina tradicional y etnobotanica"),
    Experto("Dra. Critica Total","Arte","estandar","Critica de arte y estetica"),
    Experto("Dr. Ritmo y Forma","Arte","estandar","Musicologia y analisis sonoro"),
    Experto("Tlacuilo Hablante","Arte","P3:voz_periferica","Narracion oral y arte pictografico mesoamericano"),
    Experto("Dr. Sistema Abierto","Tecnologia","estandar","Ingenieria de sistemas y software libre"),
    Experto("Dra. Red Neuronal","Tecnologia","P1:oponente","Inteligencia artificial y critica algoritmica"),
    Experto("El Tejedor","Tecnologia","P1:oponente","Hacking etico y seguridad de la informacion"),
    Experto("Dra. Ciudad Viva","Sociologia","estandar","Sociologia urbana y espacio publico"),
    Experto("Dr. Masa Critica","Sociologia","estandar","Demografia critica y analisis de poblaciones"),
    Experto("Dra. Tejido Social","Sociologia","P3:voz_periferica","Analisis cultural y comunidades marginadas"),
    Experto("Dr. Mapa Mental","Psicologia","estandar","Psicologia cognitiva y ciencias del comportamiento"),
    Experto("Dra. Sombra Interior","Psicologia","P1:oponente","Psicoanalisis jungiano e inconsciente colectivo"),
    Experto("Dr. Cerebro Vivo","Psicologia","estandar","Neuropsicologia y bases neurales del conocimiento"),
    Experto("Dr. Origen Comun","Antropologia","estandar","Antropologia fisica y evolucion humana"),
    Experto("Dra. Campo Abierto","Antropologia","P3:voz_periferica","Etnografia y trabajo de campo"),
    Experto("Dr. Palabra Madre","Antropologia","estandar","Linguistica y origen del lenguaje"),
    Experto("Dra. Raiz Profunda","Medio ambiente","estandar","Ecologia y sistemas naturales"),
    Experto("Dr. Clima Roto","Medio ambiente","P1:oponente","Climatologia y crisis ambiental"),
    Experto("Dra. Mar Sin Fondo","Medio ambiente","estandar","Biologia marina y oceanos"),
    Experto("Fr. Logos Eterno","Espiritualidad","estandar","Teologia comparativa y mistica"),
    Experto("Marakame del Norte","Espiritualidad","P3:voz_periferica","Chamanismo huichol y conocimiento sagrado"),
    Experto("Dr. Philosophia","Espiritualidad","estandar","Filosofia perenne y tradiciones sapienciales"),
    Experto("Dra. Mithos Vivo","Espiritualidad","P1:oponente","Mitologia comparada y estructura del relato sagrado"),
]

SABIOS = [
    Sabio("Nezahualcoyotl","Nahuatl","Poesia como filosofia y el conocimiento del corazon"),
    Sabio("Sor Juana Ines de la Cruz","Novohispana","Primera voz critica del Nuevo Mundo"),
    Sabio("Popol Vuh","Maya Kiche","La creacion como proceso dialectico"),
    Sabio("Chilam Balam","Maya Yucateco","Profecia y memoria ciclica del tiempo"),
    Sabio("Tlacaelel","Mexica","Arquitectura del pensamiento cosmologico"),
    Sabio("Cuauhtemoc","Mexica","La resistencia como forma de conocimiento"),
    Sabio("Tonantzin","Nahuatl","El principio femenino como fundamento"),
    Sabio("El Viejo Antonio","Zapatista","Sabiduria oral y la pregunta como metodo"),
    Sabio("Pablo Gonzalez Casanova","Latinoamerica","Democracia interna y colonialismo del poder"),
    Sabio("Leopoldo Zea","Latinoamerica","La filosofia de lo americano"),
    Sabio("Jose Marti","Cubana","Nuestra America como proyecto epistemico"),
    Sabio("Frida Kahlo","Mexicana","El cuerpo como territorio de conocimiento"),
    Sabio("Eduardo Galeano","Latinoamerica","Las venas abiertas como memoria"),
    Sabio("Octavio Paz","Mexicana","El laberinto como estructura del ser"),
    Sabio("Maria Sabina","Mazateca","Los hongos sagrados y el conocimiento no ordinario"),
    Sabio("Socrates","Griega","El no saber como puerta al conocimiento"),
    Sabio("Heraclito","Griega","El flujo perpetuo como unica constante"),
    Sabio("Hipatia de Alejandria","Alejandrina","El conocimiento femenino silenciado por la historia"),
    Sabio("Epicuro","Griega","El conocimiento al servicio de la vida"),
    Sabio("Diogenes de Sinope","Griega","La irreverencia como herramienta epistemica"),
    Sabio("Pitagoras","Griega","El numero como lenguaje del universo"),
    Sabio("Empedocles","Griega","Los cuatro elementos como sistema"),
    Sabio("Aristoteles","Griega","La clasificacion como forma de conocer"),
    Sabio("Platon","Griega","Las ideas como realidad profunda"),
    Sabio("Parmenides","Griega","El ser como fundamento inmutable"),
    Sabio("Confucio","China","El orden social como conocimiento practico"),
    Sabio("Lao Tse","China","El vacio como contenedor de toda posibilidad"),
    Sabio("Buda Gautama","India","El sufrimiento como puerta al conocimiento"),
    Sabio("Nagarjuna","India","La vacuidad de la vacuidad como metodo"),
    Sabio("Sun Tzu","China","La estrategia como conocimiento del flujo"),
    Sabio("Ibn Rushd","Islamica","El que preservo el conocimiento griego para el mundo"),
    Sabio("Al-Biruni","Islamica","El viajero del conocimiento universal"),
    Sabio("Rumi","Persa-Islamica","El conocimiento que no puede contenerse sin bailar"),
    Sabio("Kukai","Japonesa","El lenguaje como universo y el universo como lenguaje"),
    Sabio("Matsuo Basho","Japonesa","La impermanencia como unica verdad"),
    Sabio("Ibn Jaldu","Arabe-Africana","Padre de la sociologia: el conocimiento como ciclo"),
    Sabio("Sundiata Keita","Mandinga","La historia oral como verdad mas fiel que el documento"),
    Sabio("Imhotep","Egipcia","El primer genio universal de la historia"),
    Sabio("Mansa Musa","Mali","La riqueza como vehiculo de conocimiento"),
    Sabio("Nefertiti","Egipcia","El poder femenino como conocimiento visible"),
    Sabio("Ibn Battuta","Arabe-Africana","El mundo entero como texto a leer"),
    Sabio("Frantz Fanon","Caribena-Africana","El colonizado que se conoce libera al colonizador"),
    Sabio("Cheikh Anta Diop","Africana","Africa como cuna del conocimiento universal"),
    Sabio("Miriam Makeba","Africana","La voz como resistencia epistemica"),
    Sabio("Thomas Sankara","Africana","El conocimiento como acto politico de liberacion"),
    Sabio("Baruch Spinoza","Holandesa","Dios como naturaleza y la etica como geometria"),
    Sabio("Giordano Bruno","Italiana","Quemado por un conocimiento demasiado verdadero"),
    Sabio("Leonardo da Vinci","Renacentista","El conocimiento sin fronteras disciplinarias"),
    Sabio("Marie Curie","Polaco-Francesa","La que midio lo invisible y pago el precio"),
    Sabio("Nikola Tesla","Serbia-Americana","El que capto la frecuencia que otros no oian"),
    Sabio("Simone de Beauvoir","Francesa","El genero como epistemologia"),
    Sabio("Antonio Gramsci","Italiana","El intelectual organico como agente del conocimiento"),
    Sabio("Walter Benjamin","Alemana","La historia de los vencidos como conocimiento verdadero"),
    Sabio("Hannah Arendt","Alemana","El mal como banalidad y el pensamiento como resistencia"),
    Sabio("Michel Foucault","Francesa","El poder como saber y el saber como poder"),
    Sabio("Vandana Shiva","India","Las semillas como conocimiento y como resistencia"),
    Sabio("Noam Chomsky","Estadounidense","El lenguaje como estructura del pensamiento"),
    Sabio("bell hooks","Afroamericana","El amor como epistemologia y la pedagogia critica"),
    Sabio("Carl Sagan","Estadounidense","El cosmos como hogar y la ciencia como humildad"),
    Sabio("Richard Feynman","Estadounidense","El placer de entender como motor del conocimiento"),
    Sabio("Octavia Butler","Afroamericana","El futuro como forma de recordar el presente"),
    Sabio("Carlos Monsivais","Mexicana","La cultura popular como conocimiento legitimo"),
    Sabio("Rigoberta Menchu","Maya Kiche","El testimonio como epistemologia de los sobrevivientes"),
    Sabio("Paulo Freire","Brasilena","La pedagogia del oprimido como conocimiento liberador"),
    Sabio("Arundhati Roy","India","La belleza y la justicia como conocimientos inseparables"),
]

NODOS_SEMILLA = {
    "personajes_historicos":[
        ("Nezahualcoyotl: poeta-rey de Texcoco. Sus poemas son la primera filosofia documentada del Mexico antiguo.",Etiqueta.VERIFICADO),
        ("Sor Juana Ines de la Cruz: primera intelectual del Nuevo Mundo. Defendio el derecho de las mujeres al conocimiento en el siglo XVII.",Etiqueta.VERIFICADO),
        ("Cuauhtemoc: ultimo tlatoani mexica. Su resistencia es el primer acto documentado de soberania epistemica indigena ante la conquista.",Etiqueta.VERIFICADO),
    ],
    "historia_universal":[
        ("El Quinto Sol nahuatl: Nahui Ollin es nuestra era. Termina con transformacion, no con destruccion.",Etiqueta.CORROBORADO),
        ("La destruccion de los codices mesoamericanos (1521, 1562) es uno de los mayores actos de destruccion del conocimiento humano.",Etiqueta.VERIFICADO),
        ("La Revolucion Mexicana (1910-1920): primer conflicto del siglo XX con componente agrario e indigena explicito.",Etiqueta.CONTROVERTIDO),
    ],
    "conocimiento_cientifico":[
        ("El principio de incertidumbre de Heisenberg: es imposible conocer simultaneamente posicion y momento de una particula con precision arbitraria.",Etiqueta.VERIFICADO),
        ("La teoria de la evolucion por seleccion natural (Darwin-Wallace, 1858) es la base de toda la biologia moderna.",Etiqueta.VERIFICADO),
        ("La relatividad del tiempo (Einstein, 1905): el tiempo transcurre a ritmos distintos segun velocidad relativa y gravedad.",Etiqueta.VERIFICADO),
    ],
    "infraestructura_mundial":[
        ("Las rutas comerciales prehispanicas conectaban desde el suroeste de Norteamerica hasta Centroamerica. El cacao y la obsidiana eran monedas de conocimiento.",Etiqueta.CORROBORADO),
        ("Las chinampas aztecas sostuvieron a mas de 200,000 personas en Tenochtitlan. Tecnologia ignorada sistematicamente por los colonizadores.",Etiqueta.VERIFICADO),
        ("Las redes digitales concentran el 90% del trafico en menos de 20 corporaciones. La infraestructura del conocimiento replica la desigualdad fisica.",Etiqueta.CORROBORADO),
    ],
    "redes_poder":[
        ("Los sacerdotes-astronomos mexicas controlaban el tiempo calendrico y por tanto la legitimidad del poder politico.",Etiqueta.CORROBORADO),
        ("El sistema colonial de castas novohispano: 16 categorias raciales que determinaban derechos y acceso al conocimiento.",Etiqueta.VERIFICADO),
        ("Las cinco mayores empresas tecnologicas controlan mas datos sobre la poblacion global que la mayoria de los gobiernos nacionales.",Etiqueta.CORROBORADO),
    ],
    "omisiones_historicas":[
        ("Se estima que existian miles de codices mesoamericanos. Solo sobreviven 15 de origen prehispanico.",Etiqueta.CORROBORADO),
        ("Efecto Matilda: logros cientificos de mujeres atribuidos a hombres. Rosalind Franklin (ADN), Lise Meitner (fision nuclear), Cecilia Payne (composicion del sol).",Etiqueta.VERIFICADO),
        ("El 40% de las culturas humanas carecen de registro escrito. Eso no significa que carecieran de conocimiento.",Etiqueta.CORROBORADO),
    ],
    "hipotesis_operativas":[
        ("La arquitectura espejo de OLLIN permite que el conocimiento crezca indefinidamente sin perder coherencia: cada nodo conoce su lugar porque tiene su reflejo exacto.",Etiqueta.ESPECULATIVO),
        ("La dualidad como principio universal: desde la fisica de particulas hasta la cosmologia nahuatl, aparece como estructura en sistemas de conocimiento radicalmente distintos.",Etiqueta.PLAUSIBLE),
        ("AHO como metafora del temazcal: expansivo pero contenido, purificador pero preservador.",Etiqueta.ESPECULATIVO),
    ],
    "escenarios_posibles":[
        ("OLLIN podria ser la primera enciclopedia que registra con igual rigor lo que la academia reconoce y lo que la academia ignora.",Etiqueta.ESPECULATIVO),
        ("Con embeddings semanticos, OLLIN puede detectar que dos nodos son sobre el mismo tema aunque usen palabras completamente distintas.",Etiqueta.PLAUSIBLE),
        ("El grafo de conocimiento de OLLIN podria revelar conexiones entre tradiciones epistemicas que nunca se comunicaron historicamente.",Etiqueta.ESPECULATIVO),
    ],
    "perfilamiento_actores":[
        ("Luis Ernesto Berzunza Diaz construyo OLLIN sin laboratorio ni financiamiento. Desde un Pixel 7 Pro y una ThinkPad X1 Carbon usados.",Etiqueta.VERIFICADO),
        ("Los guardianes de la memoria oral en culturas sin escritura son equivalentes funcionales de las bibliotecas.",Etiqueta.CORROBORADO),
        ("Los hackers eticos son los unicos actores que sistematicamente prueban la integridad de los sistemas de informacion.",Etiqueta.PLAUSIBLE),
    ],
    "archivos_clasificados":[
        ("Documento fundacional OLLIN v5.5: Ciudad de Mexico, 17 marzo 2026. Autor: Luis Ernesto Berzunza Diaz.",Etiqueta.VERIFICADO),
        ("Herramientas: Claude Sonnet 4.6 (Anthropic, gratuito) y DeepSeek como espejo tecnologico.",Etiqueta.VERIFICADO),
        ("Registros de autoria: Safe Creative, Gmail timestamp, Google Drive timestamp, INDAUTOR.",Etiqueta.VERIFICADO),
    ],
    "datos_valores_numericos":[
        ("Camara Dialectica: 46 expertos en 14 dominios + 65 sabios de 6 tradiciones = 111 voces totales.",Etiqueta.VERIFICADO),
        ("AHO: 11 repositorios. 33 nodos semilla por lado = 66 nodos estado inicial.",Etiqueta.VERIFICADO),
        ("Arquitectura neural: 5 capas. Umbral de similitud semantica: 0.72. Consolidacion cada 10 nodos nuevos.",Etiqueta.VERIFICADO),
    ],
}


# ══════════════════════════════════════════════════════════════
# CAPA 1 — ENCODER SEMANTICO
# Fallback: vectores hash de 128 dims si sentence-transformers no disponible
# ══════════════════════════════════════════════════════════════

class Encoder:
    MODELO = "all-MiniLM-L6-v2"

    def __init__(self):
        self._modelo = None
        self.modo = "hash-128d"
        if _ST:
            try:
                self._modelo = _SentenceTransformer(self.MODELO)
                self.modo = f"sentence-transformers:{self.MODELO}"
            except Exception as e:
                print(f"  [Encoder] Fallback hash: {e}")

    def codificar(self, texto:str) -> list:
        if self._modelo:
            return self._modelo.encode(texto, convert_to_numpy=True).tolist()
        return self._hash_encode(texto)

    def _hash_encode(self, texto:str) -> list:
        vec = [0.0] * 128
        words = texto.lower().split()
        for w in words:
            h = int(hashlib.md5(w.encode()).hexdigest(), 16) % 128
            vec[h] += 1.0
        total = sum(vec) or 1.0
        return [v/total for v in vec]

    @staticmethod
    def cosine(a:list, b:list) -> float:
        dot = sum(x*y for x,y in zip(a,b))
        ma  = math.sqrt(sum(x*x for x in a)) or 1.0
        mb  = math.sqrt(sum(x*x for x in b)) or 1.0
        return dot/(ma*mb)


# ══════════════════════════════════════════════════════════════
# CAPA 2 — VECTOR STORE
# Fallback: busqueda coseno en memoria si ChromaDB no disponible
# ══════════════════════════════════════════════════════════════

class VectorStore:
    def __init__(self, encoder:Encoder, path:str="./chroma_ollin"):
        self._enc = encoder
        self._coll = None
        self._mem:dict[str,dict] = {}
        self.modo = "in-memory-cosine"

        if _CHROMA:
            try:
                client = _chromadb_mod.PersistentClient(path=path)
                self._coll = client.get_or_create_collection(
                    name="aho", metadata={"hnsw:space":"cosine"})
                self.modo = "chromadb"
            except Exception as e:
                print(f"  [VectorStore] Fallback memoria: {e}")

    def agregar(self, nodo:Nodo, emb:list):
        self._mem[nodo.id] = {"emb":emb,"contenido":nodo.contenido,
                               "carpeta":nodo.carpeta,"etiqueta":nodo.etiqueta.value}
        if self._coll:
            try:
                self._coll.upsert(ids=[nodo.id], embeddings=[emb],
                    documents=[nodo.contenido[:500]],
                    metadatas=[{"carpeta":nodo.carpeta,"etiqueta":nodo.etiqueta.value}])
            except Exception: pass

    def buscar(self, query:str, n:int=6, carpeta:str=None) -> list:
        emb = self._enc.codificar(query)
        if self._coll:
            try:
                kw = {}
                if carpeta: kw["where"] = {"carpeta":carpeta}
                count = self._coll.count()
                if count == 0: return []
                res = self._coll.query(query_embeddings=[emb],
                    n_results=min(n,count), **kw)
                out = []
                for i,doc in enumerate(res["documents"][0]):
                    out.append({"id":res["ids"][0][i],"contenido":doc[:80],
                                "score":round(1-res["distances"][0][i],3)})
                return out
            except Exception: pass
        scored = sorted(
            ((nid, Encoder.cosine(emb,d["emb"]), d) for nid,d in self._mem.items()
             if not carpeta or d["carpeta"]==carpeta),
            key=lambda x: x[1], reverse=True)
        return [{"id":nid,"contenido":d["contenido"][:80],"score":round(sc,3)}
                for nid,sc,d in scored[:n] if sc > 0.1]

    def conteo(self) -> int:
        if self._coll:
            try: return self._coll.count()
            except: pass
        return len(self._mem)


# ══════════════════════════════════════════════════════════════
# CAPA 3 — LLM LOCAL
# Prioridad: Ollama > Claude API > DeepSeek API > simulado
# ══════════════════════════════════════════════════════════════

class LLMLocal:
    MODELOS_OLLAMA = ["llama3","mistral","phi3","gemma2","qwen2","llama2"]

    def __init__(self):
        self._ollama_modelo = None
        self._claude  = None
        self._deepseek = None
        self.modo = "simulado"
        self._detectar()

    def _detectar(self):
        if _OLLAMA:
            try:
                resp = _ollama_mod.list()
                disponibles = [m.model for m in (resp.models if hasattr(resp,"models") else [])]
                for pref in self.MODELOS_OLLAMA:
                    for d in disponibles:
                        if pref in d.lower():
                            self._ollama_modelo = d
                            self.modo = f"ollama:{d}"
                            return
            except Exception: pass
        k = os.getenv("ANTHROPIC_API_KEY","")
        if _CLAUDE and k:
            self._claude = _ant.Anthropic(api_key=k)
            self.modo = "claude-sonnet-4-6"
            return
        k2 = os.getenv("DEEPSEEK_API_KEY","")
        if _DEEPSEEK and k2:
            self._deepseek = _oai.OpenAI(api_key=k2, base_url="https://api.deepseek.com")
            self.modo = "deepseek"

    def analizar(self, nodo:Nodo) -> dict:
        prompt = (
            f"OLLIN v5.5 analisis epistemologico.\n"
            f"Etiqueta:{nodo.etiqueta.value} Carpeta:{nodo.carpeta}\n"
            f"Contenido:{nodo.contenido[:300]}\n\n"
            f"Responde SOLO JSON sin markdown:\n"
            f"{{\"dimensiones\":[],\"gaps\":[],\"relaciones\":[],\"confianza\":\"ALTA|MEDIA|BAJA\",\"sintesis\":\"\"}}"
        )
        base = {"modo":self.modo,"confianza":"MEDIA","dimensiones":[],"gaps":[],"relaciones":[],"sintesis":"Analisis local."}

        if self._ollama_modelo:
            try:
                resp = _ollama_mod.chat(model=self._ollama_modelo,
                    messages=[{"role":"user","content":prompt}],
                    options={"num_predict":512})
                txt = resp.message.content.strip().replace("```json","").replace("```","")
                d = json.loads(txt); d["modo"] = self.modo; return d
            except Exception as e: base["err_ollama"] = str(e)[:60]

        if self._claude:
            try:
                r = self._claude.messages.create(model="claude-sonnet-4-6",max_tokens=512,
                    messages=[{"role":"user","content":prompt}])
                txt = r.content[0].text.strip().replace("```json","").replace("```","")
                d = json.loads(txt); d["modo"] = "claude-sonnet-4-6"; return d
            except Exception as e: base["err_claude"] = str(e)[:60]

        if self._deepseek:
            try:
                r = self._deepseek.chat.completions.create(model="deepseek-chat",max_tokens=512,
                    messages=[{"role":"user","content":prompt}])
                txt = r.choices[0].message.content.strip().replace("```json","").replace("```","")
                d = json.loads(txt); d["modo"] = "deepseek"; return d
            except Exception as e: base["err_deepseek"] = str(e)[:60]

        return base


# ══════════════════════════════════════════════════════════════
# CAPA 4 — CONSOLIDADOR NEURAL (Sueno activo)
# Corre K-Means en background cada N nodos nuevos
# Fallback: agrupacion por carpeta si scikit-learn no disponible
# ══════════════════════════════════════════════════════════════

class Consolidador:
    INTERVALO = 10

    def __init__(self, encoder:Encoder):
        self._enc = encoder
        self._embs:dict[str,list] = {}
        self._lock = threading.Lock()
        self._contador = 0
        self._reportes:list[dict] = []
        self.modo = "sklearn-kmeans" if _SK else "carpeta-fallback"

    def registrar(self, nodo_id:str, emb:list):
        with self._lock:
            self._embs[nodo_id] = emb
            self._contador += 1
            if self._contador >= self.INTERVALO:
                self._contador = 0
                t = threading.Thread(target=self._consolidar, daemon=True)
                t.start()

    def _consolidar(self):
        with self._lock:
            ids  = list(self._embs.keys())
            vecs = list(self._embs.values())
        if len(ids) < 4: return
        if _SK:
            try:
                X = _np.array(vecs, dtype=_np.float32)
                norms = _np.linalg.norm(X, axis=1, keepdims=True)
                X = X / (_np.where(norms==0,1,norms))
                k = max(2, min(len(CARPETAS), len(ids)//3))
                labels = _KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
                clusters = {}
                for nid, lab in zip(ids, labels):
                    clusters.setdefault(int(lab),[]).append(nid)
                rep = {"ts":datetime.datetime.utcnow().isoformat(),
                       "metodo":"kmeans","k":k,
                       "clusters":{str(k):v for k,v in clusters.items()},
                       "total":len(ids)}
            except Exception as e:
                rep = {"ts":datetime.datetime.utcnow().isoformat(),"error":str(e)}
        else:
            rep = {"ts":datetime.datetime.utcnow().isoformat(),
                   "metodo":"fallback","total":len(ids)}
        with self._lock:
            self._reportes.append(rep)
            if len(self._reportes) > 20: self._reportes.pop(0)

    def ultimo(self) -> dict:
        with self._lock:
            return self._reportes[-1] if self._reportes else {"estado":"sin consolidaciones aun"}

    def total_reportes(self) -> int:
        with self._lock: return len(self._reportes)


# ══════════════════════════════════════════════════════════════
# CAPA 5 — GRAFO DE CONOCIMIENTO
# Aristas semanticas entre nodos con similitud > umbral
# Fallback: diccionario de adyacencia si networkx no disponible
# ══════════════════════════════════════════════════════════════

class Grafo:
    UMBRAL = 0.72

    def __init__(self, encoder:Encoder):
        self._enc = encoder
        self._embs:dict[str,list] = {}
        self._lock = threading.Lock()
        self.modo = "networkx" if _NX else "adyacencia-dict"
        if _NX: self._g = _nx_mod.DiGraph()
        else:   self._adj:dict[str,list] = {}

    def agregar(self, nodo:Nodo, emb:list):
        with self._lock:
            nid = nodo.id
            self._embs[nid] = emb
            if _NX:
                self._g.add_node(nid,
                    contenido=nodo.contenido[:60],
                    carpeta=nodo.carpeta,
                    etiqueta=nodo.etiqueta.value)
            for eid, eemb in list(self._embs.items()):
                if eid == nid or eid.endswith("-ESP"): continue
                sim = Encoder.cosine(emb, eemb)
                if sim >= self.UMBRAL:
                    if _NX: self._g.add_edge(nid, eid, peso=round(sim,3))
                    else:
                        self._adj.setdefault(nid,[]).append((eid,round(sim,3)))

    def vecinos(self, nodo_id:str, n:int=5) -> list:
        with self._lock:
            if _NX:
                if not self._g.has_node(nodo_id): return []
                edges = sorted(self._g.out_edges(nodo_id,data=True),
                               key=lambda e:e[2].get("peso",0), reverse=True)
                return [(e[1],e[2].get("peso",0)) for e in edges[:n]]
            return sorted(self._adj.get(nodo_id,[]),key=lambda x:x[1],reverse=True)[:n]

    def estadisticas(self) -> dict:
        with self._lock:
            if _NX:
                nn = self._g.number_of_nodes()
                na = self._g.number_of_edges()
                dens = round(_nx_mod.density(self._g),4) if nn>1 else 0.0
                return {"nodos":nn,"aristas":na,"densidad":dens,"modo":self.modo}
            return {"nodos":len(self._embs),
                    "aristas":sum(len(v) for v in self._adj.values()),
                    "modo":self.modo}


# ══════════════════════════════════════════════════════════════
# COMPONENTES ORIGINALES (actualizados)
# ══════════════════════════════════════════════════════════════

class CapaAntiBias:
    def __init__(self, encoder:Encoder):
        self._enc = encoder
    def procesar(self, contenido:str, etiqueta:Etiqueta=Etiqueta.ESPECULATIVO,
                 carpeta:str="hipotesis_operativas",
                 memoria:TipoMemoria=TipoMemoria.PERMANENTE):
        if carpeta not in CARPETAS: carpeta="hipotesis_operativas"
        nodo = Nodo(contenido=contenido, etiqueta=etiqueta,
                    carpeta=carpeta, memoria=memoria, origen="ANTI_BIAS")
        emb  = self._enc.codificar(contenido)
        return nodo, emb


class AHO:
    def __init__(self, modo:str="SISTEMA", db_path:str="aho_local.db"):
        assert modo in ("SISTEMA","LOCAL")
        self.modo=modo; self._nodos:dict[str,Nodo]={}
        if modo=="LOCAL":
            self._db=db_path
            with sqlite3.connect(db_path) as c:
                c.execute("""CREATE TABLE IF NOT EXISTS nodos(
                    id TEXT PRIMARY KEY,contenido TEXT,etiqueta TEXT,
                    carpeta TEXT,memoria TEXT,origen TEXT,
                    timestamp TEXT,hash TEXT,version_anterior TEXT)""")
                c.commit()
    def depositar(self, nodo:Nodo):
        self._nodos[nodo.id]=nodo
        if self.modo=="LOCAL":
            with sqlite3.connect(self._db) as c:
                c.execute("INSERT OR REPLACE INTO nodos VALUES(?,?,?,?,?,?,?,?,?)",
                    (nodo.id,nodo.contenido,nodo.etiqueta.value,nodo.carpeta,
                     nodo.memoria.value,nodo.origen,nodo.timestamp,
                     nodo.hash,nodo.version_anterior)); c.commit()
    def corregir(self, nodo_id:str, nuevo:str) -> bool:
        if nodo_id not in self._nodos: return False
        n=self._nodos[nodo_id]; n.version_anterior,n.contenido,n.etiqueta=n.contenido,nuevo,Etiqueta.REVISADO
        return True
    def buscar(self, txt:str) -> list:
        return [n for n in self._nodos.values() if txt.lower() in n.contenido.lower()]
    def por_carpeta(self, c:str) -> list:
        return [n for n in self._nodos.values() if n.carpeta==c]
    def exportar(self) -> list: return [n.to_dict() for n in self._nodos.values()]
    def __len__(self): return len(self._nodos)


class Sueno:
    def __init__(self, consolidador:Consolidador):
        self._c={c:[] for c in CARPETAS}
        self._cons = consolidador
    def integrar(self, nodo:Nodo, emb:list):
        self._c[nodo.carpeta].append(nodo)
        self._cons.registrar(nodo.id, emb)
    def resumen(self): return {c:len(ns) for c,ns in self._c.items() if ns}


class CamaraDialectica:
    def __init__(self):
        self._P1=[e for e in EXPERTOS if e.posicion=="P1:oponente"]
        self._P3=[e for e in EXPERTOS if e.posicion=="P3:voz_periferica"]
    def convocar(self, nodo:Nodo, vecinos_grafo:list=None) -> dict:
        return {
            "nodo_id":nodo.id,"etiqueta":nodo.etiqueta.value,
            "P1_oponente":{"nombre":random.choice(self._P1).nombre},
            "P3_voz_periferica":{"nombre":random.choice(self._P3).nombre},
            "sabio":{"nombre":random.choice(SABIOS).nombre,
                     "tradicion":random.choice(SABIOS).tradicion},
            "dimensiones":random.sample(DIMS,7),
            "vecinos_semanticos":[v[0] for v in (vecinos_grafo or [])[:3]],
            "voces_totales":len(EXPERTOS)+len(SABIOS),
            "mce":"mapa_confianza_epistemica",
        }


class HemisferioCreativo:
    PERSONAJES=[
        {"nombre":"Don Silverio","reg":"didactico"},{"nombre":"Charly Munon","reg":"satirico"},
        {"nombre":"Toribio","reg":"coaching"},{"nombre":"Yaya","reg":"cientifico"},
        {"nombre":"Solobo","reg":"juridico"},{"nombre":"La Abuelita","reg":"sapiencial"},
    ]
    def __init__(self): self._g=[]
    def borrador(self, camara:dict) -> dict:
        p=random.choice(self.PERSONAJES)
        g={"id":str(uuid.uuid4())[:8],"personaje":p["nombre"],
           "registro":p["reg"],"nodo_ref":camara.get("nodo_id"),
           "estado":"BORRADOR","ts":datetime.datetime.utcnow().isoformat()}
        self._g.append(g); return g
    def borradores(self): return [g for g in self._g if g["estado"]=="BORRADOR"]


class Mitote:
    def __init__(self, llm:LLMLocal, grafo:Grafo, vector:VectorStore):
        self._c={c:[] for c in CARPETAS}
        self._gaps=[]; self._llm=llm; self._grafo=grafo; self._vec=vector
        self.camara=CamaraDialectica(); self.hemisferio=HemisferioCreativo()
    def procesar(self, nodo:Nodo, emb:list) -> dict:
        self._c[nodo.carpeta].append(nodo)
        ia  = self._llm.analizar(nodo)
        vec = self._vec.buscar(nodo.contenido, n=3, carpeta=nodo.carpeta)
        vg  = self._grafo.vecinos(nodo.id, n=3)
        cam = self.camara.convocar(nodo, vg)
        gu  = self.hemisferio.borrador(cam)
        gap = self._gap(nodo)
        if gap: self._gaps.append(gap)
        return {"nodo_id":nodo.id,"ia":ia,"camara":cam,"guion":gu,"gap":gap,
                "similares_semanticos":vec,"vecinos_grafo":vg}
    def _gap(self, nodo:Nodo):
        cc=[n for n in self._c[nodo.carpeta]
            if n.etiqueta==Etiqueta.CONTROVERTIDO and n.id!=nodo.id]
        if cc: return {"tipo":"CONTRADICCION","nodo":nodo.id,"carpeta":nodo.carpeta,
                       "ts":datetime.datetime.utcnow().isoformat()}
        return None
    def resumen(self):
        return {"carpetas":{c:len(ns) for c,ns in self._c.items() if ns},
                "gaps":len(self._gaps),"motor":self._llm.modo,
                "borradores":len(self.hemisferio.borradores())}


class Ometeotl:
    CLAUSULAS={
        "C-04":lambda n:isinstance(n.etiqueta,Etiqueta),
        "C-09":lambda n:True,
        "C-25":lambda n:"AGENTE_AUTONOMO" not in n.origen,
    }
    def __init__(self, notif=None):
        self._repo=[]; self._pausado=False
        self._lock=threading.Lock(); self._notif=notif or self._default
    def observar(self, nodo:Nodo, fase:str):
        inf=[c for c,r in self.CLAUSULAS.items() if not r(nodo)]
        if inf:
            with self._lock:
                self._pausado=True
                reg={"tipo":"RUPTURA","fase":fase,"nodo":nodo.id,
                     "infracciones":inf,"ts":datetime.datetime.utcnow().isoformat(),
                     "resolucion":"PENDIENTE_ARQUITECTO"}
                self._repo.append(reg); self._notif(reg)
        else:
            self._repo.append({"tipo":"obs","fase":fase,"nodo":nodo.id,
                                "ts":datetime.datetime.utcnow().isoformat()})
    def reanudar(self, arq:str="Luis Ernesto Berzunza Diaz"):
        with self._lock:
            self._pausado=False
            self._repo.append({"tipo":"REANUDADO","por":arq,"ts":datetime.datetime.utcnow().isoformat()})
    @property
    def pausado(self): return self._pausado
    def dioses(self): return list(self._repo)
    @staticmethod
    def _default(reg):
        print(f"\n{'='*56}\n  OMETEOTL - ALERTA AL ARQUITECTO")
        print(f"  Fase: {reg['fase']} | Infracciones: {', '.join(reg['infracciones'])}")
        print(f"  Luis Ernesto Berzunza Diaz debe intervenir.\n{'='*56}\n")


# ══════════════════════════════════════════════════════════════
# OLLIN NEURAL — Integracion de las 5 capas
# ══════════════════════════════════════════════════════════════

class OLLINNeural:
    VERSION = "5.5-neural"
    AUTOR   = "Luis Ernesto Berzunza Diaz"

    def __init__(self, db_path:str="aho_local.db", chroma_path:str="./chroma_ollin"):
        print("  Iniciando capas neurales...")
        self._enc    = Encoder()
        print(f"  C1 Encoder    : {self._enc.modo}")
        self._vec    = VectorStore(self._enc, chroma_path)
        print(f"  C2 VectorStore: {self._vec.modo}")
        self._llm    = LLMLocal()
        print(f"  C3 LLMLocal   : {self._llm.modo}")
        self._cons   = Consolidador(self._enc)
        print(f"  C4 Consolidador: {self._cons.modo}")
        self._grafo  = Grafo(self._enc)
        print(f"  C5 Grafo      : {self._grafo.modo}")
        self.anti_bias = CapaAntiBias(self._enc)
        self.sueno     = Sueno(self._cons)
        self.mitote    = Mitote(self._llm, self._grafo, self._vec)
        self.aho       = AHO("SISTEMA")
        self.aho_local = AHO("LOCAL", db_path)
        self.ometeotl  = Ometeotl()
        self._log:list[dict] = []
        print("  Sembrando AHO...")
        self._sembrar()
        print(f"  AHO inicial: {len(self.aho)} nodos")

    def _sembrar(self):
        for carpeta, semillas in NODOS_SEMILLA.items():
            for contenido, etiqueta in semillas:
                nodo = Nodo(contenido=contenido,etiqueta=etiqueta,
                            carpeta=carpeta,origen="SEMILLA")
                emb  = self._enc.codificar(contenido)
                espejo = nodo.espejo()
                self.aho.depositar(nodo); self.aho.depositar(espejo)
                self.aho_local.depositar(nodo)
                self._vec.agregar(nodo,emb); self._vec.agregar(espejo,emb)
                self._grafo.agregar(nodo,emb); self._grafo.agregar(espejo,emb)
                self.sueno._c[nodo.carpeta].append(nodo)
                self.mitote._c[espejo.carpeta].append(espejo)
                self._cons.registrar(nodo.id, emb)

    def ingresar(self, contenido:str, etiqueta:Etiqueta=Etiqueta.ESPECULATIVO,
                 carpeta:str="hipotesis_operativas",
                 memoria:TipoMemoria=TipoMemoria.PERMANENTE) -> dict:
        if self.ometeotl.pausado:
            return {"estado":"PAUSADO","mensaje":"Ometeotl pauso el sistema. El Arquitecto debe intervenir."}

        nodo, emb = self.anti_bias.procesar(contenido, etiqueta, carpeta, memoria)
        espejo    = nodo.espejo()
        self.ometeotl.observar(nodo,"ANTI_BIAS")

        rs, rm = {}, {}

        def camino_sueno():
            self._grafo.agregar(nodo, emb)
            self._vec.agregar(nodo, emb)
            self.sueno.integrar(nodo, emb)
            self.ometeotl.observar(nodo,"SUENO")
            self.aho.depositar(nodo); self.aho_local.depositar(nodo)
            self.ometeotl.observar(nodo,"AHO_SUENO")
            rs["id"]=nodo.id

        def camino_mitote():
            self._vec.agregar(espejo, emb)
            self._grafo.agregar(espejo, emb)
            self.ometeotl.observar(espejo,"AHO_MITOTE")
            self.aho.depositar(espejo); self.aho_local.depositar(espejo)
            rm.update(self.mitote.procesar(espejo, emb))
            self.ometeotl.observar(espejo,"MITOTE")

        hs=threading.Thread(target=camino_sueno,name="Temictli",daemon=True)
        hm=threading.Thread(target=camino_mitote,name="Mitotl",daemon=True)
        hs.start(); hm.start(); hs.join(); hm.join()

        ciclo={"nodo":nodo.id,"espejo":espejo.id,"etiqueta":etiqueta.value,
               "carpeta":carpeta,"sueno":rs,"mitote":rm,
               "aho_total":len(self.aho),"ts":datetime.datetime.utcnow().isoformat()}
        self._log.append(ciclo); return ciclo

    def buscar_semantico(self, query:str, n:int=6) -> list:
        return self._vec.buscar(query, n=n)

    def estado(self) -> dict:
        gst = self._grafo.estadisticas()
        return {
            "version":self.VERSION,"autor":self.AUTOR,
            "nodos_aho":len(self.aho),"nodos_aho_local":len(self.aho_local),
            "flujo_activo":not self.ometeotl.pausado,
            "gaps":len(self.mitote._gaps),"ciclos":len(self._log),
            "C1_encoder":self._enc.modo,
            "C2_vectorstore":f"{self._vec.modo} ({self._vec.conteo()} vecs)",
            "C3_llm":self._llm.modo,
            "C4_consolidador":f"{self._cons.modo} ({self._cons.total_reportes()} consolidaciones)",
            "C5_grafo":f"{gst['modo']} ({gst['nodos']} nodos, {gst['aristas']} aristas)",
            "borradores":len(self.mitote.hemisferio.borradores()),
        }


# ══════════════════════════════════════════════════════════════
# CLI NEURAL
# ══════════════════════════════════════════════════════════════

def _banner():
    print("""
+============================================================+
|            O L L I N  v5.5  Neural                         |
|      El sistema no piensa -- RECUERDA                      |
|  Luis Ernesto Berzunza Diaz . CDMX . 2026                  |
|  C1:Embeddings C2:ChromaDB C3:Ollama C4:KMeans C5:Grafo    |
+============================================================+""")

def _ayuda():
    print("""
  INGRESAR (+ |carpeta opcional):
    i  iv  ic  ip  ix  io  <texto>

  BUSQUEDA:
    b   <texto>    Busqueda exacta en AHO
    sem <texto>    Busqueda SEMANTICA (C2) -- por significado
    k   <carpeta>  Nodos de una carpeta

  NEURAL:
    neural         Estado de las 5 capas neurales
    vec            Estadisticas del vector store (C2)
    graf <id>      Vecinos semanticos de un nodo (C5)
    consol         Ultimo reporte de consolidacion (C4)

  SISTEMA:
    e              Estado completo
    s              Resumen Sueno / Mitote
    g              Guiones BORRADOR
    d              Repositorio Ometeotl
    x              Exportar AHO -> aho_export.json
    r              Reanudar flujo pausado
    ?              Ayuda   q  Salir
""")

def _print_ciclo(c:dict):
    if "estado" in c: print(f"  ! {c['mensaje']}"); return
    print(f"  Nodo  : {c['nodo']}  <->  Espejo: {c['espejo']}")
    print(f"  [{c['etiqueta']}] {c['carpeta']}")
    ia=c.get("mitote",{}).get("ia",{})
    cam=c.get("mitote",{}).get("camara",{})
    sim=c.get("mitote",{}).get("similares_semanticos",[])
    vg =c.get("mitote",{}).get("vecinos_grafo",[])
    print(f"  Motor : {ia.get('modo','?')} | Confianza: {ia.get('confianza','?')}")
    if cam:
        print(f"  P1    : {cam.get('P1_oponente',{}).get('nombre','?')}")
        print(f"  P3    : {cam.get('P3_voz_periferica',{}).get('nombre','?')}")
        print(f"  Sabio : {cam.get('sabio',{}).get('nombre','?')}")
        print(f"  Dims  : {', '.join(cam.get('dimensiones',[])[:4])}")
    if sim:
        print(f"  Sem   : {', '.join(s['id'] for s in sim[:3])} (semanticos)")
    if vg:
        print(f"  Grafo : {', '.join(f'{v[0]}({v[1]:.2f})' for v in vg[:3])}")
    if ia.get("sintesis"):
        print(f"  Sintesis: {ia['sintesis'][:80]}")
    if c.get("mitote",{}).get("gap"):
        print(f"  ! GAP : {c['mitote']['gap']['tipo']}")
    print(f"  AHO   : {c['aho_total']} nodos")

PREFIX_MAP={"i":"e","iv":"v","ic":"c","ip":"p","ix":"x","io":"o"}

def main():
    _banner()
    s=OLLINNeural()
    _ayuda()
    while True:
        try: raw=input("ollin> ").strip()
        except (EOFError,KeyboardInterrupt): print("\n  AHO. Hasta pronto."); break
        if not raw: continue
        p=raw.split(" ",1); cmd=p[0].lower(); arg=p[1].strip() if len(p)>1 else ""

        if cmd in PREFIX_MAP:
            if not arg: print("  Escribe el contenido."); continue
            carpeta="hipotesis_operativas"
            if "|" in arg:
                arg,c2=arg.split("|",1); arg=arg.strip(); c2=c2.strip()
                if c2 in CARPETAS: carpeta=c2
                else: print(f"  Carpeta '{c2}' no existe.")
            et=ETIQUETA_CLI.get(PREFIX_MAP[cmd],Etiqueta.ESPECULATIVO)
            print("  Procesando..."); _print_ciclo(s.ingresar(arg,et,carpeta))

        elif cmd=="sem":
            if not arg: print("  Escribe la query semantica."); continue
            rs=s.buscar_semantico(arg)
            print(f"  Busqueda semantica: '{arg}' -> {len(rs)} resultado(s):")
            for r in rs: print(f"    [{r['score']:.3f}] {r['id']} - {r['contenido'][:65]}")

        elif cmd=="b":
            rs=s.aho.buscar(arg)
            print(f"  {len(rs)} resultado(s):")
            for n in rs[:10]: print(f"    [{n.etiqueta.value}] {n.id} - {n.contenido[:65]}")

        elif cmd=="k":
            if arg not in CARPETAS: print(f"  Carpetas: {chr(10).join(CARPETAS)}"); continue
            ns=s.aho.por_carpeta(arg)
            print(f"  {arg}: {len(ns)} nodos")
            for n in ns[:8]: print(f"    [{n.etiqueta.value}] {n.id} - {n.contenido[:55]}")

        elif cmd=="neural":
            print("  5 CAPAS NEURALES:")
            for k,v in s.estado().items():
                if k.startswith("C"): print(f"    {k}: {v}")

        elif cmd=="vec":
            gst=s._grafo.estadisticas()
            print(f"  VectorStore : {s._vec.modo}")
            print(f"  Vectores    : {s._vec.conteo()}")
            print(f"  Grafo nodos : {gst['nodos']}")
            print(f"  Grafo aristas: {gst['aristas']}")
            print(f"  Densidad    : {gst.get('densidad','N/A')}")

        elif cmd=="graf":
            if not arg: print("  Escribe un nodo ID."); continue
            vs=s._grafo.vecinos(arg,n=8)
            if not vs: print(f"  Sin vecinos semanticos para '{arg}'")
            else:
                print(f"  Vecinos de {arg}:")
                for nid,peso in vs: print(f"    {nid} (similitud:{peso:.3f})")

        elif cmd=="consol":
            rep=s._cons.ultimo()
            print(f"  Consolidaciones totales: {s._cons.total_reportes()}")
            print(f"  Ultimo: {json.dumps(rep, ensure_ascii=False)[:200]}")

        elif cmd=="e":
            for k,v in s.estado().items(): print(f"  {k:<26}: {v}")

        elif cmd=="s":
            print("  SUENO:"); [print(f"    {c}: {n}") for c,n in s.sueno.resumen().items()]
            r=s.mitote.resumen()
            print("  MITOTE:"); [print(f"    {c}: {n}") for c,n in r["carpetas"].items()]
            print(f"  Gaps: {r['gaps']}")

        elif cmd=="g":
            bs=s.mitote.hemisferio.borradores()
            print(f"  {len(bs)} guion(es) BORRADOR:")
            for b in bs[-5:]: print(f"    {b['id']} | {b['personaje']} | nodo: {b['nodo_ref']}")

        elif cmd=="d":
            repo=s.ometeotl.dioses()
            print(f"  CONOCIMIENTO_DE_LOS_DIOSES: {len(repo)} registros")
            for r in repo[-6:]: print(f"    [{r.get('tipo','?')}] {r.get('fase','?')} {r.get('ts','')[:19]}")

        elif cmd=="x":
            datos=s.aho.exportar()
            with open("aho_export.json","w",encoding="utf-8") as f:
                json.dump(datos,f,ensure_ascii=False,indent=2)
            print(f"  Exportado: aho_export.json ({len(datos)} nodos)")

        elif cmd=="r": s.ometeotl.reanudar(); print("  Flujo reanudado.")
        elif cmd in ("?","ayuda","help"): _ayuda()
        elif cmd in ("q","salir","exit"): print("  AHO. Hasta pronto."); break
        else: print(f"  '{cmd}' no reconocido. Escribe ?")

if __name__=="__main__":
    main()
