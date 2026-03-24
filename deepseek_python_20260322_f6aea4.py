"""
OLLIN Dual Neural — Sistema Cognitivo Epistemologico
=====================================================
Autor y titular : Luis Ernesto Berzunza Diaz
Chihuahua, Chihuahua - 17 marzo 2026
Herramientas    : Claude Sonnet 4.6 (Anthropic) - DeepSeek

Licencia OLLIN: uso gratuito individual/academico/civil.
Cualquier filtro sobre outputs viola C-01 y C-03B.

Correr: python ollin_completo.py
Sin dependencias obligatorias. Funciona desde el primer comando.

Opcional para analisis IA real:
    pip install anthropic python-dotenv
    Crear .env con ANTHROPIC_API_KEY=sk-ant-...
"""
from __future__ import annotations
import os, json, sqlite3, hashlib, uuid, threading, datetime, random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

try: from dotenv import load_dotenv; load_dotenv()
except ImportError: pass
try: import anthropic as _ant; _CLAUDE = True
except ImportError: _CLAUDE = False
try: import openai as _oai; _DEEPSEEK = True
except ImportError: _DEEPSEEK = False


# ══════════════════════════════════════════════════════
# ENUMERACIONES
# ══════════════════════════════════════════════════════

class Etiqueta(Enum):
    VERIFICADO        = "VERIFICADO"
    CORROBORADO       = "CORROBORADO"
    PLAUSIBLE         = "PLAUSIBLE"
    ESPECULATIVO      = "ESPECULATIVO"
    CONTROVERTIDO     = "CONTROVERTIDO"
    OMISION_HISTORICA = "OMISION_HISTORICA"
    REVISADO          = "REVISADO"

class TipoMemoria(Enum):
    PERMANENTE = "PERMANENTE"
    CICLICA    = "CICLICA"
    EFIMERA    = "EFIMERA"

class EstadoNodo(Enum):
    PENDIENTE = "PENDIENTE"      # Recién ingresado, espera procesamiento
    CONSOLIDADO = "CONSOLIDADO"  # Sueno ya lo integró
    EXPRESADO = "EXPRESADO"      # Mitote ya lo procesó
    COMPLETO = "COMPLETO"        # Ambas vías completadas

CARPETAS = [
    "personajes_historicos", "historia_universal", "conocimiento_cientifico",
    "infraestructura_mundial", "redes_poder", "omisiones_historicas",
    "hipotesis_operativas", "escenarios_posibles", "perfilamiento_actores",
    "archivos_clasificados", "datos_valores_numericos",
]
DIMS = ["ontologica","epistemologica","etica","politica","estetica","cosmologica","pragmatica"]
ETIQUETA_CLI = {
    "v": Etiqueta.VERIFICADO,   "c": Etiqueta.CORROBORADO,
    "p": Etiqueta.PLAUSIBLE,    "e": Etiqueta.ESPECULATIVO,
    "x": Etiqueta.CONTROVERTIDO,"o": Etiqueta.OMISION_HISTORICA,
}


# ══════════════════════════════════════════════════════
# NODO
# ══════════════════════════════════════════════════════

@dataclass
class Nodo:
    contenido : str
    etiqueta  : Etiqueta    = Etiqueta.ESPECULATIVO
    carpeta   : str         = "hipotesis_operativas"
    memoria   : TipoMemoria = TipoMemoria.PERMANENTE
    origen    : str         = "EXTERNO"
    id        : str         = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp : str         = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    version_anterior: Optional[str] = None
    estado    : EstadoNodo  = EstadoNodo.PENDIENTE
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = hashlib.sha256(
            f"{self.contenido}{self.etiqueta.value}{self.timestamp}".encode()
        ).hexdigest()[:16]

    def espejo(self):
        return Nodo(contenido=self.contenido, etiqueta=self.etiqueta,
                    carpeta=self.carpeta, memoria=self.memoria,
                    origen=f"ESPEJO:{self.origen}", timestamp=self.timestamp,
                    id=f"{self.id}-ESP", estado=self.estado)

    def to_dict(self):
        return {"id":self.id,"contenido":self.contenido,"etiqueta":self.etiqueta.value,
                "carpeta":self.carpeta,"memoria":self.memoria.value,"origen":self.origen,
                "timestamp":self.timestamp,"hash":self.hash,"estado":self.estado.value,
                "version_anterior":self.version_anterior}


# ══════════════════════════════════════════════════════
# EXPERTOS Y SABIOS (mismo que antes)
# ══════════════════════════════════════════════════════

@dataclass
class Experto:
    nombre: str; dominio: str; posicion: str; especialidad: str = ""

@dataclass
class Sabio:
    nombre: str; tradicion: str; aporte: str

EXPERTOS = [
    Experto("Huitzilin Cronica",     "Historia",       "estandar",          "Critica de fuentes y veracidad documental"),
    Experto("Xochitl Palabra",       "Historia",       "P3:voz_periferica", "Historia oral y tradicion no escrita"),
    Experto("Dr. Olmedo Roca",       "Historia",       "estandar",          "Arqueologia y cultura material"),
    Experto("Contrahistoria",        "Historia",       "P1:oponente",       "Relato disidente y revisionismo critico"),
    Experto("Tlamatini Cero",        "Filosofia",      "P3:voz_periferica", "Filosofia nahuatl y pensamiento mesoamericano"),
    Experto("Episteme Viva",         "Filosofia",      "P1:oponente",       "Epistemologia critica y teoria del conocimiento"),
    Experto("Logos Dual",            "Filosofia",      "estandar",          "Filosofia analitica y logica formal"),
    Experto("Dra. Tiempo Abierto",   "Filosofia",      "estandar",          "Fenomenologia y hermeneutica"),
    Experto("Dr. Numero Primo",      "Ciencias",       "estandar",          "Matematicas y teoria de la complejidad"),
    Experto("Cuanto Incierto",       "Ciencias",       "P1:oponente",       "Fisica cuantica e incertidumbre"),
    Experto("Dra. Estrella Fija",    "Ciencias",       "estandar",          "Astronomia y cosmologia fisica"),
    Experto("Dr. Codigo Vivo",       "Ciencias",       "estandar",          "Biologia computacional y sistemas complejos"),
    Experto("Mercado Libre",         "Economia",       "estandar",          "Economia neoclasica y teoria de mercados"),
    Experto("Dra. Raiz Comun",       "Economia",       "P3:voz_periferica", "Economia del buen vivir y desarrollo comunitario"),
    Experto("Dr. Crisis Permanente", "Economia",       "P1:oponente",       "Economia heterodoxa y critica al capitalismo"),
    Experto("Dr. Estado Nacion",     "Politica",       "estandar",          "Ciencia politica e instituciones"),
    Experto("Dra. Poder Subterraneo","Politica",       "estandar",          "Geopolitica y analisis de poder"),
    Experto("Sin Estado",            "Politica",       "P1:oponente",       "Teoria anarquista y critica al Estado"),
    Experto("Dra. Norma Viva",       "Derecho",        "estandar",          "Derecho constitucional y garantias"),
    Experto("Dr. Derecho Propio",    "Derecho",        "P3:voz_periferica", "Derechos de pueblos originarios"),
    Experto("Dra. Sombra Legal",     "Derecho",        "P1:oponente",       "Criminologia critica y derecho penal"),
    Experto("Dr. Cuerpo Entero",     "Medicina",       "estandar",          "Medicina general e integrada"),
    Experto("Dra. Mente Profunda",   "Medicina",       "estandar",          "Psiquiatria y salud mental"),
    Experto("Curandera del Camino",  "Medicina",       "P3:voz_periferica", "Medicina tradicional y etnobotanica"),
    Experto("Dra. Critica Total",    "Arte",           "estandar",          "Critica de arte y estetica"),
    Experto("Dr. Ritmo y Forma",     "Arte",           "estandar",          "Musicologia y analisis sonoro"),
    Experto("Tlacuilo Hablante",     "Arte",           "P3:voz_periferica", "Narracion oral y arte pictografico mesoamericano"),
    Experto("Dr. Sistema Abierto",   "Tecnologia",     "estandar",          "Ingenieria de sistemas y software libre"),
    Experto("Dra. Red Neuronal",     "Tecnologia",     "P1:oponente",       "Inteligencia artificial y critica algoritmica"),
    Experto("El Tejedor",            "Tecnologia",     "P1:oponente",       "Hacking etico y seguridad de la informacion"),
    Experto("Dra. Ciudad Viva",      "Sociologia",     "estandar",          "Sociologia urbana y espacio publico"),
    Experto("Dr. Masa Critica",      "Sociologia",     "estandar",          "Demografia critica y analisis de poblaciones"),
    Experto("Dra. Tejido Social",    "Sociologia",     "P3:voz_periferica", "Analisis cultural y comunidades marginadas"),
    Experto("Dr. Mapa Mental",       "Psicologia",     "estandar",          "Psicologia cognitiva y ciencias del comportamiento"),
    Experto("Dra. Sombra Interior",  "Psicologia",     "P1:oponente",       "Psicoanalisis jungiano e inconsciente colectivo"),
    Experto("Dr. Cerebro Vivo",      "Psicologia",     "estandar",          "Neuropsicologia y bases neurales del conocimiento"),
    Experto("Dr. Origen Comun",      "Antropologia",   "estandar",          "Antropologia fisica y evolucion humana"),
    Experto("Dra. Campo Abierto",    "Antropologia",   "P3:voz_periferica", "Etnografia y trabajo de campo"),
    Experto("Dr. Palabra Madre",     "Antropologia",   "estandar",          "Linguistica y origen del lenguaje"),
    Experto("Dra. Raiz Profunda",    "Medio ambiente", "estandar",          "Ecologia y sistemas naturales"),
    Experto("Dr. Clima Roto",        "Medio ambiente", "P1:oponente",       "Climatologia y crisis ambiental"),
    Experto("Dra. Mar Sin Fondo",    "Medio ambiente", "estandar",          "Biologia marina y oceanos"),
    Experto("Fr. Logos Eterno",      "Espiritualidad", "estandar",          "Teologia comparativa y mistica"),
    Experto("Marakame del Norte",    "Espiritualidad", "P3:voz_periferica", "Chamanismo huichol y conocimiento sagrado"),
    Experto("Dr. Philosophia",       "Espiritualidad", "estandar",          "Filosofia perenne y tradiciones sapienciales"),
    Experto("Dra. Mithos Vivo",      "Espiritualidad", "P1:oponente",       "Mitologia comparada y estructura del relato sagrado"),
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


# ══════════════════════════════════════════════════════
# NODOS SEMILLA (33 x 2 = 66)
# ══════════════════════════════════════════════════════

NODOS_SEMILLA = {
    "personajes_historicos": [
        ("Nezahualcoyotl: poeta-rey de Texcoco. Primera filosofia documentada del Mexico antiguo.", Etiqueta.VERIFICADO),
        ("Sor Juana Ines de la Cruz: primera intelectual del Nuevo Mundo. Siglo XVII.", Etiqueta.VERIFICADO),
        ("Cuauhtemoc: ultimo tlatoani mexica. Primer acto de soberania epistemica indigena ante la conquista.", Etiqueta.VERIFICADO),
    ],
    "historia_universal": [
        ("El Quinto Sol nahuatl Nahui Ollin es nuestra era. Termina con transformacion.", Etiqueta.CORROBORADO),
        ("La destruccion de codices mesoamericanos (1521, 1562): uno de los mayores actos de destruccion del conocimiento humano.", Etiqueta.VERIFICADO),
        ("La Revolucion Mexicana 1910-1920: primer conflicto del siglo XX con componente agrario e indigena.", Etiqueta.CONTROVERTIDO),
    ],
    "conocimiento_cientifico": [
        ("Principio de incertidumbre de Heisenberg: imposible conocer simultaneamente posicion y momento de una particula.", Etiqueta.VERIFICADO),
        ("Teoria de la evolucion por seleccion natural Darwin-Wallace 1858: base de la biologia moderna.", Etiqueta.VERIFICADO),
        ("Relatividad del tiempo Einstein 1905: el tiempo transcurre a ritmos distintos segun velocidad y gravedad.", Etiqueta.VERIFICADO),
    ],
    "infraestructura_mundial": [
        ("Rutas comerciales prehispanicas conectaban desde el suroeste de Norteamerica hasta Centroamerica.", Etiqueta.CORROBORADO),
        ("Chinampas aztecas sostuvieron 200,000 personas en Tenochtitlan. Tecnologia ignorada por colonizadores.", Etiqueta.VERIFICADO),
        ("Las redes digitales concentran 90% del trafico en menos de 20 corporaciones.", Etiqueta.CORROBORADO),
    ],
    "redes_poder": [
        ("Sacerdotes-astronomos mexicas controlaban el tiempo calendrico y la legitimidad del poder.", Etiqueta.CORROBORADO),
        ("Sistema colonial de castas novohispano: 16 categorias raciales que determinaban derechos y conocimiento.", Etiqueta.VERIFICADO),
        ("Las cinco mayores tecnologicas controlan mas datos que la mayoria de los gobiernos nacionales.", Etiqueta.CORROBORADO),
    ],
    "omisiones_historicas": [
        ("Se estima que existian miles de codices mesoamericanos. Solo sobreviven 15 de origen prehispanico.", Etiqueta.CORROBORADO),
        ("Efecto Matilda: logros cientificos de mujeres atribuidos a hombres. Franklin, Meitner, Payne.", Etiqueta.VERIFICADO),
        ("El 40% de culturas humanas carecen de registro escrito. No significa falta de conocimiento.", Etiqueta.CORROBORADO),
    ],
    "hipotesis_operativas": [
        ("La arquitectura espejo de OLLIN permite crecimiento indefinido sin perder coherencia.", Etiqueta.ESPECULATIVO),
        ("La dualidad aparece como principio estructural en sistemas de conocimiento radicalmente distintos.", Etiqueta.PLAUSIBLE),
        ("AHO como metafora del temazcal: expansivo pero contenido, purificador pero preservador.", Etiqueta.ESPECULATIVO),
    ],
    "escenarios_posibles": [
        ("OLLIN podria ser la primera enciclopedia que registra con igual rigor lo que la academia reconoce e ignora.", Etiqueta.ESPECULATIVO),
        ("Con embeddings semanticos OLLIN puede detectar que dos nodos tratan el mismo tema con palabras distintas.", Etiqueta.PLAUSIBLE),
        ("El grafo de OLLIN podria revelar conexiones entre tradiciones epistemicas que nunca se comunicaron.", Etiqueta.ESPECULATIVO),
    ],
    "perfilamiento_actores": [
        ("Luis Ernesto Berzunza Diaz construyo OLLIN Dual Neural sin laboratorio ni financiamiento desde dispositivos usados.", Etiqueta.VERIFICADO),
        ("Guardianes de memoria oral en culturas sin escritura son equivalentes funcionales de bibliotecas.", Etiqueta.CORROBORADO),
        ("Hackers eticos son los unicos actores que sistematicamente prueban la integridad de sistemas de informacion.", Etiqueta.PLAUSIBLE),
    ],
    "archivos_clasificados": [
        ("Documento fundacional OLLIN Dual Neural: Chihuahua, Chihuahua, 17 marzo 2026. Autor: Luis Ernesto Berzunza Diaz.", Etiqueta.VERIFICADO),
        ("Herramientas: Claude Sonnet 4.6 y DeepSeek como espejo tecnologico. Son instrumentos, no coautores.", Etiqueta.VERIFICADO),
        ("Registros de autoria: Safe Creative, Gmail, Google Drive, INDAUTOR.", Etiqueta.VERIFICADO),
    ],
    "datos_valores_numericos": [
        ("Camara Dialectica: 46 expertos en 14 dominios + 65 sabios de 6 tradiciones = 111 voces.", Etiqueta.VERIFICADO),
        ("AHO: 11 repositorios. 33 nodos semilla por lado = 66 nodos estado inicial.", Etiqueta.VERIFICADO),
        ("FSM Ometeotl: 12 estados. 25 clausulas. 7 dimensiones filosoficas por ciclo. 10 principios rectores.", Etiqueta.VERIFICADO),
    ],
}


# ══════════════════════════════════════════════════════
# CAPA ANTI-BIAS (Capa 00)
# ══════════════════════════════════════════════════════

class CapaAntiBias:
    """Capa 00: Filtra ingesta, aplica C-04 (etiquetado)."""
    def procesar(self, contenido: str, etiqueta: Etiqueta = Etiqueta.ESPECULATIVO,
                 carpeta: str = "hipotesis_operativas", memoria: TipoMemoria = TipoMemoria.PERMANENTE,
                 contexto: Optional[Dict] = None) -> Nodo:
        if carpeta not in CARPETAS:
            carpeta = "hipotesis_operativas"
        return Nodo(contenido=contenido, etiqueta=etiqueta,
                    carpeta=carpeta, memoria=memoria, origen="ANTI_BIAS")


# ══════════════════════════════════════════════════════
# MEMORIA EPISÓDICA
# ══════════════════════════════════════════════════════

class MemoriaEpisodica:
    """
    Capa de contexto: desordenadamente ordenada, carga bajo demanda.
    Tipos: EFÍMERA (se purga), CÍCLICA (se reusa), PERMANENTE (siempre disponible).
    """
    def __init__(self, aho: 'AHO'):
        self.aho = aho
        self._cache: Dict[str, List[Nodo]] = {}  # contexto_id -> nodos
        self._contexto_activo: Optional[str] = None

    def activar_contexto(self, contexto_id: str):
        """Carga bajo demanda: activa un contexto por proyecto/tema."""
        self._contexto_activo = contexto_id
        if contexto_id not in self._cache:
            # Buscar nodos relacionados en AHO (por palabras clave del contexto)
            # Por ahora, carga todos los nodos del contexto si existen
            self._cache[contexto_id] = []

    def alimentar(self, nodo: Nodo):
        """Alimenta la memoria episódica con un nodo (desde AHO)."""
        if self._contexto_activo:
            self._cache[self._contexto_activo].append(nodo)
        # También guardar por tipo de memoria para purgas
        if nodo.memoria == TipoMemoria.EFIMERA:
            # Se purgará automáticamente después de N ciclos
            pass

    def obtener_contexto(self) -> List[Nodo]:
        """Devuelve nodos del contexto activo."""
        if self._contexto_activo:
            return self._cache.get(self._contexto_activo, [])
        return []

    def purgar_efimera(self):
        """Limpia memorias efímeras."""
        for ctx, nodos in self._cache.items():
            self._cache[ctx] = [n for n in nodos if n.memoria != TipoMemoria.EFIMERA]

    def resumen(self) -> Dict:
        return {
            "contexto_activo": self._contexto_activo,
            "contextos": len(self._cache),
            "nodos_cache": sum(len(v) for v in self._cache.values())
        }


# ══════════════════════════════════════════════════════
# AHO (CENTRO) — VERSIÓN CORREGIDA
# ══════════════════════════════════════════════════════

class AHO:
    """
    Archivos Históricos OLLIN.
    Centro de todo el sistema. Fuente única de verdad.
    """
    def __init__(self, modo: str = "SISTEMA", db_path: str = "aho_central.db"):
        assert modo in ("SISTEMA", "LOCAL")
        self.modo = modo
        self._nodos: Dict[str, Nodo] = {}
        self._db_path = db_path
        if modo == "LOCAL":
            with sqlite3.connect(db_path) as c:
                c.execute("""CREATE TABLE IF NOT EXISTS nodos(
                    id TEXT PRIMARY KEY, contenido TEXT, etiqueta TEXT,
                    carpeta TEXT, memoria TEXT, origen TEXT, estado TEXT,
                    timestamp TEXT, hash TEXT, version_anterior TEXT)""")
                c.commit()

    def depositar(self, nodo: Nodo):
        """Deposita un nodo en el centro."""
        self._nodos[nodo.id] = nodo
        if self.modo == "LOCAL":
            with sqlite3.connect(self._db_path) as c:
                c.execute("INSERT OR REPLACE INTO nodos VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (nodo.id, nodo.contenido, nodo.etiqueta.value, nodo.carpeta,
                     nodo.memoria.value, nodo.origen, nodo.estado.value,
                     nodo.timestamp, nodo.hash, nodo.version_anterior))
                c.commit()

    def obtener(self, nodo_id: str) -> Optional[Nodo]:
        return self._nodos.get(nodo_id)

    def buscar(self, texto: str) -> List[Nodo]:
        return [n for n in self._nodos.values() if texto.lower() in n.contenido.lower()]

    def por_carpeta(self, carpeta: str) -> List[Nodo]:
        return [n for n in self._nodos.values() if n.carpeta == carpeta]

    def por_estado(self, estado: EstadoNodo) -> List[Nodo]:
        return [n for n in self._nodos.values() if n.estado == estado]

    def actualizar_estado(self, nodo_id: str, nuevo_estado: EstadoNodo):
        if nodo_id in self._nodos:
            self._nodos[nodo_id].estado = nuevo_estado
            if self.modo == "LOCAL":
                self._actualizar_db(nodo_id)

    def _actualizar_db(self, nodo_id: str):
        n = self._nodos[nodo_id]
        with sqlite3.connect(self._db_path) as c:
            c.execute("UPDATE nodos SET estado=? WHERE id=?", (n.estado.value, nodo_id))
            c.commit()

    def __len__(self) -> int:
        return len(self._nodos)

    def exportar(self) -> List[Dict]:
        return [n.to_dict() for n in self._nodos.values()]


# ══════════════════════════════════════════════════════
# SUEÑO — Temictli (hacia adentro)
# ══════════════════════════════════════════════════════

class Sueno:
    """Camino hacia adentro: consolida conocimiento desde el AHO."""
    def __init__(self, aho: AHO, memoria: MemoriaEpisodica):
        self.aho = aho
        self.memoria = memoria
        self._carpetas = {c: [] for c in CARPETAS}

    def consolidar(self, nodo_id: str):
        """Toma un nodo del AHO y lo consolida."""
        nodo = self.aho.obtener(nodo_id)
        if not nodo:
            return False
        self._carpetas[nodo.carpeta].append(nodo)
        # Alimentar memoria episódica
        self.memoria.alimentar(nodo)
        # Marcar como consolidado
        self.aho.actualizar_estado(nodo.id, EstadoNodo.CONSOLIDADO)
        return True

    def procesar_pendientes(self):
        """Procesa todos los nodos pendientes que aún no se han consolidado."""
        pendientes = self.aho.por_estado(EstadoNodo.PENDIENTE)
        for n in pendientes:
            self.consolidar(n.id)

    def resumen(self) -> Dict:
        return {c: len(ns) for c, ns in self._carpetas.items() if ns}


# ══════════════════════════════════════════════════════
# CÁMARA DIALÉCTICA
# ══════════════════════════════════════════════════════

class CamaraDialectica:
    def __init__(self):
        self._P1 = [e for e in EXPERTOS if e.posicion == "P1:oponente"]
        self._P3 = [e for e in EXPERTOS if e.posicion == "P3:voz_periferica"]

    def convocar(self, nodo: Nodo) -> Dict:
        return {
            "nodo_id":   nodo.id,
            "etiqueta":  nodo.etiqueta.value,
            "P1":        {"nombre": random.choice(self._P1).nombre if self._P1 else "Ninguno"},
            "P3":        {"nombre": random.choice(self._P3).nombre if self._P3 else "Ninguno"},
            "sabio":     {"nombre": random.choice(SABIOS).nombre,
                          "tradicion": random.choice(SABIOS).tradicion},
            "dimensiones": random.sample(DIMS, 7),
            "voces":     len(EXPERTOS) + len(SABIOS),
            "mce":       "mapa_confianza_epistemica",
        }


# ══════════════════════════════════════════════════════
# HEMISFERIO CREATIVO
# ══════════════════════════════════════════════════════

class HemisferioCreativo:
    PERSONAJES = [
        {"nombre": "Don Silverio", "registro": "didactico"},
        {"nombre": "Charly Munon", "registro": "satirico"},
        {"nombre": "Toribio",      "registro": "coaching"},
        {"nombre": "Yaya",         "registro": "cientifico"},
        {"nombre": "Solobo",       "registro": "juridico"},
        {"nombre": "La Abuelita",  "registro": "sapiencial"},
    ]

    def __init__(self): 
        self._guiones = []

    def borrador(self, camara: Dict) -> Dict:
        p = random.choice(self.PERSONAJES)
        g = {"id": str(uuid.uuid4())[:8], "personaje": p