"""
OLLIN v5.5 — Arquitectura Cosmológica Completa
================================================
Autor y titular : Luis Ernesto Berzunza Díaz
Ciudad de México · 17 marzo 2026
Herramientas    : Claude Sonnet 4.6 (Anthropic) · DeepSeek

El sistema no piensa — RECUERDA.

Ejecutar:
    python ollin_completo.py

Dependencias opcionales (IA real):
    pip install anthropic openai python-dotenv

Archivo .env (opcional):
    ANTHROPIC_API_KEY=sk-ant-...
    DEEPSEEK_API_KEY=sk-...
"""

from __future__ import annotations
import os, json, sqlite3, hashlib, uuid, threading, datetime, random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
try:
    import anthropic as _ant; _CLAUDE = True
except ImportError:
    _CLAUDE = False
try:
    import openai as _oai; _DEEPSEEK = True
except ImportError:
    _DEEPSEEK = False


# ══════════════════════════════════════════════════════════════════
# CONSTANTES Y ENUMERACIONES
# ══════════════════════════════════════════════════════════════════

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

CARPETAS = [
    "personajes_historicos", "historia_universal", "conocimiento_cientifico",
    "infraestructura_mundial", "redes_poder", "omisiones_historicas",
    "hipotesis_operativas", "escenarios_posibles", "perfilamiento_actores",
    "archivos_clasificados", "datos_valores_numericos",
]

DIMS_FILOSOFICAS = [
    "ontológica", "epistemológica", "ética", "política",
    "estética", "cosmológica", "pragmática",
]

ETIQUETA_CLI = {
    "v": Etiqueta.VERIFICADO, "c": Etiqueta.CORROBORADO,
    "p": Etiqueta.PLAUSIBLE,  "e": Etiqueta.ESPECULATIVO,
    "x": Etiqueta.CONTROVERTIDO, "o": Etiqueta.OMISION_HISTORICA,
}


# ══════════════════════════════════════════════════════════════════
# DATACLASSES BASE
# ══════════════════════════════════════════════════════════════════

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
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = hashlib.sha256(
            f"{self.contenido}{self.etiqueta.value}{self.timestamp}".encode()
        ).hexdigest()[:16]

    def espejo(self) -> "Nodo":
        return Nodo(contenido=self.contenido, etiqueta=self.etiqueta,
                    carpeta=self.carpeta, memoria=self.memoria,
                    origen=f"ESPEJO:{self.origen}", timestamp=self.timestamp,
                    id=f"{self.id}-ESP")

    def to_dict(self) -> dict:
        return {"id": self.id, "contenido": self.contenido,
                "etiqueta": self.etiqueta.value, "carpeta": self.carpeta,
                "memoria": self.memoria.value, "origen": self.origen,
                "timestamp": self.timestamp, "hash": self.hash,
                "version_anterior": self.version_anterior}


@dataclass
class Experto:
    nombre  : str
    dominio : str
    posicion: str   # "estandar" | "P1:oponente" | "P3:voz_periferica"
    especialidad: str = ""


@dataclass
class Sabio:
    nombre    : str
    tradicion : str
    aporte    : str


# ══════════════════════════════════════════════════════════════════
# CATÁLOGO — 46 EXPERTOS
# ══════════════════════════════════════════════════════════════════

EXPERTOS: list[Experto] = [
    # HISTORIA (4)
    Experto("Huitzilin Crónica",     "Historia",        "estandar",          "Crítica de fuentes y veracidad documental"),
    Experto("Xochitl Palabra",       "Historia",        "P3:voz_periferica", "Historia oral y tradición no escrita"),
    Experto("Dr. Olmedo Roca",       "Historia",        "estandar",          "Arqueología y cultura material"),
    Experto("Contrahistoria",        "Historia",        "P1:oponente",       "Relato disidente y revisionismo crítico"),
    # FILOSOFÍA (4)
    Experto("Tlamatini Cero",        "Filosofía",       "P3:voz_periferica", "Filosofía náhuatl y pensamiento mesoamericano"),
    Experto("Episteme Viva",         "Filosofía",       "P1:oponente",       "Epistemología crítica y teoría del conocimiento"),
    Experto("Lógos Dual",            "Filosofía",       "estandar",          "Filosofía analítica y lógica formal"),
    Experto("Dra. Tiempo Abierto",   "Filosofía",       "estandar",          "Fenomenología y hermenéutica"),
    # CIENCIAS EXACTAS (4)
    Experto("Dr. Número Primo",      "Ciencias",        "estandar",          "Matemáticas y teoría de la complejidad"),
    Experto("Cuanto Incierto",       "Ciencias",        "P1:oponente",       "Física cuántica e incertidumbre"),
    Experto("Dra. Estrella Fija",    "Ciencias",        "estandar",          "Astronomía y cosmología física"),
    Experto("Dr. Código Vivo",       "Ciencias",        "estandar",          "Biología computacional y sistemas complejos"),
    # ECONOMÍA (3)
    Experto("Mercado Libre",         "Economía",        "estandar",          "Economía neoclásica y teoría de mercados"),
    Experto("Dra. Raíz Común",       "Economía",        "P3:voz_periferica", "Economía del buen vivir y desarrollo comunitario"),
    Experto("Dr. Crisis Permanente", "Economía",        "P1:oponente",       "Economía heterodoxa y crítica al capitalismo"),
    # POLÍTICA (3)
    Experto("Dr. Estado Nación",     "Política",        "estandar",          "Ciencia política e instituciones"),
    Experto("Dra. Poder Subterráneo","Política",        "estandar",          "Geopolítica y análisis de poder"),
    Experto("Sin Estado",            "Política",        "P1:oponente",       "Teoría anarquista y crítica al Estado"),
    # DERECHO (3)
    Experto("Dra. Norma Viva",       "Derecho",         "estandar",          "Derecho constitucional y garantías"),
    Experto("Dr. Derecho Propio",    "Derecho",         "P3:voz_periferica", "Derechos de pueblos originarios y derecho consuetudinario"),
    Experto("Dra. Sombra Legal",     "Derecho",         "P1:oponente",       "Criminología crítica y derecho penal"),
    # MEDICINA Y SALUD (3)
    Experto("Dr. Cuerpo Entero",     "Medicina",        "estandar",          "Medicina general e integrada"),
    Experto("Dra. Mente Profunda",   "Medicina",        "estandar",          "Psiquiatría y salud mental"),
    Experto("Curandera del Camino",  "Medicina",        "P3:voz_periferica", "Medicina tradicional y etnobotánica"),
    # ARTE Y CULTURA (3)
    Experto("Dra. Crítica Total",    "Arte",            "estandar",          "Crítica de arte y estética"),
    Experto("Dr. Ritmo y Forma",     "Arte",            "estandar",          "Musicología y análisis sonoro"),
    Experto("Tlacuilo Hablante",     "Arte",            "P3:voz_periferica", "Narración oral y arte pictográfico mesoamericano"),
    # TECNOLOGÍA (3)
    Experto("Dr. Sistema Abierto",   "Tecnología",      "estandar",          "Ingeniería de sistemas y software libre"),
    Experto("Dra. Red Neuronal",     "Tecnología",      "P1:oponente",       "Inteligencia artificial y crítica algorítmica"),
    Experto("El Tejedor",            "Tecnología",      "P1:oponente",       "Hacking ético y seguridad de la información"),
    # SOCIOLOGÍA (3)
    Experto("Dra. Ciudad Viva",      "Sociología",      "estandar",          "Sociología urbana y espacio público"),
    Experto("Dr. Masa Crítica",      "Sociología",      "estandar",          "Demografía crítica y análisis de poblaciones"),
    Experto("Dra. Tejido Social",    "Sociología",      "P3:voz_periferica", "Análisis cultural y comunidades marginadas"),
    # PSICOLOGÍA (3)
    Experto("Dr. Mapa Mental",       "Psicología",      "estandar",          "Psicología cognitiva y ciencias del comportamiento"),
    Experto("Dra. Sombra Interior",  "Psicología",      "P1:oponente",       "Psicoanálisis jungiano y el inconsciente colectivo"),
    Experto("Dr. Cerebro Vivo",      "Psicología",      "estandar",          "Neuropsicología y bases neurales del conocimiento"),
    # ANTROPOLOGÍA (3)
    Experto("Dr. Origen Común",      "Antropología",    "estandar",          "Antropología física y evolución humana"),
    Experto("Dra. Campo Abierto",    "Antropología",    "P3:voz_periferica", "Etnografía y trabajo de campo"),
    Experto("Dr. Palabra Madre",     "Antropología",    "estandar",          "Lingüística y origen del lenguaje"),
    # MEDIO AMBIENTE (3)
    Experto("Dra. Raíz Profunda",    "Medio ambiente",  "estandar",          "Ecología y sistemas naturales"),
    Experto("Dr. Clima Roto",        "Medio ambiente",  "P1:oponente",       "Climatología y crisis ambiental"),
    Experto("Dra. Mar Sin Fondo",    "Medio ambiente",  "estandar",          "Biología marina y océanos"),
    # ESPIRITUALIDAD Y COSMOLOGÍA (4)
    Experto("Fr. Logos Eterno",      "Espiritualidad",  "estandar",          "Teología comparativa y mística"),
    Experto("Mara'akame del Norte",  "Espiritualidad",  "P3:voz_periferica", "Chamanismo huichol y conocimiento sagrado"),
    Experto("Dr. Philosophia",       "Espiritualidad",  "estandar",          "Filosofía perenne y tradiciones sapienciales"),
    Experto("Dra. Mithos Vivo",      "Espiritualidad",  "P1:oponente",       "Mitología comparada y estructura del relato sagrado"),
]


# ══════════════════════════════════════════════════════════════════
# CATÁLOGO — 65 SABIOS
# ══════════════════════════════════════════════════════════════════

SABIOS: list[Sabio] = [
    # Mesoamérica y América (15)
    Sabio("Nezahualcóyotl",        "Náhuatl",        "Poesía como filosofía y el conocimiento del corazón"),
    Sabio("Sor Juana Inés de la Cruz","Novohispana", "Primera voz crítica del Nuevo Mundo"),
    Sabio("Popol Vuh",             "Maya K'iche",    "La creación como proceso dialéctico"),
    Sabio("Chilam Balam",          "Maya Yucateco",  "Profecía y memoria cíclica del tiempo"),
    Sabio("Tlacaelel",             "Mexica",         "Arquitectura del pensamiento cosmológico"),
    Sabio("Cuauhtémoc",            "Mexica",         "La resistencia como forma de conocimiento"),
    Sabio("Tonantzin",             "Náhuatl",        "El principio femenino como fundamento"),
    Sabio("El Viejo Antonio",      "Zapatista",      "Sabiduría oral y la pregunta como método"),
    Sabio("Pablo González Casanova","Latinoamérica", "Democracia interna y colonialismo del poder"),
    Sabio("Leopoldo Zea",          "Latinoamérica",  "La filosofía de lo americano"),
    Sabio("José Martí",            "Cubana",         "Nuestra América como proyecto epistémico"),
    Sabio("Frida Kahlo",           "Mexicana",       "El cuerpo como territorio de conocimiento"),
    Sabio("Eduardo Galeano",       "Latinoamérica",  "Las venas abiertas como memoria"),
    Sabio("Octavio Paz",           "Mexicana",       "El laberinto como estructura del ser"),
    Sabio("María Sabina",          "Mazateca",       "Los hongos sagrados y el conocimiento no ordinario"),
    # Grecia y mundo clásico (10)
    Sabio("Sócrates",              "Griega",         "El no saber como puerta al conocimiento"),
    Sabio("Heráclito",             "Griega",         "El flujo perpetuo como única constante"),
    Sabio("Hipatia de Alejandría", "Alejandrina",    "El conocimiento femenino silenciado por la historia"),
    Sabio("Epicuro",               "Griega",         "El conocimiento al servicio de la vida"),
    Sabio("Diógenes de Sínope",    "Griega",         "La irreverencia como herramienta epistémica"),
    Sabio("Pitágoras",             "Griega",         "El número como lenguaje del universo"),
    Sabio("Empédocles",            "Griega",         "Los cuatro elementos como sistema"),
    Sabio("Aristóteles",           "Griega",         "La clasificación como forma de conocer"),
    Sabio("Platón",                "Griega",         "Las ideas como realidad profunda"),
    Sabio("Parménides",            "Griega",         "El ser como fundamento inmutable"),
    # Asia (10)
    Sabio("Confucio",              "China",          "El orden social como conocimiento práctico"),
    Sabio("Lao Tsé",               "China",          "El vacío como contenedor de toda posibilidad"),
    Sabio("Buda Gautama",          "India",          "El sufrimiento como puerta al conocimiento"),
    Sabio("Nagarjuna",             "India",          "La vacuidad de la vacuidad como método"),
    Sabio("Sun Tzu",               "China",          "La estrategia como conocimiento del flujo"),
    Sabio("Ibn Rushd (Averroes)",  "Islámica",       "El que preservó el conocimiento griego para el mundo"),
    Sabio("Al-Biruni",             "Islámica",       "El viajero del conocimiento universal"),
    Sabio("Rumi",                  "Persa-Islámica", "El conocimiento que no puede contenerse sin bailar"),
    Sabio("Kūkai",                 "Japonesa",       "El lenguaje como universo y el universo como lenguaje"),
    Sabio("Matsuo Bashō",          "Japonesa",       "La impermanencia como única verdad"),
    # África y mundo árabe (10)
    Sabio("Ibn Jaldún",            "Árabe-Africana",  "Padre de la sociología: el conocimiento como ciclo"),
    Sabio("Sundiata Keita",        "Mandinga",       "La historia oral como verdad más fiel que el documento"),
    Sabio("Imhotep",               "Egipcia",        "El primer genio universal de la historia"),
    Sabio("Mansa Musa",            "Mali",           "La riqueza como vehículo de conocimiento"),
    Sabio("Nefertiti",             "Egipcia",        "El poder femenino como conocimiento visible"),
    Sabio("Ibn Battuta",           "Árabe-Africana", "El mundo entero como texto a leer"),
    Sabio("Frantz Fanon",          "Caribeña-Africana","El colonizado que se conoce libera al colonizador"),
    Sabio("Cheikh Anta Diop",      "Africana",       "África como cuna del conocimiento universal"),
    Sabio("Miriam Makeba",         "Africana",       "La voz como resistencia epistémica"),
    Sabio("Thomas Sankara",        "Africana",       "El conocimiento como acto político de liberación"),
    # Europa moderna (10)
    Sabio("Baruch Spinoza",        "Holandesa",      "Dios como naturaleza y la ética como geometría"),
    Sabio("Giordano Bruno",        "Italiana",       "Quemado por un conocimiento demasiado verdadero"),
    Sabio("Leonardo da Vinci",     "Renacentista",   "El conocimiento sin fronteras disciplinarias"),
    Sabio("Marie Curie",           "Polaco-Francesa","La que midió lo invisible y pagó el precio"),
    Sabio("Nikola Tesla",          "Serbia-Americana","El que captó la frecuencia que otros no oían"),
    Sabio("Simone de Beauvoir",    "Francesa",       "El género como epistemología"),
    Sabio("Antonio Gramsci",       "Italiana",       "El intelectual orgánico como agente del conocimiento"),
    Sabio("Walter Benjamin",       "Alemana",        "La historia de los vencidos como conocimiento verdadero"),
    Sabio("Hannah Arendt",         "Alemana",        "El mal como banalidad y el pensamiento como resistencia"),
    Sabio("Michel Foucault",       "Francesa",       "El poder como saber y el saber como poder"),
    # Contemporáneos (10)
    Sabio("Vandana Shiva",         "India",          "Las semillas como conocimiento y como resistencia"),
    Sabio("Noam Chomsky",          "Estadounidense", "El lenguaje como estructura del pensamiento"),
    Sabio("bell hooks",            "Afroamericana",  "El amor como epistemología y la pedagogía crítica"),
    Sabio("Carl Sagan",            "Estadounidense", "El cosmos como hogar y la ciencia como humildad"),
    Sabio("Richard Feynman",       "Estadounidense", "El placer de entender como motor del conocimiento"),
    Sabio("Octavia Butler",        "Afroamericana",  "El futuro como forma de recordar el presente"),
    Sabio("Carlos Monsiváis",      "Mexicana",       "La cultura popular como conocimiento legítimo"),
    Sabio("Rigoberta Menchú",      "Maya K'iche",    "El testimonio como epistemología de los sobrevivientes"),
    Sabio("Paulo Freire",          "Brasileña",      "La pedagogía del oprimido como conocimiento liberador"),
    Sabio("Arundhati Roy",         "India",          "La belleza y la justicia como conocimientos inseparables"),
]


# ══════════════════════════════════════════════════════════════════
# NODOS SEMILLA — AHO inicial (3 por carpeta = 33 nodos × 2 lados)
# ══════════════════════════════════════════════════════════════════

NODOS_SEMILLA: dict[str, list[tuple]] = {
    "personajes_historicos": [
        ("Nezahualcóyotl: poeta-rey de Texcoco, autor de los Romances de los Señores de la Nueva España. Sus poemas son la primera filosofía documentada del México antiguo.", Etiqueta.VERIFICADO),
        ("Sor Juana Inés de la Cruz: primera intelectual del Nuevo Mundo. Defendió el derecho de las mujeres al conocimiento en el siglo XVII.", Etiqueta.VERIFICADO),
        ("Cuauhtémoc: último tlatoani mexica. Su resistencia ante Cortés es el primer acto documentado de soberanía epistémica indígena frente a la conquista.", Etiqueta.VERIFICADO),
    ],
    "historia_universal": [
        ("El Quinto Sol náhuatl: la cosmología mexica establece cinco eras del mundo. La quinta — Nahui Ollin — es la nuestra, el sol del movimiento, el que termina con temblor y transformación.", Etiqueta.CORROBORADO),
        ("La Conquista de México como ruptura epistémica: la destrucción de los códices en Tlatelolco (1521) y la quema de libros por Diego de Landa (1562) representan uno de los mayores actos de destrucción del conocimiento humano.", Etiqueta.VERIFICADO),
        ("La Revolución Mexicana (1910-1920): primer conflicto armado del siglo XX con componente explícitamente agrario e indígena. Su memoria histórica sigue siendo disputada entre distintos actores.", Etiqueta.CONTROVERTIDO),
    ],
    "conocimiento_cientifico": [
        ("El principio de incertidumbre de Heisenberg (1927): es imposible conocer simultáneamente la posición y el momento de una partícula con precisión arbitraria. La incertidumbre es constitutiva de la realidad, no un defecto del observador.", Etiqueta.VERIFICADO),
        ("La teoría de la evolución por selección natural (Darwin-Wallace, 1858): los organismos que se reproducen con variaciones hereditarias son sujetos de selección diferencial. Base de la biología moderna.", Etiqueta.VERIFICADO),
        ("La relatividad del tiempo (Einstein, 1905): el tiempo no es absoluto. Transcurre a ritmos distintos según la velocidad relativa y la gravedad del observador.", Etiqueta.VERIFICADO),
    ],
    "infraestructura_mundial": [
        ("Las rutas comerciales prehispánicas: Mesoamérica contaba con redes de intercambio que conectaban desde el suroeste de Norteamérica hasta Centroamérica. El cacao, la obsidiana y las plumas eran monedas de conocimiento.", Etiqueta.CORROBORADO),
        ("Los sistemas de irrigación azteca (chinampas): tecnología agrícola de alta eficiencia que permitió sostener a más de 200,000 personas en Tenochtitlan. Ignorada sistemáticamente por los colonizadores.", Etiqueta.VERIFICADO),
        ("Las redes digitales como nueva infraestructura de conocimiento: Internet concentra el 90% del tráfico en menos de 20 corporaciones. La infraestructura del conocimiento digital replica la desigualdad de la infraestructura física.", Etiqueta.CORROBORADO),
    ],
    "redes_poder": [
        ("El sistema del tlatoani y el pipiltin mexica: estructura de poder basada en el mérito guerrero, el linaje y el conocimiento calendárico. Los sacerdotes-astrónomos controlaban el tiempo y por tanto la legitimidad del poder.", Etiqueta.CORROBORADO),
        ("El sistema colonial de castas novohispano: clasificación racial de 16 categorías que determinaba derechos, trabajo y acceso al conocimiento. Primer sistema moderno de racismo institucionalizado.", Etiqueta.VERIFICADO),
        ("Las corporaciones tecnológicas como poder sin Estado: las cinco mayores empresas tecnológicas del mundo controlan más datos sobre la población global que la mayoría de los gobiernos nacionales.", Etiqueta.CORROBORADO),
    ],
    "omisiones_historicas": [
        ("El conocimiento destruido en la conquista: se estima que existían miles de códices mesoamericanos. Solo sobreviven 15 de origen prehispánico. Lo que se perdió supera todo lo que se conservó.", Etiqueta.CORROBORADO),
        ("Las mujeres científicas no nombradas: el fenómeno del 'efecto Matilda' documenta cómo los logros científicos de mujeres fueron sistemáticamente atribuidos a hombres. Rosalind Franklin (ADN), Lise Meitner (fisión nuclear) y Cecilia Payne (composición del sol) son casos documentados.", Etiqueta.VERIFICADO),
        ("Los pueblos sin historia escrita: aproximadamente el 40% de las culturas humanas que han existido carecen de registro escrito. Esto no significa que carecieran de conocimiento — significa que el conocimiento escrito es una forma cultural particular, no la única.", Etiqueta.CORROBORADO),
    ],
    "hipotesis_operativas": [
        ("OLLIN como sistema de memoria colectiva: la arquitectura espejo de OLLIN permite que el conocimiento crezca indefinidamente sin perder coherencia. El nodo que entra conoce su lugar porque tiene su reflejo exacto al otro lado.", Etiqueta.ESPECULATIVO),
        ("La dualidad como principio universal de organización: desde la física de partículas (materia-antimateria) hasta la cosmología náhuatl (Ometeotl), la dualidad aparece como principio estructural en sistemas de conocimiento radicalmente distintos.", Etiqueta.PLAUSIBLE),
        ("El temazcal como metáfora del conocimiento: el vapor que llena el temazcal es expansivo pero contenido, purificador pero preservador. El AHO funciona bajo el mismo principio: acoge todo, purifica mediante el etiquetado, preserva sin censura.", Etiqueta.ESPECULATIVO),
    ],
    "escenarios_posibles": [
        ("Una enciclopedia sin censura como patrimonio universal: OLLIN podría convertirse en la primera enciclopedia que registra no solo lo que la academia reconoce sino lo que la academia ignora, con igual rigor y distinta etiqueta.", Etiqueta.ESPECULATIVO),
        ("La IA como herramienta de preservación del conocimiento marginal: modelos como Claude Sonnet 4.6 y DeepSeek pueden actuar como amplificadores del conocimiento periférico si su arquitectura garantiza la neutralidad epistemológica.", Etiqueta.PLAUSIBLE),
        ("El retorno a las epistemologías originarias: el siglo XXI podría marcar el inicio de una segunda transición epistémica: de la supremacía del conocimiento occidental hacia un pluralismo epistémico donde los saberes indígenas, femeninos y periféricos tienen igual dignidad.", Etiqueta.ESPECULATIVO),
    ],
    "perfilamiento_actores": [
        ("El arquitecto sin institución: Luis Ernesto Berzunza Díaz construyó OLLIN sin laboratorio, sin financiamiento, sin institución detrás. Desde un Pixel 7 Pro y una ThinkPad X1 Carbon usados. Esto es evidencia de que los recursos no son el límite del pensamiento.", Etiqueta.VERIFICADO),
        ("El sabio como guardián de la memoria oral: en las culturas sin escritura, los guardianes de la memoria oral son equivalentes funcionales a las bibliotecas. Su desaparición es una pérdida epistémica tan grave como un incendio.", Etiqueta.CORROBORADO),
        ("El hacker ético como custodio del conocimiento libre: los hackers éticos son los únicos actores que sistemáticamente prueban la integridad de los sistemas de información. Su rol epistémico está profundamente subestimado.", Etiqueta.PLAUSIBLE),
    ],
    "archivos_clasificados": [
        ("Documento fundacional OLLIN v5.5: Ciudad de México, 17 marzo 2026. Primera declaración formal del sistema por Luis Ernesto Berzunza Díaz.", Etiqueta.VERIFICADO),
        ("Registro de herramientas: Claude Sonnet 4.6 (Anthropic, gratuito) y DeepSeek utilizados como espejo tecnológico en el desarrollo del sistema.", Etiqueta.VERIFICADO),
        ("Registro de registro de autoría: Safe Creative, Gmail timestamp, Google Drive timestamp, INDAUTOR — cuatro fuentes independientes de evidencia de autoría.", Etiqueta.VERIFICADO),
    ],
    "datos_valores_numericos": [
        ("Catálogo Cámara Dialéctica: 46 expertos registrados en 14 dominios. 65 sabios de 6 tradiciones culturales. Total: 111 voces en la Cámara.", Etiqueta.VERIFICADO),
        ("Estructura AHO: 11 repositorios temáticos. Dualidad AHO Sistema / AHO Local. 33 nodos semilla × 2 lados = 66 nodos en el estado inicial.", Etiqueta.VERIFICADO),
        ("Arquitectura FSM: 12 estados del Inspector. 25 cláusulas inmutables. 7 dimensiones filosóficas garantizadas por ciclo. 10 principios rectores.", Etiqueta.VERIFICADO),
    ],
}


# ══════════════════════════════════════════════════════════════════
# CAPA ANTI-BIAS
# ══════════════════════════════════════════════════════════════════

class CapaAntiBias:
    @staticmethod
    def procesar(contenido: str, etiqueta: Etiqueta = Etiqueta.ESPECULATIVO,
                 carpeta: str = "hipotesis_operativas",
                 memoria: TipoMemoria = TipoMemoria.PERMANENTE) -> Nodo:
        if carpeta not in CARPETAS:
            carpeta = "hipotesis_operativas"
        return Nodo(contenido=contenido, etiqueta=etiqueta,
                    carpeta=carpeta, memoria=memoria, origen="ANTI_BIAS")


# ══════════════════════════════════════════════════════════════════
# AHO — La Piedra
# ══════════════════════════════════════════════════════════════════

class AHO:
    def __init__(self, modo: str = "SISTEMA", db_path: str = "aho_local.db"):
        assert modo in ("SISTEMA", "LOCAL")
        self.modo = modo
        self._nodos: dict[str, Nodo] = {}
        if modo == "LOCAL":
            self._db = db_path
            self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db) as con:
            con.execute("""CREATE TABLE IF NOT EXISTS nodos (
                id TEXT PRIMARY KEY, contenido TEXT, etiqueta TEXT,
                carpeta TEXT, memoria TEXT, origen TEXT,
                timestamp TEXT, hash TEXT, version_anterior TEXT)""")
            con.commit()

    def depositar(self, nodo: Nodo) -> None:
        self._nodos[nodo.id] = nodo
        if self.modo == "LOCAL":
            with sqlite3.connect(self._db) as con:
                con.execute("INSERT OR REPLACE INTO nodos VALUES (?,?,?,?,?,?,?,?,?)",
                    (nodo.id, nodo.contenido, nodo.etiqueta.value, nodo.carpeta,
                     nodo.memoria.value, nodo.origen, nodo.timestamp,
                     nodo.hash, nodo.version_anterior))
                con.commit()

    def corregir(self, nodo_id: str, nuevo: str) -> bool:
        if nodo_id not in self._nodos:
            return False
        n = self._nodos[nodo_id]
        n.version_anterior, n.contenido, n.etiqueta = n.contenido, nuevo, Etiqueta.REVISADO
        return True

    def buscar(self, texto: str) -> list[Nodo]:
        return [n for n in self._nodos.values() if texto.lower() in n.contenido.lower()]

    def por_carpeta(self, carpeta: str) -> list[Nodo]:
        return [n for n in self._nodos.values() if n.carpeta == carpeta]

    def exportar(self) -> list[dict]:
        return [n.to_dict() for n in self._nodos.values()]

    def __len__(self): return len(self._nodos)


# ══════════════════════════════════════════════════════════════════
# SUEÑO — Temictli (ingesta · hacia adentro)
# ══════════════════════════════════════════════════════════════════

class Sueno:
    """Recorre el camino EXTERNO → CARPETA → AHO"""
    def __init__(self):
        self._carpetas: dict[str, list[Nodo]] = {c: [] for c in CARPETAS}

    def integrar(self, nodo: Nodo) -> None:
        self._carpetas[nodo.carpeta].append(nodo)

    def leer(self, carpeta: str) -> list[Nodo]:
        return self._carpetas.get(carpeta, [])

    def resumen(self) -> dict:
        return {c: len(ns) for c, ns in self._carpetas.items() if ns}


# ══════════════════════════════════════════════════════════════════
# CÁMARA DIALÉCTICA — 46 expertos + 65 sabios
# ══════════════════════════════════════════════════════════════════

class CamaraDialectica:
    """
    Corazón analítico del Mitote.
    P1: oponente forzado — contradice la posición dominante.
    P3: voz periférica forzada — perspectiva del margen.
    CapaDimensiones: 7 dimensiones filosóficas garantizadas.
    """
    def __init__(self):
        self.expertos = EXPERTOS
        self.sabios   = SABIOS
        self._oponentes  = [e for e in EXPERTOS if e.posicion == "P1:oponente"]
        self._perifericos= [e for e in EXPERTOS if e.posicion == "P3:voz_periferica"]
        self._sabios_por_tradicion: dict[str, list[Sabio]] = {}
        for s in SABIOS:
            self._sabios_por_tradicion.setdefault(s.tradicion, []).append(s)

    def convocar(self, nodo: Nodo) -> dict:
        oponente   = random.choice(self._oponentes)
        periferico = random.choice(self._perifericos)
        sabio      = random.choice(self.sabios)
        dims       = random.sample(DIMS_FILOSOFICAS, 7)
        expertos_dominio = [e for e in self.expertos
                            if e.dominio.lower() in nodo.carpeta.replace("_", " ")]
        return {
            "nodo_id":         nodo.id,
            "etiqueta":        nodo.etiqueta.value,
            "carpeta":         nodo.carpeta,
            "P1_oponente":     {"nombre": oponente.nombre,   "especialidad": oponente.especialidad},
            "P3_voz_periferica":{"nombre": periferico.nombre,"especialidad": periferico.especialidad},
            "sabio_convocado": {"nombre": sabio.nombre,      "tradicion": sabio.tradicion, "aporte": sabio.aporte},
            "expertos_dominio": [e.nombre for e in expertos_dominio],
            "dimensiones_cubiertas": dims,
            "total_voces":     len(self.expertos) + len(self.sabios),
            "mce":             "mapa_confianza_epistemica",
        }


# ══════════════════════════════════════════════════════════════════
# HEMISFERIO CREATIVO — corre en paralelo al Mitote
# ══════════════════════════════════════════════════════════════════

class HemisferioCreativo:
    """
    Corre en paralelo — no aparte.
    Arte · Filosofía · Cultura · Música
    Alimenta a los personajes divulgativos.
    """
    PERSONAJES = [
        {"nombre": "Don Silverio",  "registro": "didáctico",  "dominio": "divulgación general"},
        {"nombre": "Charly Muñón",  "registro": "satírico",   "dominio": "crítica política y social"},
        {"nombre": "Toribio",       "registro": "coaching",   "dominio": "motivación y acción"},
        {"nombre": "Yaya",          "registro": "científico", "dominio": "ciencia y datos"},
        {"nombre": "Solobo",        "registro": "jurídico",   "dominio": "derecho y justicia"},
        {"nombre": "La Abuelita",   "registro": "sapiencial", "dominio": "memoria oral y sabiduría"},
    ]

    def __init__(self):
        self._guiones: list[dict] = []

    def generar_borrador(self, analisis_camara: dict) -> dict:
        personaje = random.choice(self.PERSONAJES)
        guion = {
            "id":        str(uuid.uuid4())[:8],
            "personaje": personaje["nombre"],
            "registro":  personaje["registro"],
            "nodo_ref":  analisis_camara.get("nodo_id"),
            "estado":    "BORRADOR",  # Siempre BORRADOR — Arquitecto aprueba
            "dimensiones": analisis_camara.get("dimensiones_cubiertas", []),
            "sabio_citado": analisis_camara.get("sabio_convocado", {}).get("nombre"),
            "ts":        datetime.datetime.utcnow().isoformat(),
        }
        self._guiones.append(guion)
        return guion

    def borradores(self) -> list[dict]:
        return [g for g in self._guiones if g["estado"] == "BORRADOR"]


# ══════════════════════════════════════════════════════════════════
# MITOTE — Mitotl (proceso cognitivo · hacia afuera)
# ══════════════════════════════════════════════════════════════════

class Mitote:
    """Recorre el camino AHO → CARPETA → EXTERNO (opuesto al Sueño)"""
    def __init__(self):
        self._carpetas: dict[str, list[Nodo]] = {c: [] for c in CARPETAS}
        self._gaps: list[dict] = []
        self.camara     = CamaraDialectica()
        self.hemisferio = HemisferioCreativo()
        self._claude    = self._init_claude()
        self._deepseek  = self._init_deepseek()

    def _init_claude(self):
        k = os.getenv("ANTHROPIC_API_KEY","")
        return _ant.Anthropic(api_key=k) if _CLAUDE and k else None

    def _init_deepseek(self):
        k = os.getenv("DEEPSEEK_API_KEY","")
        return _oai.OpenAI(api_key=k, base_url="https://api.deepseek.com") if _DEEPSEEK and k else None

    def procesar(self, nodo: Nodo) -> dict:
        self._carpetas[nodo.carpeta].append(nodo)
        analisis_ia     = self._analizar_ia(nodo)
        analisis_camara = self.camara.convocar(nodo)
        guion_borrador  = self.hemisferio.generar_borrador(analisis_camara)
        gap             = self._gap(nodo)
        if gap: self._gaps.append(gap)
        return {
            "nodo_id":       nodo.id,
            "carpeta":       nodo.carpeta,
            "etiqueta":      nodo.etiqueta.value,
            "ia":            analisis_ia,
            "camara":        analisis_camara,
            "guion_borrador":guion_borrador,
            "gap":           gap,
        }

    def _analizar_ia(self, nodo: Nodo) -> dict:
        prompt = (
            f"Sistema: OLLIN v5.5 — análisis epistemológico.\n"
            f"Etiqueta: {nodo.etiqueta.value} | Carpeta: {nodo.carpeta}\n"
            f"Nodo: {nodo.contenido[:300]}\n\n"
            f"Responde SOLO JSON sin markdown:\n"
            f"{{\"dimensiones\":[...],\"gaps\":[...],\"relaciones\":[...],\"confianza\":\"ALTA|MEDIA|BAJA\",\"sintesis\":\"...\"}}"
        )
        base = {"modo":"simulado","confianza":"MEDIA","dimensiones":[],"gaps":[],"relaciones":[],"sintesis":"Análisis en modo simulado."}
        if self._claude:
            try:
                r = self._claude.messages.create(model="claude-sonnet-4-6", max_tokens=600,
                    messages=[{"role":"user","content":prompt}])
                txt = r.content[0].text.strip().replace("```json","").replace("```","")
                d = json.loads(txt); d["modo"] = "claude-sonnet-4-6"; return d
            except Exception as e:
                base["claude_error"] = str(e)[:80]
        if self._deepseek:
            try:
                r = self._deepseek.chat.completions.create(model="deepseek-chat", max_tokens=600,
                    messages=[{"role":"user","content":prompt}])
                txt = r.choices[0].message.content.strip().replace("```json","").replace("```","")
                d = json.loads(txt); d["modo"] = "deepseek"; return d
            except Exception as e:
                base["deepseek_error"] = str(e)[:80]
        return base

    def _gap(self, nodo: Nodo) -> Optional[dict]:
        contradictorios = [n for n in self._carpetas[nodo.carpeta]
                           if n.etiqueta == Etiqueta.CONTROVERTIDO and n.id != nodo.id]
        if contradictorios:
            return {"tipo":"CONTRADICCION","nodo_ref":nodo.id,
                    "carpeta":nodo.carpeta,"ts":datetime.datetime.utcnow().isoformat()}
        return None

    def motor(self) -> str:
        if self._claude:   return "claude-sonnet-4-6"
        if self._deepseek: return "deepseek"
        return "simulado"

    def resumen(self) -> dict:
        return {"carpetas": {c:len(ns) for c,ns in self._carpetas.items() if ns},
                "gaps": len(self._gaps), "motor": self.motor(),
                "guiones_borrador": len(self.hemisferio.borradores())}


# ══════════════════════════════════════════════════════════════════
# OMETEOTL — La Dualidad Suprema
# ══════════════════════════════════════════════════════════════════

class Ometeotl:
    CLAUSULAS = {
        "C-04": lambda n: isinstance(n.etiqueta, Etiqueta),
        "C-09": lambda n: True,
        "C-25": lambda n: "AGENTE_AUTONOMO" not in n.origen,
    }

    def __init__(self, notificar: Optional[Callable] = None):
        self._repo: list[dict] = []
        self._pausado = False
        self._lock = threading.Lock()
        self._notificar = notificar or self._alerta_default

    def observar(self, nodo: Nodo, fase: str) -> None:
        infracciones = [c for c, r in self.CLAUSULAS.items() if not r(nodo)]
        if infracciones:
            with self._lock:
                self._pausado = True
                reg = {"tipo":"RUPTURA","fase":fase,"nodo":nodo.id,
                       "hash":nodo.hash,"infracciones":infracciones,
                       "contenido":nodo.contenido[:100],
                       "ts":datetime.datetime.utcnow().isoformat(),
                       "resolucion":"PENDIENTE_ARQUITECTO"}
                self._repo.append(reg)
                self._notificar(reg)
        else:
            self._repo.append({"tipo":"obs","fase":fase,"nodo":nodo.id,
                                "ts":datetime.datetime.utcnow().isoformat()})

    def analizar(self, motivo: str, datos: dict) -> None:
        self._repo.append({"tipo":"ANALISIS_OMETEOTL","motivo":motivo,
                            "datos":datos,"ts":datetime.datetime.utcnow().isoformat()})

    def reanudar(self, arquitecto: str = "Luis Ernesto Berzunza Díaz") -> None:
        with self._lock:
            self._pausado = False
            self._repo.append({"tipo":"REANUDADO","por":arquitecto,
                                "ts":datetime.datetime.utcnow().isoformat()})

    @property
    def pausado(self) -> bool: return self._pausado

    def conocimiento_dioses(self) -> list[dict]: return list(self._repo)

    @staticmethod
    def _alerta_default(reg: dict) -> None:
        print(f"\n{'═'*58}")
        print("  OMETEOTL — ALERTA AL ARQUITECTO")
        print(f"{'═'*58}")
        print(f"  Fase        : {reg['fase']}")
        print(f"  Nodo        : {reg['nodo']}")
        print(f"  Infracciones: {', '.join(reg['infracciones'])}")
        print(f"  → Luis Ernesto Berzunza Díaz debe intervenir.")
        print(f"{'═'*58}\n")


# ══════════════════════════════════════════════════════════════════
# OLLIN — Sistema Completo
# ══════════════════════════════════════════════════════════════════

class OLLIN:
    VERSION = "5.5"
    AUTOR   = "Luis Ernesto Berzunza Díaz"

    def __init__(self, db_path: str = "aho_local.db"):
        self.anti_bias = CapaAntiBias()
        self.sueno     = Sueno()
        self.mitote    = Mitote()
        self.aho       = AHO("SISTEMA")
        self.aho_local = AHO("LOCAL", db_path)
        self.ometeotl  = Ometeotl()
        self._log: list[dict] = []
        self._sembrar_aho()

    def _sembrar_aho(self) -> None:
        """Carga los nodos semilla en ambos lados del espejo al inicio."""
        for carpeta, semillas in NODOS_SEMILLA.items():
            for contenido, etiqueta in semillas:
                nodo = Nodo(contenido=contenido, etiqueta=etiqueta,
                            carpeta=carpeta, origen="SEMILLA")
                espejo = nodo.espejo()
                self.aho.depositar(nodo)
                self.aho.depositar(espejo)
                self.sueno.integrar(nodo)
                self._carpeta_mitote_directo(espejo)

    def _carpeta_mitote_directo(self, nodo: Nodo) -> None:
        self.mitote._carpetas[nodo.carpeta].append(nodo)

    def ingresar(self, contenido: str, etiqueta: Etiqueta = Etiqueta.ESPECULATIVO,
                 carpeta: str = "hipotesis_operativas",
                 memoria: TipoMemoria = TipoMemoria.PERMANENTE) -> dict:

        if self.ometeotl.pausado:
            return {"estado":"FLUJO_PAUSADO",
                    "mensaje":"Ometeotl pausó el sistema. El Arquitecto debe intervenir."}

        nodo   = self.anti_bias.procesar(contenido, etiqueta, carpeta, memoria)
        espejo = nodo.espejo()
        self.ometeotl.observar(nodo, "ANTI_BIAS")

        r_sueno, r_mitote = {}, {}

        def camino_sueno():
            self.sueno.integrar(nodo)
            self.ometeotl.observar(nodo, "SUENO")
            self.aho.depositar(nodo)
            self.aho_local.depositar(nodo)
            self.ometeotl.observar(nodo, "AHO_SUENO")
            r_sueno["id"] = nodo.id

        def camino_mitote():
            self.aho.depositar(espejo)
            self.aho_local.depositar(espejo)
            self.ometeotl.observar(espejo, "AHO_MITOTE")
            analisis = self.mitote.procesar(espejo)
            self.ometeotl.observar(espejo, "MITOTE")
            r_mitote.update(analisis)

        hs = threading.Thread(target=camino_sueno,  name="Temictli", daemon=True)
        hm = threading.Thread(target=camino_mitote, name="Mitotl",   daemon=True)
        hs.start(); hm.start()
        hs.join();  hm.join()

        ciclo = {"nodo":nodo.id,"espejo":espejo.id,
                 "etiqueta":etiqueta.value,"carpeta":carpeta,
                 "sueno":r_sueno,"mitote":r_mitote,
                 "aho_total":len(self.aho),"ts":datetime.datetime.utcnow().isoformat()}
        self._log.append(ciclo)
        return ciclo

    def estado(self) -> dict:
        return {"version":self.VERSION,"autor":self.AUTOR,
                "nodos_aho":len(self.aho),"nodos_aho_local":len(self.aho_local),
                "flujo_activo":not self.ometeotl.pausado,
                "gaps":len(self.mitote._gaps),"ciclos":len(self._log),
                "expertos":len(EXPERTOS),"sabios":len(SABIOS),
                "motor_ia":self.mitote.motor(),
                "guiones_borrador":len(self.mitote.hemisferio.borradores())}


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

def _banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                 O L L I N  v5.5                          ║
║         El sistema no piensa — RECUERDA                  ║
║    Luis Ernesto Berzunza Díaz · CDMX · 2026              ║
║    Herramientas: Claude Sonnet 4.6 · DeepSeek            ║
╚══════════════════════════════════════════════════════════╝""")

def _ayuda():
    print("""
  Ingresar conocimiento:
    i  <texto>   Especulativo (default)
    iv <texto>   Verificado
    ic <texto>   Corroborado
    ip <texto>   Plausible
    ix <texto>   Controvertido
    io <texto>   Omisión histórica

  Explorar:
    b  <texto>   Buscar en el AHO
    k  <carpeta> Ver nodos de una carpeta
    e            Estado del sistema
    s            Resumen Sueño / Mitote
    g            Ver guiones BORRADOR
    d            Repositorio Ometeotl (CONOCIMIENTO_DE_LOS_DIOSES)
    camara       Info de la Cámara Dialéctica

  Sistema:
    x            Exportar AHO → aho_export.json
    r            Reanudar flujo (si Ometeotl lo pausó)
    ?            Esta ayuda
    q            Salir
""")

def _imprimir_ciclo(c: dict):
    if "estado" in c:
        print(f"  ⚠  {c['mensaje']}"); return
    print(f"  ┌ Nodo : {c['nodo']}  ↔  Espejo: {c['espejo']}")
    print(f"  │ [{c['etiqueta']}] → {c['carpeta']}")
    ia = c.get("mitote",{}).get("ia",{})
    print(f"  │ Motor IA   : {ia.get('modo','—')}")
    print(f"  │ Confianza  : {ia.get('confianza','—')}")
    cam = c.get("mitote",{}).get("camara",{})
    if cam:
        print(f"  │ P1 oponente: {cam.get('P1_oponente',{}).get('nombre','—')}")
        print(f"  │ P3 periferia:{cam.get('P3_voz_periferica',{}).get('nombre','—')}")
        print(f"  │ Sabio      : {cam.get('sabio_convocado',{}).get('nombre','—')}")
        print(f"  │ Dims       : {', '.join(cam.get('dimensiones_cubiertas',[])[:4])}")
    g = c.get("mitote",{}).get("guion_borrador",{})
    if g:
        print(f"  │ Borrador   : {g.get('personaje')} ({g.get('registro')})")
    if c.get("mitote",{}).get("gap"):
        print(f"  │ ⚡ GAP: {c['mitote']['gap']['tipo']}")
    print(f"  └ AHO total : {c['aho_total']} nodos")

def main():
    _banner()
    sistema = OLLIN()
    e = sistema.estado()
    print(f"\n  AHO inicial : {e['nodos_aho']} nodos semilla cargados")
    print(f"  Expertos    : {e['expertos']} | Sabios: {e['sabios']}")
    print(f"  Motor IA    : {e['motor_ia']}")
    if e["motor_ia"] == "simulado":
        print("  ⚠  Sin claves API — crea .env con ANTHROPIC_API_KEY / DEEPSEEK_API_KEY")
    _ayuda()

    PREFIX = {"i":"e","iv":"v","ic":"c","ip":"p","ix":"x","io":"o"}

    while True:
        try: raw = input("ollin> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  AHO guardado. AHO."); break
        if not raw: continue
        partes = raw.split(" ", 1)
        cmd = partes[0].lower()
        arg = partes[1].strip() if len(partes) > 1 else ""

        if cmd in PREFIX:
            if not arg: print("  Escribe el contenido."); continue
            carpeta_input = ""
            if "|" in arg:
                parts2 = arg.split("|", 1)
                arg = parts2[0].strip()
                carpeta_input = parts2[1].strip()
            et = ETIQUETA_CLI.get(PREFIX[cmd], Etiqueta.ESPECULATIVO)
            carp = carpeta_input if carpeta_input in CARPETAS else "hipotesis_operativas"
            if carpeta_input and carpeta_input not in CARPETAS:
                print(f"  Carpeta '{carpeta_input}' no existe, usando hipotesis_operativas")
            print("  → Procesando...")
            _imprimir_ciclo(sistema.ingresar(arg, et, carp))

        elif cmd == "b":
            rs = sistema.aho.buscar(arg)
            print(f"  {len(rs)} resultado(s):")
            for n in rs[:10]:
                print(f"    [{n.etiqueta.value}] {n.id} — {n.contenido[:70]}")

        elif cmd == "k":
            if arg not in CARPETAS:
                print(f"  Carpetas: {', '.join(CARPETAS)}"); continue
            ns = sistema.aho.por_carpeta(arg)
            print(f"  {arg}: {len(ns)} nodos")
            for n in ns[:8]:
                print(f"    [{n.etiqueta.value}] {n.id} {n.origen} — {n.contenido[:60]}")

        elif cmd == "e":
            for k, v in sistema.estado().items():
                print(f"  {k:<22}: {v}")

        elif cmd == "s":
            print("  SUEÑO (Temictli):"); [print(f"    {c}: {n}") for c,n in sistema.sueno.resumen().items()]
            r = sistema.mitote.resumen()
            print("  MITOTE (Mitotl):"); [print(f"    {c}: {n}") for c,n in r["carpetas"].items()]
            print(f"  Gaps detectados : {r['gaps']}")

        elif cmd == "g":
            bs = sistema.mitote.hemisferio.borradores()
            print(f"  {len(bs)} guion(es) BORRADOR pendientes de aprobación:")
            for b in bs[-5:]:
                print(f"    {b['id']} | {b['personaje']} | nodo: {b['nodo_ref']}")

        elif cmd == "d":
            repo = sistema.ometeotl.conocimiento_dioses()
            rupturas = [r for r in repo if r.get("tipo") == "RUPTURA"]
            print(f"  CONOCIMIENTO_DE_LOS_DIOSES: {len(repo)} registros | {len(rupturas)} rupturas")
            for r in repo[-8:]:
                print(f"    [{r.get('tipo','?')}] {r.get('fase','—')} {r.get('ts','')[:19]}")

        elif cmd == "camara":
            print(f"  Cámara Dialéctica OLLIN v5.5")
            print(f"  Expertos: {len(EXPERTOS)} | Sabios: {len(SABIOS)}")
            print(f"  Oponentes (P1): {len([e for e in EXPERTOS if e.posicion=='P1:oponente'])}")
            print(f"  Voces periféricas (P3): {len([e for e in EXPERTOS if e.posicion=='P3:voz_periferica'])}")
            print(f"  Dominios: {len(set(e.dominio for e in EXPERTOS))}")
            print(f"  Tradiciones de sabios: {len(set(s.tradicion for s in SABIOS))}")

        elif cmd == "x":
            datos = sistema.aho.exportar()
            with open("aho_export.json","w",encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            print(f"  Exportado: aho_export.json ({len(datos)} nodos)")

        elif cmd == "r":
            sistema.ometeotl.reanudar(); print("  Flujo reanudado por el Arquitecto.")

        elif cmd in ("?","ayuda","help"): _ayuda()
        elif cmd in ("q","salir","exit"): print("  AHO guardado. AHO."); break
        else: print(f"  '{cmd}' no reconocido. Escribe ?")

if __name__ == "__main__":
    main()
