# Exemplo de Integração com N8N

## 📋 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW - ANÁLISE DE PERFIL                    │
│                    (Perfil de Escuta e Comunicação - LSP-R)            │
└─────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────────┐
                                    │  Google Sheets      │
                                    │     Trigger         │
                                    │  (Monitora novas    │
                                    │   respostas do      │
                                    │   formulário)       │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │       Code2         │
                                    │  (Calcula perfil    │
                                    │   PESSOAS/ACAO/     │
                                    │   TEMPO/MENSAGEM)   │
                                    │  Define arquivo     │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │    Edit Fields      │
                                    │  (Organiza dados:   │
                                    │   nome, email,      │
                                    │   telefone, perfis) │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │   HTTP Request1     │
                                    │  (Gera relatório    │
                                    │   completo na API)  │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │   HTTP Request2     │
                                    │  (Gera PDF e HTML   │
                                    │   do relatório)     │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │    Send Email       │
                                    │  (Envia relatório   │
                                    │   por email)        │
                                    └──────────┬──────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │ enviar mensagem8    │
                                    │  (Envia PDF via     │
                                    │   WhatsApp/UazAPI)  │
                                    └─────────────────────┘


═══════════════════════════════════════════════════════════════════════════

LEGENDA DE DADOS PROCESSADOS:

┌──────────────────────────────────────────────────────────────────────────┐
│ ENTRADA (Google Sheets):                                                │
│  • 24 perguntas (escala 1-7)                                            │
│  • Nome completo                                                         │
│  • Email                                                                 │
│  • WhatsApp                                                              │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ PROCESSAMENTO (Code2):                                                  │
│  • Calcula pontuações: PESSOAS, AÇÃO, TEMPO, MENSAGEM                  │
│  • Identifica perfil predominante (maior pontuação)                     │
│  • Identifica perfil menos desenvolvido (menor pontuação)               │
│  • Define arquivo de relatório baseado na combinação                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ SAÍDA (HTTP Requests + Email + WhatsApp):                               │
│  • PDF personalizado com análise de perfil                              │
│  • HTML para visualização em email                                      │
│  • Entrega por email e WhatsApp                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuração do HTTP Request Node

### Configuração Básica
```
Name: Gerar Relatório LSP-R
Method: POST
URL: http://seudominio:3344/gerar-relatorio
Authentication: None
```

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
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
```

### Response
```
Response Format: File
Binary Property: data
File Name Expression: relatorio_{{ $json.participante }}.pdf
```

---

## 📝 Function Node - Código de Cálculo

Use o código fornecido pelo cliente:

```javascript
// Mapeamento dos arquivos
const ARQUIVOS = {
  'ACAO-MENSAGEM': 'relatório_mais_ação_menos_mensagem',
  'ACAO-PESSOAS': 'relatório_mais_ação_menos_pessoas',
  'ACAO-TEMPO': 'relatório_mais_ação_menos_tempo',
  'MENSAGEM-ACAO': 'relatório_mais_mensagem_menos_ação',
  'MENSAGEM-PESSOAS': 'relatório_mais_mensagem_menos_pessoas',
  'MENSAGEM-TEMPO': 'relatório_mais_mensagem_menos_tempo',
  'PESSOAS-ACAO': 'relatório_mais_pessoas_e_menos_ação',
  'PESSOAS-MENSAGEM': 'relatório_mais_pessoas_e_menos_mensagem',
  'PESSOAS-TEMPO': 'relatório_mais_pessoas_e_menos_tempo',
  'TEMPO-ACAO': 'relatório_mais_tempo_e_menos_ação',
  'TEMPO-MENSAGEM': 'relatório_mais_tempo_e_menos_mensagem',
  'TEMPO-PESSOAS': 'relatório_mais_tempo_e_menos_pessoas'
};

// Itens de cada perfil
const PERFIS = {
  PESSOAS: [1, 5, 9, 13, 17, 21],
  ACAO: [2, 6, 10, 14, 18, 22],
  TEMPO: [3, 7, 11, 15, 19, 23],
  MENSAGEM: [4, 8, 12, 16, 20, 24]
};

// Pegar dados de entrada
const items = $input.all();
const resultados = [];

for (const item of items) {
  const data = item.json;
  
  // Extrair respostas das perguntas 1 a 24
  const respostas = {};
  for (const [key, value] of Object.entries(data)) {
    const match = key.match(/^(\d+)\./);
    if (match) {
      respostas[parseInt(match[1])] = parseInt(value) || 0;
    }
  }
  
  // Calcular pontuações
  const pont = {
    PESSOAS: PERFIS.PESSOAS.reduce((soma, num) => soma + (respostas[num] || 0), 0),
    ACAO: PERFIS.ACAO.reduce((soma, num) => soma + (respostas[num] || 0), 0),
    TEMPO: PERFIS.TEMPO.reduce((soma, num) => soma + (respostas[num] || 0), 0),
    MENSAGEM: PERFIS.MENSAGEM.reduce((soma, num) => soma + (respostas[num] || 0), 0)
  };
  
  // Identificar predominante (maior pontuação)
  const predominante = Object.keys(pont).reduce((a, b) => 
    pont[a] > pont[b] ? a : b
  );
  
  // Identificar menos desenvolvido (menor pontuação)
  const menosDesenvolvido = Object.keys(pont).reduce((a, b) => 
    pont[a] < pont[b] ? a : b
  );
  
  // Buscar arquivo
  const chave = `${predominante}-${menosDesenvolvido}`;
  const arquivo = ARQUIVOS[chave] || 'arquivo_nao_encontrado.docx';
  
  // Pegar nome do participante
  const participante = data.nome || data.participante || "Participante";
  
  // Retornar resultado
  resultados.push({
    json: {
      participante: participante,
      pontuacoes: pont,
      predominante: predominante,
      menosDesenvolvido: menosDesenvolvido,
      arquivo: arquivo
    }
  });
}

return resultados;
```

---

## 📤 Exemplo de Dados de Teste

### Input (Google Forms)
```json
{
  "nome": "João Silva",
  "1. Questão 1": "5",
  "2. Questão 2": "3",
  "3. Questão 3": "7",
  "4. Questão 4": "6",
  // ... até questão 24
}
```

### Output (Function Node)
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

### Response (API)
Binary PDF file pronto para download/compartilhamento

---

## 🧪 Teste Manual

### cURL
```bash
curl -X POST http://seu-vps:3344/gerar-relatorio \
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
  --output teste_relatorio.pdf
```

### Postman/Insomnia
1. Method: POST
2. URL: `http://seu-vps:3344/gerar-relatorio`
3. Body → JSON:
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
4. Send
5. Save Response → Save to file (PDF)

---

## ⚠️ Tratamento de Erros no N8N

Adicione um **Error Trigger** após o HTTP Request:

```
IF HTTP Request fails:
  ↓
  Send notification to admin (Slack/Email)
  Log error details
  Retry with exponential backoff
```

### Possíveis erros:
- **400**: JSON inválido ou predominante = menosDesenvolvido
- **404**: Template não encontrado
- **500**: Erro de processamento (LibreOffice, conversão, etc)
- **Connection refused**: API não está rodando

---

## 📊 Monitoramento

Adicione nodes para monitorar:
- ✅ Taxa de sucesso (PDF gerado)
- ❌ Taxa de erro
- ⏱️ Tempo de processamento
- 📈 Quantidade de relatórios gerados por dia

---

## 🔄 Workflow Completo (JSON N8N)

```json
{
  "nodes": [
    {
      "parameters": {
        "pollTimes": {
          "item": [
            {
              "mode": "everyMinute"
            }
          ]
        },
        "documentId": {
          "__rl": true,
          "value": "1fwxhe47YTRpzoOHLp1dAm4HI-xnPTD-nY9wOKMoG3EU",
          "mode": "list",
          "cachedResultName": "Perfil de comunicação e escuta ativa em vendas (Responses)",
          "cachedResultUrl": "https://docs.google.com/spreadsheets/d/1fwxhe47YTRpzoOHLp1dAm4HI-xnPTD-nY9wOKMoG3EU/edit?usp=drivesdk"
        },
        "sheetName": {
          "__rl": true,
          "value": 667567621,
          "mode": "list",
          "cachedResultName": "Form Responses 1",
          "cachedResultUrl": "https://docs.google.com/spreadsheets/d/1fwxhe47YTRpzoOHLp1dAm4HI-xnPTD-nY9wOKMoG3EU/edit#gid=667567621"
        },
        "event": "rowAdded",
        "options": {}
      },
      "type": "n8n-nodes-base.googleSheetsTrigger",
      "typeVersion": 1,
      "position": [
        720,
        432
      ],
      "id": "385a9488-1fd4-44a0-9f25-504e41c45bbe",
      "name": "Google Sheets Trigger",
      "retryOnFail": true,
      "executeOnce": true,
      "credentials": {
        "googleSheetsTriggerOAuth2Api": {
          "id": "JKKrcccWexP8Gsrr",
          "name": "Google Sheets Trigger account 2"
        }
      }
    },
    {
      "parameters": {
        "fromEmail": "marcia@criandoclientes.com.br",
        "toEmail": "={{ $('Edit Fields').item.json.email }}",
        "subject": "=Relatorio de Análise de Perfil |{{ $('Edit Fields').item.json.nome }}",
        "html": "={{ $('HTTP Request2').item.json.html }}",
        "options": {
          "appendAttribution": false,
          "attachments": "=data"
        }
      },
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 2.1,
      "position": [
        1840,
        432
      ],
      "id": "57e23672-f5b6-4af3-94b5-51c12201ea75",
      "name": "Send email",
      "webhookId": "dd73ff25-24ab-4bf7-b2ee-c3b16d879ed2",
      "credentials": {
        "smtp": {
          "id": "EKB8mYvn7BcSUhmH",
          "name": "conexao resposta"
        }
      }
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "47ef4400-1786-4ff7-803e-32609a614665",
              "name": "nome",
              "value": "={{ $('Google Sheets Trigger').item.json['Nome completo:'] }}",
              "type": "string"
            },
            {
              "id": "9ec81299-ed00-44ec-a777-6c415facfdb6",
              "name": "email",
              "value": "={{ $('Google Sheets Trigger').item.json['Informe seu melhor e-mail:'] }}",
              "type": "string"
            },
            {
              "id": "6ec5ec6a-2dec-4911-aafd-be29d8ab8837",
              "name": "timestamp",
              "value": "={{ $now }}",
              "type": "string"
            },
            {
              "id": "79ca7e3a-54e5-4a03-9cfc-e60b9ff1af43",
              "name": "pessoas",
              "value": "={{ $json.pontuacoes.PESSOAS }}",
              "type": "string"
            },
            {
              "id": "f502828f-c520-493c-9383-79ae1214b608",
              "name": "acao",
              "value": "={{ $json.pontuacoes.ACAO }}",
              "type": "string"
            },
            {
              "id": "0e020b26-f6d6-4fa6-829f-093b05d85b50",
              "name": "tempo",
              "value": "={{ $json.pontuacoes.TEMPO }}",
              "type": "string"
            },
            {
              "id": "57032cc5-cda3-4035-a871-92e1b67dac7c",
              "name": "mensagem",
              "value": "={{ $json.pontuacoes.MENSAGEM }}",
              "type": "string"
            },
            {
              "id": "d3637808-fd9d-42d6-a01a-6582337bdfce",
              "name": "predominante",
              "value": "={{ $json.predominante }}",
              "type": "string"
            },
            {
              "id": "97caec0e-1ddb-41b0-9f03-cdc29cc49500",
              "name": "menosDesenvolvido",
              "value": "={{ $json.menosDesenvolvido }}",
              "type": "string"
            },
            {
              "id": "5c551932-eb92-444d-9720-c2a7e6e3bb6f",
              "name": "arquivo",
              "value": "={{ $json.arquivo }}",
              "type": "string"
            },
            {
              "id": "9765f765-2091-420c-80f0-f0ee9ed4d143",
              "name": "telefone",
              "value": "={{ $('Google Sheets Trigger').item.json['Qual é o seu número de WhatsApp?  (Use apenas números, com DDD. Ex: 11987654321) Vamos usar esse número só para enviar o seu resultado e informações do treinamento.'] }}",
              "type": "string"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.set",
      "typeVersion": 3.4,
      "position": [
        1168,
        432
      ],
      "id": "c2d5b36a-bff9-494e-b933-48a792207f2b",
      "name": "Edit Fields"
    },
    {
      "parameters": {
        "jsCode": "// ========================================\n// CÓDIGO - PERFIL DE ESTILOS DE ESCUTA (LSP-R)\n// VERSÃO CORRIGIDA - Nomes dos arquivos padronizados\n// ========================================\n\n// Mapeamento CORRETO dos arquivos (conforme GitHub)\nconst ARQUIVOS = {\n  'ACAO-MENSAGEM': 'relatório_mais_ação_menos_mensagem',\n  'ACAO-PESSOAS': 'relatório_mais_ação_menos_pessoas',\n  'ACAO-TEMPO': 'relatório_mais_ação_menos_tempo',\n  \n  'MENSAGEM-ACAO': 'relatório_mais_mensagem_menos_ação',\n  'MENSAGEM-PESSOAS': 'relatório_mais_mensagem_menos_pessoas',\n  'MENSAGEM-TEMPO': 'relatório_mais_mensagem_menos_tempo',\n  \n  'PESSOAS-ACAO': 'relatório_mais_pessoas_e_menos_ação',      // ← CORRIGIDO: \"e_\"\n  'PESSOAS-MENSAGEM': 'relatório_mais_pessoas_e_menos_mensagem', // ← CORRIGIDO: \"e_\"\n  'PESSOAS-TEMPO': 'relatório_mais_pessoas_e_menos_tempo',    // ← CORRIGIDO: \"e_\"\n  \n  'TEMPO-ACAO': 'relatório_mais_tempo_e_menos_ação',          // ← CORRIGIDO: \"e_\"\n  'TEMPO-MENSAGEM': 'relatório_mais_tempo_e_menos_mensagem',  // ← CORRIGIDO: \"e_\"\n  'TEMPO-PESSOAS': 'relatório_mais_tempo_e_menos_pessoas'     // ← CORRIGIDO: \"e_\"\n};\n\n// Itens de cada perfil\nconst PERFIS = {\n  PESSOAS: [1, 5, 9, 13, 17, 21],\n  ACAO: [2, 6, 10, 14, 18, 22],\n  TEMPO: [3, 7, 11, 15, 19, 23],\n  MENSAGEM: [4, 8, 12, 16, 20, 24]\n};\n\n// Pegar dados de entrada\nconst items = $input.all();\nconst resultados = [];\n\nfor (const item of items) {\n  const data = item.json;\n  \n  // Extrair respostas das perguntas 1 a 24\n  const respostas = {};\n  for (const [key, value] of Object.entries(data)) {\n    const match = key.match(/^(\\d+)\\./);\n    if (match) {\n      respostas[parseInt(match[1])] = parseInt(value) || 0;\n    }\n  }\n  \n  // Calcular pontuações\n  const pont = {\n    PESSOAS: PERFIS.PESSOAS.reduce((soma, num) => soma + (respostas[num] || 0), 0),\n    ACAO: PERFIS.ACAO.reduce((soma, num) => soma + (respostas[num] || 0), 0),\n    TEMPO: PERFIS.TEMPO.reduce((soma, num) => soma + (respostas[num] || 0), 0),\n    MENSAGEM: PERFIS.MENSAGEM.reduce((soma, num) => soma + (respostas[num] || 0), 0)\n  };\n  \n  // Identificar predominante (maior pontuação)\n  const predominante = Object.keys(pont).reduce((a, b) => \n    pont[a] > pont[b] ? a : b\n  );\n  \n  // Identificar menos desenvolvido (menor pontuação)\n  const menosDesenvolvido = Object.keys(pont).reduce((a, b) => \n    pont[a] < pont[b] ? a : b\n  );\n  \n  // Buscar arquivo\n  const chave = `${predominante}-${menosDesenvolvido}`;\n  const arquivo = ARQUIVOS[chave];\n  \n  // Validar se arquivo existe\n  if (!arquivo) {\n    throw new Error(`Combinação inválida: ${chave}`);\n  }\n  \n  // Retornar resultado\n  resultados.push({\n    json: {\n      participante: data.nome || data.participante || \"Participante\",\n      pontuacoes: pont,\n      predominante: predominante,\n      menosDesenvolvido: menosDesenvolvido,\n      arquivo: arquivo\n    }\n  });\n}\n\nreturn resultados;"
      },
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        944,
        432
      ],
      "id": "432c9d22-cd10-4d8f-b2a6-5e314ea7178c",
      "name": "Code2"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://benitechlab.uazapi.com/send/media",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "token",
              "value": "=0b8aa281-7ff3-4bad-8e75-11145e6a68cc"
            },
            {
              "name": "content-type",
              "value": "application/json"
            },
            {
              "name": "Accept",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n  \"number\": \"{{ $('Edit Fields').item.json.telefone }}\",\n  \"type\": \"document\",\n  \"file\": \"{{ $('HTTP Request2').item.json.pdf_base64 }}\",\n  \"docName\": \"{{ $('Edit Fields').item.json.nome }}\",\n  \"text\": \"Olá, {{ $('Edit Fields').item.json.nome.split(' ').first() }}!\\n\\nSegue o seu Relatório Personalizado – Perfil de Escuta e Comunicação.\\n\\nEle traz recomendações práticas para melhorar sua conexão com clientes e aumentar seus resultados.\\n\\nVale a leitura! Os insights podem elevar sua conversão em vendas.\\n\\nObrigada por participar.\\n\\nMárcia Shimizu | Criando Clientes\",\n  \"delay\": \"3000\"\n}",
        "options": {
          "timeout": 30000
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        2064,
        432
      ],
      "id": "544c37e3-805a-4887-87a4-8b41358fccc2",
      "name": "enviar mensagem8",
      "retryOnFail": false,
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://benitech-marcia.x3t6qy.easypanel.host/gerar-relatorio-completo",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n    \"participante\": \"{{ $json.nome }}\",\n    \"pontuacoes\": {\n      \"PESSOAS\": {{ $json.pessoas }},\n      \"ACAO\": {{ $json.acao }},\n      \"TEMPO\": {{ $json.tempo }},\n      \"MENSAGEM\": {{ $json.mensagem }}\n    },\n    \"predominante\": \"{{ $json.predominante }}\",\n    \"menosDesenvolvido\": \"{{ $json.menosDesenvolvido }}\",\n    \"arquivo\": \"{{ $json.arquivo }}\"\n  }",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        1392,
        432
      ],
      "id": "3fdeab35-b6f6-4b0b-b39e-7e594201129c",
      "name": "HTTP Request1"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://benitech-marcia.x3t6qy.easypanel.host/gerar-relatorio",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n    \"participante\": \"{{ $('Edit Fields').item.json.nome }}\",\n    \"pontuacoes\": {\n      \"PESSOAS\": {{ $('Edit Fields').item.json.pessoas }},\n      \"ACAO\": {{ $('Edit Fields').item.json.acao }},\n      \"TEMPO\": {{ $('Edit Fields').item.json.tempo }},\n      \"MENSAGEM\": {{ $('Edit Fields').item.json.mensagem }}\n    },\n    \"predominante\": \"{{ $('Edit Fields').item.json.predominante }}\",\n    \"menosDesenvolvido\": \"{{ $('Edit Fields').item.json.menosDesenvolvido }}\",\n    \"arquivo\": \"{{ $('Edit Fields').item.json.arquivo }}\"\n  }",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        1616,
        432
      ],
      "id": "7a346983-1355-4170-b347-ec2219aeaa0a",
      "name": "HTTP Request2"
    }
  ],
  "connections": {
    "Google Sheets Trigger": {
      "main": [
        [
          {
            "node": "Code2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send email": {
      "main": [
        [
          {
            "node": "enviar mensagem8",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Edit Fields": {
      "main": [
        [
          {
            "node": "HTTP Request1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Code2": {
      "main": [
        [
          {
            "node": "Edit Fields",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "enviar mensagem8": {
      "main": [
        []
      ]
    },
    "HTTP Request1": {
      "main": [
        [
          {
            "node": "HTTP Request2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "HTTP Request2": {
      "main": [
        [
          {
            "node": "Send email",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {
    "Google Sheets Trigger": [
      {
        "Timestamp": "11/6/2025 18:38:53",
        "Nome completo:": "Marcia Shimizu",
        "Informe seu melhor e-mail:": "marciamshimizu@gmail.com",
        "1. Tento entender as emoções e sentimentos de quem está falando.": 7,
        "2. Espero ter todos os fatos antes de formar julgamentos. ": 4,
        "3.   Fico impaciente com pessoas que se alongam nas conversas. ": 6,
        "4.  Frequentemente percebo erros na lógica do que os outros dizem.": 6,
        "5.  Eu escuto para entender as emoções e o estado de espírito de quem fala.": 6,
        "6. Eu escuto tudo o que a pessoa tem a dizer antes de tirar qualquer conclusão.": 2,
        "7.  Tenho dificuldade em ouvir pessoas que demoram para passar suas ideias.": 7,
        "8.  Tendo a notar, de forma natural, erros no que os outros dizem.": 7,
        "9.  Ao ouvir alguém, considero importante entender os sentimentos de quem está falando.": 7,
        "10.  Costumo ouvir tudo o que uma pessoa tem a dizer, para julgar suas ideias.": 2,
        "11.  Fico frustrado quando as pessoas fogem do assunto durante a conversa.": 7,
        "12.  Ao ouvir, foco em possíveis inconsistências e/ou erros no que está sendo dito.": 4,
        "13.  Eu escuto principalmente para construir e manter relacionamentos com as pessoas.": 4,
        "14.  Ao ouvir alguém, procuro não formar opinião até escutar toda a mensagem.": 2,
        "15.  Ao ouvir, fico impaciente quando parece que estão perdendo tempo.": 7,
        "16.  Tenho facilidade para perceber inconsistências no que a pessoa está dizendo.": 7,
        "17.  Gosto de ouvir os outros porque isso me permite me conectar com eles.": 6,
        "18.  Ao ouvir, considero todos os lados da questão antes de responder.": 6,
        "19.  Prefiro quem chega rapidamente no ponto.": 7,
        "20.  Ao ouvir, noto contradições no que as pessoas dizem.": 7,
        "21.  Ao ouvir, foco em entender os sentimentos por trás das palavras.": 7,
        "22.  Para ser justo com os outros, escuto tudo o que têm a dizer antes de formar uma opinião.": 2,
        "23.  Ao ouvir, valorizo quem apresenta informações de forma breve e direta.": 7,
        "24.  Bons ouvintes percebem discrepâncias no que as pessoas dizem.": 7,
        "Email Address": "",
        "Qual é o seu número de WhatsApp?  (Use apenas números, com DDD. Ex: 11987654321) Vamos usar esse número só para enviar o seu resultado e informações do treinamento.": "5511910716677"
      }
    ]
  },
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "f2f5cb03e983ae2d91043df97d8bacb2991fe43e508542051260416ca471316f"
  }
}
```

---

**Dica:** Salve este workflow como template no N8N para reutilizar em novos projetos!
