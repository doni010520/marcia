# Dockerfile para API Relatório LSP-R
# Base image com Python 3.11
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema (LibreOffice para conversão DOCX->PDF)
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Tornar script executável e configurar LibreOffice
RUN chmod +x configure-libreoffice.sh && \
    ./configure-libreoffice.sh

# Criar diretórios necessários
RUN mkdir -p /app/temp /app/assets/corpos_pdf /app/templates

# Expor porta 3344
EXPOSE 3344

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PORT=3344

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
