"""
OLLIN v5.5 — Estructura Cognitiva y Epistemológica
Autor y titular: Luis Ernesto Berzunza Díaz
Ciudad de México · 17 marzo 2026
Herramientas: Claude Sonnet 4.6 (Anthropic) · DeepSeek

Este archivo expresa formalmente la arquitectura OLLIN como programa
de computación para efectos de registro ante INDAUTOR y protección
bajo la Ley Federal del Derecho de Autor, Art. 102 (LFDA México)
y el Convenio de Berna.

OLLIN no es software de ejecución comercial — es la expresión formal
en código de una estructura cognitiva, epistemológica y metodológica
original, concebida íntegramente por Luis Ernesto Berzunza Díaz.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional
import datetime

# ══════════════════════════════════════════════════════════════════
# CAPA 00 — ETIQUETAS EPISTEMOLÓGICAS (Anti-Bias, inmutables)
# ══════════════════════════════════════════════════════════════════

class EtiquetaEpistemica(Enum):
    """Cláusula C-04: Todo dato lleva etiqueta epistemológica."""
    VERIFICADO        = "VERIFICADO"         # Corroborado por múltiples fuentes
    CORROBORADO       = "CORROBORADO"        # Confirmado por fuente secundaria
    PLAUSIBLE         = "PLAUSIBLE"          # Coherente pero no verificado
    ESPECULATIVO      = "ESPECULATIVO"       # Hipótesis operativa
    CONTROVERTIDO     = "CONTROVERTIDO"      # Disputado activamente
    OMISION_HISTORICA = "OMISION_HISTORICA"  # Silencio informativo detectado
    REVISADO          = "REVISADO"           # Corregido — versión anterior conservada (C-15)


class TipoMemoria(Enum):
    """Tipos de memoria por proyecto — AHO Local."""
    PERMANENTE = "PERMANENTE"   # Nunca se borra
    CICLICA    = "CICLICA"      # Rotación definida por n ciclos
    EFIMERA    = "EFIMERA"      # Solo dura la sesión


# ══════════════════════════════════════════════════════════════════
# NODO — Unidad mínima del AHO
# ══════════════════════════════════════════════════════════════════

@dataclass
class NodoAHO:
    """
    Unidad mínima del Archivo Histórico Ontológico.
    Cada nodo tiene su espejo en el lado opuesto de la arquitectura
    (Principio de Dualidad Ollin). El sistema crece sin perderse
    porque cada nodo reconoce su reflejo.
    """
    id:         str
    contenido:  str
    etiqueta:   EtiquetaEpistemica
    repositorio: str                          # Uno de los 11 repositorios
    memoria:    TipoMemoria = TipoMemoria.PERMANENTE
    origen:     str = "INSPECTOR"             # C-11: etiqueta de origen
    timestamp:  str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    version_anterior: Optional[str] = None   # C-15: derecho al olvido
    hash_verificacion: Optional[str] = None  # C-17: blindaje criptográfico


# ══════════════════════════════════════════════════════════════════
# AHO — Archivo Histórico Ontológico (Enciclopedia Viva)
# ══════════════════════════════════════════════════════════════════

class AHO:
    """
    Enciclopedia Viva de OLLIN.
    AHO: expresión sagrada del temazcal — afirmación, presencia, verdad.
    Dualidad: AHO_Sistema (colectivo) ↔ AHO_Local (usuario, dispositivo).
    11 repositorios temáticos. Exportable en formatos abiertos (C-16).
    """

    REPOSITORIOS = [
        "personajes_historicos",
        "historia_universal",
        "conocimiento_cientifico",
        "infraestructura_mundial",
        "redes_poder",
        "omisiones_historicas",
        "hipotesis_operativas",
        "escenarios_posibles",
        "perfilamiento_actores",
        "archivos_clasificados",
        "datos_valores_numericos",   # GAC: valores numéricos aislados (C-07)
    ]

    def __init__(self, modo: str = "SISTEMA"):
        self.modo = modo  # "SISTEMA" (colectivo) | "LOCAL" (usuario)
        self._nodos: dict[str, NodoAHO] = {}
        self._archivos_secretos: dict[str, NodoAHO] = {}  # ASI — C-14

    def ingresar(self, nodo: NodoAHO) -> None:
        """C-05: El Inspector documenta absolutamente todo."""
        assert nodo.repositorio in self.REPOSITORIOS, \
            f"Repositorio '{nodo.repositorio}' no válido."
        self._nodos[nodo.id] = nodo

    def corregir(self, id_nodo: str, nuevo_contenido: str) -> None:
        """C-15: Derecho al olvido — el error se corrige pero queda registrado."""
        if id_nodo in self._nodos:
            nodo = self._nodos[id_nodo]
            nodo.version_anterior = nodo.contenido
            nodo.contenido = nuevo_contenido
            nodo.etiqueta = EtiquetaEpistemica.REVISADO

    def exportar(self) -> list[dict]:
        """C-16: AHO exportable en formatos abiertos, sin filtrado censorio."""
        return [
            {
                "id": n.id,
                "contenido": n.contenido,
                "etiqueta": n.etiqueta.value,
                "repositorio": n.repositorio,
                "timestamp": n.timestamp,
            }
            for n in self._nodos.values()
        ]


# ══════════════════════════════════════════════════════════════════
# FSM — ESTADOS DEL INSPECTOR (12 estados)
# ══════════════════════════════════════════════════════════════════

class EstadoInspector(Enum):
    """Máquina de estados finitos del Inspector — Cláusula C-25."""
    REPOSO            = auto()
    INICIO            = auto()
    INGESTA           = auto()
    ANALIZANDO        = auto()
    CONSULTA_CAMARA   = auto()
    GAP_HUNTING       = auto()
    VALIDACION        = auto()
    ENTREGA           = auto()
    ALERTA            = auto()   # Solo el Arquitecto resuelve
    ANALISIS_PROPIO   = auto()   # C-10: solo si lo indica el Arquitecto
    ENTRENAMIENTO     = auto()
    MODO_DOCUMENTAL   = auto()


# ══════════════════════════════════════════════════════════════════
# INSPECTOR — Eje Central de la Arquitectura Espejo
# ══════════════════════════════════════════════════════════════════

class Inspector:
    """
    Eje central de OLLIN. Orquesta ambos lados del espejo.
    C-25: Ningún agente actúa sin pasar por el Inspector.
    C-12: Acceso total + veto permanente a infractores graves.
    Solo Luis Ernesto Berzunza Díaz (El Arquitecto) resuelve ALERTA.
    """

    def __init__(self, aho_sistema: AHO, aho_local: AHO):
        self.estado = EstadoInspector.REPOSO
        self.aho_sistema = aho_sistema
        self.aho_local   = aho_local
        self._vetados: set[str] = set()   # C-12
        self._log: list[dict] = []

    def _transicion(self, nuevo_estado: EstadoInspector) -> None:
        """Registra toda transición en el AHO — C-05."""
        self._log.append({
            "de": self.estado.name,
            "a":  nuevo_estado.name,
            "ts": datetime.datetime.utcnow().isoformat(),
        })
        self.estado = nuevo_estado

    def procesar(self, entrada: str, etiqueta: EtiquetaEpistemica) -> str:
        """Ciclo cognitivo completo del Inspector."""
        self._transicion(EstadoInspector.INICIO)
        self._transicion(EstadoInspector.INGESTA)
        nodo = NodoAHO(
            id=f"N-{len(self.aho_sistema._nodos)+1:04d}",
            contenido=entrada,
            etiqueta=etiqueta,
            repositorio="hipotesis_operativas",
        )
        self.aho_sistema.ingresar(nodo)
        self._transicion(EstadoInspector.ANALIZANDO)
        self._transicion(EstadoInspector.CONSULTA_CAMARA)
        self._transicion(EstadoInspector.GAP_HUNTING)
        self._transicion(EstadoInspector.VALIDACION)
        self._transicion(EstadoInspector.ENTREGA)
        self._transicion(EstadoInspector.REPOSO)
        return nodo.id

    def vetar(self, actor_id: str) -> None:
        """C-12: Veto permanente e irrevocable."""
        self._vetados.add(actor_id)

    def alerta(self, motivo: str) -> None:
        """Solo el Arquitecto (Luis Ernesto Berzunza Díaz) resuelve este estado."""
        self._transicion(EstadoInspector.ALERTA)
        print(f"[ALERTA] {motivo} — Requiere intervención del Arquitecto.")


# ══════════════════════════════════════════════════════════════════
# CÁMARA DIALÉCTICA — Análisis pluridimensional
# ══════════════════════════════════════════════════════════════════

@dataclass
class Experto:
    nombre:   str
    dominio:  str
    posicion: str   # "P1: oponente" | "P3: voz_periférica" | "estándar"

class CamaraDialectica:
    """
    v5.5: 46 expertos + 65 sabios.
    P1: oponente dialéctico forzado en cada análisis.
    P3: voz periférica forzada — perspectiva no dominante garantizada.
    CapaDimensiones: 7 dimensiones filosóficas garantizadas por ciclo.
    """
    def __init__(self):
        self._expertos: list[Experto] = []

    def registrar(self, experto: Experto) -> None:
        self._expertos.append(experto)

    def analizar(self, nodo: NodoAHO) -> dict:
        """Devuelve análisis pluridimensional — nunca valores numéricos directos."""
        oponente   = next((e for e in self._expertos if e.posicion == "P1: oponente"), None)
        periferico = next((e for e in self._expertos if e.posicion == "P3: voz_periférica"), None)
        return {
            "nodo_id":   nodo.id,
            "etiqueta":  nodo.etiqueta.value,
            "oponente":  oponente.nombre if oponente else "sin_asignar",
            "periferico": periferico.nombre if periferico else "sin_asignar",
            "mce":       "mapa_confianza_epistemica",  # GAC no entrega números directos (C-07)
        }


# ══════════════════════════════════════════════════════════════════
# PERSONAJES DIVULGATIVOS — Obras artísticas independientes
# ══════════════════════════════════════════════════════════════════

@dataclass
class Personaje:
    """
    Cada personaje es una obra artística independiente
    protegida bajo LFDA Art. 13 — Luis Ernesto Berzunza Díaz.
    Todo guión sale como BORRADOR — el Arquitecto aprueba antes de publicar.
    """
    nombre:   str
    funcion:  str
    estilo:   str
    estado:   str = "BORRADOR"   # Siempre BORRADOR hasta aprobación del Arquitecto

PERSONAJES = [
    Personaje("Don Silverio",  "divulgación general",      "didáctico y cercano"),
    Personaje("Charly Muñón",  "sátira política y social", "irónico y ácido"),
    Personaje("Toribio",       "coaching y motivación",    "directo y empático"),
    Personaje("Yaya",          "ciencia y datos",          "precisa y curiosa"),
    Personaje("Solobo",        "derecho y justicia",       "riguroso y claro"),
    Personaje("La Abuelita",   "sabiduría popular",        "cálida y profunda"),
]


# ══════════════════════════════════════════════════════════════════
# HERRAMIENTAS — Espejo Tecnológico
# ══════════════════════════════════════════════════════════════════

class HerramientaIA:
    """
    Claude Sonnet 4.6 y DeepSeek forman el espejo tecnológico.
    Son instrumentos de creación — no co-autores.
    Autoría íntegra: Luis Ernesto Berzunza Díaz.
    """
    CLAUDE_SONNET   = "claude-sonnet-4-6"   # Anthropic — gratuito
    DEEPSEEK        = "deepseek"             # DeepSeek AI — complementario

    @staticmethod
    def espejo(modelo_a: str, modelo_b: str) -> dict:
        return {
            "lado_izquierdo": modelo_a,
            "lado_derecho":   modelo_b,
            "jerarquia":      None,   # Sin jerarquía — principio dual de Ollin
        }
