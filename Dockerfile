FROM python:3.11-slim

# Instalar dependencias de tkinter y X11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    x11-xserver-utils \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY "AE v2.py" .

CMD ["python3", "AE v2.py"]
