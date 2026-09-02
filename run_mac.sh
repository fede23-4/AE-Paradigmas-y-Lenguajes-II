#!/bin/bash
# Script para correr la heladeria en macOS via Docker + X11
#
# PREREQUISITOS:
#   1. Instalar XQuartz: brew install --cask xquartz
#   2. Abrir XQuartz y en sus preferencias: Security > Allow connections from network clients
#   3. Hacer logout/login o reiniciar para que XQuartz tome efecto
#
# USO:
#   chmod +x run_mac.sh
#   ./run_mac.sh

echo "=== Heladeria Docker GUI ==="
echo ""

# Verificar que XQuartz esta instalado
if ! command -v xquartz &> /dev/null && [ ! -d "/Applications/Utilities/XQuartz.app" ]; then
    echo "ERROR: XQuartz no esta instalado."
    echo "Instalalo con: brew install --cask xquartz"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no esta instalado."
    exit 1
fi

# Configurar DISPLAY para X11
export DISPLAY=:0

# Construir la imagen
echo "Construyendo imagen Docker..."
docker build -t heladeria-gui .

echo ""
echo "Iniciando la heladeria..."
echo "(Se abrira una ventana de X11/XQuartz)"
echo ""

# Ejecutar con X11 forwarding
docker run --rm -it \
    -e DISPLAY=host.docker.internal:0 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    --name heladeria \
    heladeria-gui
