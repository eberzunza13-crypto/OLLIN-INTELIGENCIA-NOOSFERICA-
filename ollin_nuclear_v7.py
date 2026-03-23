#!/usr/bin/env python3
"""
OLLIN NUCLEAR v7 – Versión Básica para Prior Art
Arquitectura: Anti-Bias 00 | Sueño/Mitote dual opuesto | AHO (SQLite) | MECP
LEBD – Luis Ernesto Berzunza Díaz
"""

import os
import json
import hashlib
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional

# ------------------------------------------------------------
# Configuración de rutas
# ------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/ollin_nuclear")
AHO_DB = os.path.join(BASE_DIR, "aho.db")
MECP_DIR = os.path.join(BASE_DIR, "mecp")
os.makedirs(MECP_DIR, exist_ok=True)

# ------------------------------------------------------------
# Base de datos AHO (repositorio central)
# ------------------------------------------------------------
def init_aho():
    conn = sqlite3.connect(AHO_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS nodos (
            id TEXT PRIMARY KEY,
            tipo TEXT,
            contenido TEXT,
            fuente TEXT,
            etiqueta TEXT,
            timestamp TEXT,
            hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS adiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo_id TEXT,
            contenido TEXT,
            fuente TEXT,
            timestamp TEXT,
            FOREIGN KEY(nodo_id) REFERENCES nodos(id)
        )
    ''')
    conn.commit()
    conn.close()
init_aho()

def ahora():
    return datetime.now().isoformat()

def generar_hash(texto):
    return hashlib.sha256(texto.encode()).hexdigest()[:16]

# ------------------------------------------------------------
# Capa Anti-Bias 00
# ------------------------------------------------------------
def aplicar_antibias(texto, fuente, etiqueta):
    """Etiqueta epistémica mínima."""
    idioma = "es" if any(c in "áéíóúñ" for c in texto.lower()) else "en"
    estado = "factual" if len(texto.split()) < 50 else "descriptivo"
    return {
        "texto": texto,
        "fuente": fuente,
        "etiqueta": etiqueta,
        "idioma": idioma,
        "estado": estado,
        "timestamp": ahora()
    }

# ------------------------------------------------------------
# Gestión de nodos (Sueño/Mitote en AHO)
# ------------------------------------------------------------
def guardar_nodo(nodo_id, tipo, contenido, fuente, etiqueta):
    conn = sqlite3.connect(AHO_DB)
    c = conn.cursor()
    h = generar_hash(contenido + fuente)
    c.execute('''
        INSERT INTO nodos (id, tipo, contenido, fuente, etiqueta, timestamp, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nodo_id, tipo, contenido, fuente, etiqueta, ahora(), h))
    conn.commit()
    conn.close()

def guardar_adiccion(nodo_id, contenido, fuente):
    conn = sqlite3.connect(AHO_DB)
    c = conn.cursor()
    c.execute('''
        INSERT INTO adiciones (nodo_id, contenido, fuente, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (nodo_id, contenido, fuente, ahora()))
    conn.commit()
    conn.close()

def buscar_nodo_similar(texto):
    """Búsqueda simple por coincidencia de palabras (placeholder)."""
    # Por simplicidad, no implementamos embeddings; se puede añadir luego.
    return None

def crear_nodo(texto, fuente, etiqueta):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nodo_id = f"{timestamp}_{generar_hash(texto[:50])}"
    guardar_nodo(nodo_id, "sueno", texto, fuente, etiqueta)
    return nodo_id

# ------------------------------------------------------------
# Memoria Episódica Contextual Portable (MECP)
# ------------------------------------------------------------
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
        max_ciclos = 100  # configurable
        if len(archivos) > max_ciclos:
            for arch in archivos[:-max_ciclos]:
                os.remove(os.path.join(self.episodios_dir, arch))

    def exportar(self, n=10):
        episodios = sorted([f for f in os.listdir(self.episodios_dir) if f.endswith('.json')], reverse=True)
        nodos = []
        for ep in episodios:
            with open(os.path.join(self.episodios_dir, ep)) as f:
                data = json.load(f)
                nodos.extend(data.get("nodos", []))
                if len(nodos) >= n:
                    break
        nodos = nodos[-n:]
        ctx = f"[INICIO_CONTEXTO]\nProyecto: {self.proyecto}\nModo: {self.modo}\n"
        for n in nodos:
            ctx += f"[{n['timestamp']}] {n['tipo']}: {n['texto']}\n"
        ctx += "[FIN_CONTEXTO]\n\nContinuar desde este punto:"
        return ctx

# ------------------------------------------------------------
# Órbita Dual: Sueño y Mitote en hilos opuestos
# ------------------------------------------------------------
class OrbitaDual:
    def __init__(self, mecp):
        self.mecp = mecp
        self.activo = False
        self.indice_sueno = 0
        self.indice_mitote = 0
        self.direccion_sueno = 1
        self.direccion_mitote = -1
        self.hilo_sueno = None
        self.hilo_mitote = None

    def iniciar(self):
        if self.activo:
            return
        self.activo = True
        self.hilo_sueno = threading.Thread(target=self._recorrer_sueno, daemon=True)
        self.hilo_mitote = threading.Thread(target=self._recorrer_mitote, daemon=True)
        self.hilo_sueno.start()
        self.hilo_mitote.start()
        print("✓ Órbita dual iniciada (Sueño y Mitote en direcciones opuestas)")

    def detener(self):
        self.activo = False
        if self.hilo_sueno:
            self.hilo_sueno.join(timeout=1)
        if self.hilo_mitote:
            self.hilo_mitote.join(timeout=1)

    def _recorrer_sueno(self):
        while self.activo:
            time.sleep(30)  # frecuencia simplificada
            if not self.activo:
                break
            self._paso_sueno()

    def _recorrer_mitote(self):
        while self.activo:
            time.sleep(30)
            if not self.activo:
                break
            self._paso_mitote()

    def _paso_sueno(self):
        # Simulación: leer nodos desde AHO
        conn = sqlite3.connect(AHO_DB)
        c = conn.cursor()
        c.execute("SELECT id, contenido FROM nodos WHERE tipo='sueno' ORDER BY timestamp")
        nodos = c.fetchall()
        conn.close()
        if not nodos:
            return
        self.indice_sueno = (self.indice_sueno + self.direccion_sueno) % len(nodos)
        nodo_id, contenido = nodos[self.indice_sueno]
        # Aquí podría hacer análisis simple, pero dejamos placeholder
        # En la práctica, se generarían preguntas y se guardarían en Mitote.
        # Por simplicidad, solo registramos en MECP
        self.mecp.registrar("sueno", f"Nodo {nodo_id}: {contenido[:100]}", "orbita_sueno")

    def _paso_mitote(self):
        conn = sqlite3.connect(AHO_DB)
        c = conn.cursor()
        c.execute("SELECT id, contenido FROM nodos WHERE tipo='sueno' ORDER BY timestamp DESC")
        nodos = c.fetchall()
        conn.close()
        if not nodos:
            return
        self.indice_mitote = (self.indice_mitote + self.direccion_mitote) % len(nodos)
        nodo_id, contenido = nodos[self.indice_mitote]
        # Simula generación de pregunta
        pregunta = f"¿Qué implicaciones tiene {contenido[:50]}...?"
        # Guardar pregunta como nodo Mitote (otra tabla o simplemente registro)
        guardar_nodo(nodo_id + "_preg", "mitote", pregunta, "orbita_mitote", "pregunta")
        self.mecp.registrar("mitote", pregunta, "orbita_mitote")

# ------------------------------------------------------------
# CLI simple
# ------------------------------------------------------------
def main():
    mecp = MECP()
    orbita = OrbitaDual(mecp)

    print("\n" + "="*60)
    print("OLLIN NUCLEAR v7 (versión básica para prior art)")
    print("Anti-Bias 00 | Sueño/Mitote dual opuesto | AHO | MECP")
    print("Comandos: /ingesta <texto>, /conocido, /mecp_modo <modo>, /contexto, /orbita on/off, salir")
    print("="*60)

    while True:
        try:
            cmd = input("> ").strip()
            if cmd == "salir":
                break
            if cmd.startswith("/ingesta "):
                texto = cmd[9:].strip()
                if not texto:
                    print("  Error: texto vacío")
                    continue
                fuente = input("  Fuente: ").strip()
                etiqueta = input("  Etiqueta: ").strip() or "documento"
                datos = aplicar_antibias(texto, fuente, etiqueta)
                nodo_id = crear_nodo(datos["texto"], datos["fuente"], datos["etiqueta"])
                mecp.registrar("usuario", texto, fuente)
                print(f"  ✓ Nodo {nodo_id} guardado")
            elif cmd == "/conocido":
                conn = sqlite3.connect(AHO_DB)
                c = conn.cursor()
                c.execute("SELECT id, timestamp, contenido FROM nodos WHERE tipo='sueno' ORDER BY timestamp DESC LIMIT 10")
                for row in c.fetchall():
                    print(f"    {row[0]} [{row[1]}]: {row[2][:80]}")
                conn.close()
            elif cmd.startswith("/mecp_modo "):
                modo = cmd[11:].strip().upper()
                if modo in ["EPISODICO", "PERMANENTE", "CICLICO", "FUGAZ"]:
                    mecp.set_modo(modo)
                    print(f"  Modo MECP cambiado a {modo}")
                else:
                    print("  Modos válidos: EPISODICO, PERMANENTE, CICLICO, FUGAZ")
            elif cmd == "/contexto":
                print("\n" + mecp.exportar())
            elif cmd.startswith("/orbita "):
                accion = cmd[8:].strip().lower()
                if accion == "on":
                    orbita.iniciar()
                elif accion == "off":
                    orbita.detener()
                else:
                    print("  Uso: /orbita on|off")
            else:
                print("  Comando no reconocido. Usa /ingesta, /conocido, /mecp_modo, /contexto, /orbita, salir")
        except KeyboardInterrupt:
            print("\nInterrupción, saliendo...")
            break
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()
