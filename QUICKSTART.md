# 🚀 Quick Start - API Relatório LSP-R

Guia rápido para colocar a API no ar em menos de 5 minutos!

---

## ⚡ Setup Rápido (Local)

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/relatorio-lsp-api.git
cd relatorio-lsp-api

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar LibreOffice (Ubuntu/Debian)
sudo apt install libreoffice-writer -y

# 4. Adicionar seus arquivos
# - Logo em: assets/logo_cerebro.png
# - Templates DOCX em: templates/
# - Corpos PDF em: assets/corpos_pdf/

# 5. Iniciar API
python app.py
```

**API estará em:** `http://localhost:3344`

---

## 🔥 Iniciar com Script (Recomendado)

```bash
./start.sh
```

---

## 🧪 Testar se está funcionando

```bash
# Teste 1: Health check
curl http://localhost:3344/health

# Teste 2: Listar templates
curl http://localhost:3344/templates-disponiveis

# Teste 3: Rodar suite de testes
python test_api.py
```

---

## 📤 Gerar seu primeiro PDF

```bash
curl -X POST http://localhost:3344/gerar-relatorio \
  -H "Content-Type: application/json" \
  -d '{
    "participante": "João Silva",
    "pontuacoes": {
      "PESSOAS": 37,
      "ACAO": 18,
      "TEMPO": 41,
      "MENSAGEM": 38
    },
    "predominante": "TEMPO",
    "menosDesenvolvido": "ACAO",
    "arquivo": "relatório_mais_tempo_e_menos_ação"
  }' \
  --output meu_relatorio.pdf
```

---

## 🌐 Deploy na VPS (Porta 3344)

```bash
# 1. Conectar na VPS
ssh usuario@seu-vps

# 2. Clonar projeto
git clone https://github.com/seu-usuario/relatorio-lsp-api.git
cd relatorio-lsp-api

# 3. Instalar dependências
sudo apt update
sudo apt install python3-pip libreoffice-writer -y
pip3 install -r requirements.txt

# 4. Adicionar arquivos (logo, templates, PDFs)
# Use scp ou git-lfs para enviar

# 5. Iniciar em background
nohup python3 app.py > logs.txt 2>&1 &

# 6. Verificar se está rodando
curl http://localhost:3344/health
```

**API estará em:** `http://seu-vps:3344`

---

## 🔒 Abrir porta no firewall

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 3344/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=3344/tcp
sudo firewall-cmd --reload
```

---

## 📊 Verificar se está rodando

```bash
# Ver processos Python
ps aux | grep python

# Ver porta 3344
sudo lsof -i :3344

# Ver logs
tail -f logs.txt
```

---

## 🛑 Parar API

```bash
# Encontrar PID
ps aux | grep "app.py"

# Matar processo
kill <PID>

# Ou usar pkill
pkill -f "app.py"
```

---

## 🔄 Atualizar código

```bash
# Parar API
pkill -f "app.py"

# Atualizar do Git
git pull origin main

# Reinstalar dependências (se mudaram)
pip3 install -r requirements.txt

# Reiniciar
nohup python3 app.py > logs.txt 2>&1 &
```

---

## ⚙️ Systemd Service (Produção)

Crie `/etc/systemd/system/relatorio-lsp.service`:

```ini
[Unit]
Description=API Relatório LSP-R
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/relatorio-lsp-api
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Comandos:

```bash
# Ativar
sudo systemctl daemon-reload
sudo systemctl enable relatorio-lsp
sudo systemctl start relatorio-lsp

# Status
sudo systemctl status relatorio-lsp

# Logs
sudo journalctl -u relatorio-lsp -f

# Parar
sudo systemctl stop relatorio-lsp

# Reiniciar
sudo systemctl restart relatorio-lsp
```

---

## 🔗 Integrar com N8N

No HTTP Request node:

```
URL: http://seu-vps:3344/gerar-relatorio
Method: POST
Body Type: JSON
Response Format: File
```

Veja `N8N_INTEGRATION.md` para detalhes completos.

---

## 📋 Checklist de Deploy

- [ ] Python 3.8+ instalado
- [ ] LibreOffice instalado
- [ ] Porta 3344 aberta no firewall
- [ ] Logo adicionado em `assets/`
- [ ] 12 templates DOCX em `templates/`
- [ ] 12 PDFs corpo em `assets/corpos_pdf/`
- [ ] API iniciada e rodando
- [ ] Teste com `/health` passou
- [ ] Teste com `/templates-disponiveis` mostra templates
- [ ] PDF de teste gerado com sucesso
- [ ] N8N consegue acessar a API

---

## 🆘 Problemas Comuns

### Porta 3344 ocupada
```bash
sudo lsof -i :3344
sudo kill -9 <PID>
```

### LibreOffice não encontrado
```bash
which libreoffice
# Se vazio, instalar:
sudo apt install libreoffice-writer
```

### Permissão negada
```bash
chmod +x start.sh
chmod 755 -R relatorio-lsp-api/
```

### PDF corrompido
```bash
# Testar LibreOffice manual
libreoffice --convert-to pdf teste.docx
```

---

## 📞 Suporte

Consulte:
- `README.md` - Documentação completa
- `N8N_INTEGRATION.md` - Integração N8N
- `test_api.py` - Suite de testes

---

**Pronto! Sua API está no ar! 🎉**

Teste agora: `curl http://seu-vps:3344/health`
