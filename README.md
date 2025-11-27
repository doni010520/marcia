# 📊 API Relatório LSP-R (Listening Styles Profile - Revised)

API para geração automatizada de relatórios de Perfil de Escuta e Comunicação com capa personalizada.

## 🎯 Funcionalidades

- ✅ Gera capa personalizada baseada em template DOCX
- ✅ Preenche automaticamente nome do participante e pontuações
- ✅ Junta capa gerada com corpo do relatório (PDF)
- ✅ Suporta 12 variações de relatórios diferentes
- ✅ API REST pronta para integração com N8N
- ✅ Roda na porta 3344

---

## 📁 Estrutura do Projeto

```
relatorio-lsp-api/
├── app.py                          # API FastAPI principal
├── requirements.txt                # Dependências Python
├── README.md                       # Esta documentação
├── .env.example                    # Exemplo de variáveis de ambiente
├── .gitignore                      # Arquivos ignorados pelo Git
├── start.sh                        # Script para iniciar na porta 3344
│
├── assets/
│   ├── logo_cerebro.png           # Logo (você deve adicionar)
│   └── corpos_pdf/                # PDFs do corpo dos relatórios
│       ├── relatório_mais_ação_menos_mensagem.pdf
│       ├── relatório_mais_ação_menos_pessoas.pdf
│       ├── relatório_mais_ação_menos_tempo.pdf
│       ├── relatório_mais_mensagem_menos_ação.pdf
│       ├── relatório_mais_mensagem_menos_pessoas.pdf
│       ├── relatório_mais_mensagem_menos_tempo.pdf
│       ├── relatório_mais_pessoas_e_menos_ação.pdf
│       ├── relatório_mais_pessoas_e_menos_mensagem.pdf
│       ├── relatório_mais_pessoas_e_menos_tempo.pdf
│       ├── relatório_mais_tempo_e_menos_ação.pdf
│       ├── relatório_mais_tempo_e_menos_mensagem.pdf
│       └── relatório_mais_tempo_e_menos_pessoas.pdf
│
├── templates/                      # Templates DOCX das capas
│   ├── relatório_mais_ação_menos_mensagem.docx
│   ├── relatório_mais_ação_menos_pessoas.docx
│   ├── relatório_mais_ação_menos_tempo.docx
│   ├── relatório_mais_mensagem_menos_ação.docx
│   ├── relatório_mais_mensagem_menos_pessoas.docx
│   ├── relatório_mais_mensagem_menos_tempo.docx
│   ├── relatório_mais_pessoas_e_menos_ação.docx
│   ├── relatório_mais_pessoas_e_menos_mensagem.docx
│   ├── relatório_mais_pessoas_e_menos_tempo.docx
│   ├── relatório_mais_tempo_e_menos_ação.docx
│   ├── relatório_mais_tempo_e_menos_mensagem.docx
│   └── relatório_mais_tempo_e_menos_pessoas.docx
│
└── temp/                           # Arquivos temporários (gerados automaticamente)
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- LibreOffice (para conversão DOCX → PDF)
- Git

### Passo 1: Clonar repositório

```bash
git clone https://github.com/seu-usuario/relatorio-lsp-api.git
cd relatorio-lsp-api
```

### Passo 2: Instalar dependências Python

```bash
pip install -r requirements.txt
```

### Passo 3: Instalar LibreOffice (se necessário)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install libreoffice-writer libreoffice-core --no-install-recommends
```

**CentOS/RHEL:**
```bash
sudo yum install libreoffice-writer libreoffice-core
```

**macOS:**
```bash
brew install --cask libreoffice
```

### Passo 4: Adicionar seus arquivos

1. **Logo**: Coloque `logo_cerebro.png` em `assets/`
2. **Templates DOCX**: Coloque os 12 arquivos `.docx` em `templates/`
3. **Corpos PDF**: Coloque os 12 arquivos `.pdf` em `assets/corpos_pdf/`

---

## ▶️ Como Rodar

### Desenvolvimento (local)

```bash
python app.py
```

A API estará disponível em: `http://localhost:3344`

### Produção (VPS)

#### Opção 1: Script start.sh

```bash
chmod +x start.sh
./start.sh
```

#### Opção 2: Systemd Service

Crie o arquivo `/etc/systemd/system/relatorio-lsp.service`:

```ini
[Unit]
Description=API Relatório LSP-R
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/relatorio-lsp-api
ExecStart=/usr/bin/python3 /caminho/para/relatorio-lsp-api/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Ativar e iniciar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable relatorio-lsp
sudo systemctl start relatorio-lsp
sudo systemctl status relatorio-lsp
```

#### Opção 3: Docker (futuro)

```bash
# Em desenvolvimento
docker build -t relatorio-lsp-api .
docker run -p 3344:3344 relatorio-lsp-api
```

---

## 📡 Endpoints da API

### 1. **GET /** - Informações básicas

```bash
curl http://localhost:3344/
```

**Response:**
```json
{
  "message": "API Relatório LSP-R",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "gerar": "POST /gerar-relatorio",
    "templates": "/templates-disponiveis"
  }
}
```

---

### 2. **GET /health** - Verificar saúde da API

```bash
curl http://localhost:3344/health
```

**Response:**
```json
{
  "status": "ok",
  "message": "API Relatório LSP-R v1.0",
  "checks": {
    "templates_dir": true,
    "corpos_pdf_dir": true,
    "libreoffice": true
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 3. **GET /templates-disponiveis** - Listar templates

```bash
curl http://localhost:3344/templates-disponiveis
```

**Response:**
```json
{
  "templates_completos": [
    "relatório_mais_tempo_e_menos_ação",
    "relatório_mais_ação_menos_mensagem"
  ],
  "total_completos": 2,
  "templates_incompletos": [
    {
      "arquivo": "relatório_mais_ação_menos_pessoas",
      "docx_existe": true,
      "pdf_corpo_existe": false,
      "status": "incompleto"
    }
  ],
  "total_esperado": 12
}
```

---

### 4. **POST /gerar-relatorio** - Gerar PDF completo ⭐

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
  --output relatorio.pdf
```

**Request Body:**
```json
{
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
}
```

**Validações:**
- `participante`: string não vazia
- `PESSOAS`, `ACAO`, `TEMPO`, `MENSAGEM`: inteiros entre 0-60
- `predominante` e `menosDesenvolvido`: devem ser diferentes
- `arquivo`: deve existir em templates e corpos_pdf

**Response:** Arquivo PDF (binary)

**Possíveis erros:**
- `400`: Dados inválidos
- `404`: Template ou corpo não encontrado
- `500`: Erro no processamento

---

## 🔗 Integração com N8N

### HTTP Request Node - Configuração

```
Method: POST
URL: http://seu-vps:3344/gerar-relatorio
Authentication: None
Body Content Type: JSON

Body (JSON):
{
  "participante": "{{ $json.participante }}",
  "pontuacoes": {
    "PESSOAS": {{ $json.pontuacoes.PESSOAS }},
    "ACAO": {{ $json.pontuacoes.ACAO }},
    "TEMPO": {{ $json.pontuacoes.TEMPO }},
    "MENSAGEM": {{ $json.pontuacoes.MENSAGEM }}
  },
  "predominante": "{{ $json.predominante }}",
  "menosDesenvolvido": "{{ $json.menosDesenvolvido }}",
  "arquivo": "{{ $json.arquivo }}"
}

Response Format: File
Binary Property: data
```

### Exemplo de fluxo N8N

```
[Function Node - Calcular pontuações]
    ↓
[HTTP Request - POST /gerar-relatorio]
    ↓
[Google Drive - Upload PDF]
    ↓
[WhatsApp - Enviar para cliente]
```

---

## 🗺️ Mapeamento dos 12 Templates

| Predominante | Menos Desenvolvido | Nome do Arquivo |
|--------------|-------------------|-----------------|
| ACAO | MENSAGEM | relatório_mais_ação_menos_mensagem |
| ACAO | PESSOAS | relatório_mais_ação_menos_pessoas |
| ACAO | TEMPO | relatório_mais_ação_menos_tempo |
| MENSAGEM | ACAO | relatório_mais_mensagem_menos_ação |
| MENSAGEM | PESSOAS | relatório_mais_mensagem_menos_pessoas |
| MENSAGEM | TEMPO | relatório_mais_mensagem_menos_tempo |
| PESSOAS | ACAO | relatório_mais_pessoas_e_menos_ação |
| PESSOAS | MENSAGEM | relatório_mais_pessoas_e_menos_mensagem |
| PESSOAS | TEMPO | relatório_mais_pessoas_e_menos_tempo |
| TEMPO | ACAO | relatório_mais_tempo_e_menos_ação |
| TEMPO | MENSAGEM | relatório_mais_tempo_e_menos_mensagem |
| TEMPO | PESSOAS | relatório_mais_tempo_e_menos_pessoas |

---

## 🛠️ Troubleshooting

### Erro: "LibreOffice not found"

**Solução:**
```bash
# Verificar se LibreOffice está instalado
which libreoffice

# Instalar se necessário
sudo apt install libreoffice-writer
```

### Erro: "Template DOCX não encontrado"

**Solução:**
- Verifique se os arquivos `.docx` estão em `/templates/`
- Verifique o nome exato do arquivo (sem `.docx` na API)

### Erro: "Corpo do PDF não encontrado"

**Solução:**
- Verifique se os arquivos `.pdf` estão em `/assets/corpos_pdf/`
- O nome deve ser exatamente igual ao especificado no JSON

### PDF gerado está corrompido

**Solução:**
- Verifique se LibreOffice está funcionando: `libreoffice --version`
- Teste conversão manual: `libreoffice --convert-to pdf arquivo.docx`

### Porta 3344 já está em uso

**Solução:**
```bash
# Encontrar processo na porta 3344
sudo lsof -i :3344

# Matar processo
sudo kill -9 <PID>
```

---

## 📝 Logs

A API gera logs no console com informações sobre:
- Templates carregados
- PDFs gerados
- Erros de processamento

Para salvar logs em arquivo:

```bash
python app.py > logs/app.log 2>&1
```

---

## 🔐 Segurança

### Recomendações para produção:

1. **Firewall**: Libere apenas a porta 3344
2. **HTTPS**: Use nginx como reverse proxy com SSL
3. **Rate limiting**: Implemente limite de requisições
4. **Autenticação**: Adicione API key se necessário
5. **Validação**: Sanitize inputs do usuário

### Exemplo nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:3344;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Performance

- **Tempo médio de geração**: 2-4 segundos por PDF
- **Arquivos temporários**: Limpados automaticamente ao shutdown
- **Limite de pontuação**: 0-60 por estilo (validado na API)

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é privado e de uso interno.

---

## 👤 Autor

**CLAWDEO**
- Especialista em AI Agents para WhatsApp Business
- Integração N8N + CRM + Automação

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a seção **Troubleshooting**
2. Consulte os logs da aplicação
3. Teste os endpoints `/health` e `/templates-disponiveis`

---

## 🎯 Roadmap

- [ ] Docker support
- [ ] Sistema de cache para PDFs
- [ ] API key authentication
- [ ] Webhook para notificações
- [ ] Dashboard de monitoramento
- [ ] Suporte a múltiplos idiomas
- [ ] Testes automatizados

---

**Versão:** 1.0.0  
**Última atualização:** Janeiro 2025
