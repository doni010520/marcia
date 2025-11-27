#!/bin/bash

# Script para iniciar API Relatório LSP-R na porta 3344

echo "========================================="
echo "Iniciando API Relatório LSP-R"
echo "Porta: 3344"
echo "========================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor instale Python 3.8+"
    exit 1
fi

# Verificar se LibreOffice está instalado
if ! command -v libreoffice &> /dev/null; then
    echo "⚠️  LibreOffice não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y libreoffice-writer libreoffice-core --no-install-recommends
fi

# Verificar se dependências estão instaladas
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar/atualizar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Verificar estrutura de pastas
echo "📁 Verificando estrutura de pastas..."
mkdir -p assets/corpos_pdf
mkdir -p templates
mkdir -p temp

# Criar .gitkeep em temp/
touch temp/.gitkeep

# Iniciar API
echo "🚀 Iniciando API na porta 3344..."
echo ""
python3 app.py

# Se o script for interrompido, desativar venv
deactivate
