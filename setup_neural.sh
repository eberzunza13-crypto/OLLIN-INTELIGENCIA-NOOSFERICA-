
#!/bin/bash
# OLLIN v5.5 Neural - Setup Mac/Linux
# Luis Ernesto Berzunza Diaz - Ciudad de Mexico - 2026

echo ""
echo "  OLLIN v5.5 Neural - Instalacion"
echo "  Luis Ernesto Berzunza Diaz"
echo ""

command -v python3 &>/dev/null || { echo "  ERROR: Python 3 requerido."; exit 1; }
echo "  Python: $(python3 --version)"

python3 -m venv venv
source venv/bin/activate

echo "  Instalando 5 capas neurales..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements_neural.txt
echo "  Capas instaladas."

if ! command -v ollama &>/dev/null; then
    echo ""
    echo "  OLLAMA no encontrado (Capa 3 - LLM local)."
    echo "  Para instalar: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Luego:         ollama pull llama3"
    echo "  (Sin Ollama el sistema usa Claude/DeepSeek o modo simulado)"
else
    echo "  Ollama encontrado: $(ollama --version)"
    MODELOS=$(ollama list 2>/dev/null | grep -E "llama3|mistral|phi3|gemma2" | head -1)
    if [ -z "$MODELOS" ]; then
        echo "  Descargando llama3 (puede tardar segun tu conexion)..."
        ollama pull llama3
    else
        echo "  Modelo disponible: $MODELOS"
    fi
fi

[ ! -f ".env" ] && cp .env.example .env && echo "  .env creado desde .env.example"

echo ""
echo "  Instalacion completa. Ejecutar: ./run_neural.sh"
echo ""
