# Dockerfile para API Relatório LSP-R
FROM python:3.11-slim

WORKDIR /app

# Instalar LibreOffice E fontes extras
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    fonts-liberation \
    fonts-dejavu \
    fonts-liberation2 \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Configurar LibreOffice
RUN chmod +x configure-libreoffice.sh && \
    ./configure-libreoffice.sh

RUN mkdir -p /app/temp /app/assets/corpos_pdf /app/templates

EXPOSE 3344

ENV PYTHONUNBUFFERED=1
ENV PORT=3344

CMD ["python", "app.py"]
