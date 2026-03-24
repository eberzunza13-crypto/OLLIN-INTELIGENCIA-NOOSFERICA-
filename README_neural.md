
# OLLIN v5.5 Neural
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19203312.svg)](https://doi.org/10.5281/zenodo.19203312)

**Autor:** Luis Ernesto Berzunza Diaz  
**Ciudad de Mexico - 17 marzo 2026**

> El sistema no piensa — RECUERDA.
> Ahora tampoco solo guarda — RAZONA.

---

## Las 5 Capas Neurales

| Capa | Componente | Libreria | Fallback |
|------|-----------|----------|---------|
| C1 | Embeddings semanticos | sentence-transformers | hash-128d |
| C2 | Vector store | ChromaDB | coseno en memoria |
| C3 | LLM local | Ollama (llama3/mistral/phi3) | Claude/DeepSeek/simulado |
| C4 | Consolidacion neural | scikit-learn K-Means | agrupacion por carpeta |
| C5 | Grafo de conocimiento | networkx | diccionario de adyacencia |

Todas tienen fallback gracioso. El sistema corre sin instalar nada extra.

---

## Instalacion

### Mac / Linux
```bash
chmod +x setup_neural.sh
./setup_neural.sh
./run_neural.sh
```

### Windows
```
setup_neural.bat
run_neural.bat
```

### Manual
```bash
python -m venv venv
source venv/bin/activate         # Mac/Linux
venv\Scripts\activate.bat        # Windows

pip install -r requirements_neural.txt

# Instalar Ollama (LLM local gratuito)
# Mac/Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Windows  : https://ollama.ai/download
ollama pull llama3

python ollin_neural.py
```

---

## Nuevos comandos CLI

### Busqueda semantica (C2)
```
sem <query>
```
Busca por SIGNIFICADO, no por palabras exactas.  
Ejemplo: `sem sacrificio ritual` encuentra nodos sobre "ofrenda ceremonial azteca".

### Estado neural (C1-C5)
```
neural
```
Muestra el estado de las 5 capas y sus modos activos.

### Vector store (C2)
```
vec
```
Estadisticas: vectores almacenados, aristas del grafo, densidad.

### Grafo de conocimiento (C5)
```
graf <nodo_id>
```
Muestra los vecinos semanticos de un nodo con su similitud coseno.

### Reporte de consolidacion (C4)
```
consol
```
Ultimo reporte K-Means: cuantos clusters, cuantos nodos agrupados.

---

## Comandos originales (todos funcionan igual)

| Comando | Funcion |
|---------|---------|
| `i iv ic ip ix io <texto>` | Ingresar con etiqueta |
| `b <texto>` | Busqueda exacta |
| `k <carpeta>` | Nodos de carpeta |
| `e` | Estado del sistema |
| `s` | Resumen Sueno/Mitote |
| `g` | Guiones BORRADOR |
| `d` | Repositorio Ometeotl |
| `x` | Exportar AHO |
| `r` | Reanudar flujo |

---

## Archivos generados

| Archivo | Descripcion |
|---------|-------------|
| `aho_local.db` | AHO Local SQLite (C-20) |
| `chroma_ollin/` | Base vectorial ChromaDB (C2) |
| `aho_export.json` | Exportacion AHO (comando x) |

---

## Prioridad del LLM (C3)

1. Ollama local (llama3, mistral, phi3, gemma2, qwen2, llama2)
2. Claude Sonnet 4.6 via API (ANTHROPIC_API_KEY en .env)
3. DeepSeek via API (DEEPSEEK_API_KEY en .env)
4. Modo simulado (sin IA — todo lo demas funciona)

---

*AHO — el movimiento ya empezo.*  
*Luis Ernesto Berzunza Diaz - Ciudad de Mexico - 2026*
