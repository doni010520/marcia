# Exemplo de Integração com N8N

## 📋 Fluxo Completo

```
┌─────────────────────┐
│  Google Forms       │  ← Usuário responde questionário LSP-R
│  (24 perguntas)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Webhook Trigger    │  ← N8N recebe respostas
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Function Node      │  ← Calcular pontuações (código fornecido)
│  - Somar respostas  │
│  - Identificar      │
│    predominante     │
│  - Identificar      │
│    menos desenv.    │
│  - Definir arquivo  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  HTTP Request       │  ← POST /gerar-relatorio
│  - Enviar JSON      │
│  - Receber PDF      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Google Drive       │  ← Upload do PDF
│  - Salvar relatório │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  WhatsApp/Email     │  ← Enviar para participante
│  - Compartilhar     │
│    link do Drive    │
└─────────────────────┘
```

---

## 🔧 Configuração do HTTP Request Node

### Configuração Básica
```
Name: Gerar Relatório LSP-R
Method: POST
URL: http://seu-vps:3344/gerar-relatorio
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
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "name": "Function - Calcular",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    },
    {
      "name": "HTTP Request - Gerar PDF",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "http://seu-vps:3344/gerar-relatorio",
        "responseFormat": "file"
      }
    },
    {
      "name": "Google Drive - Upload",
      "type": "n8n-nodes-base.googleDrive",
      "position": [850, 300]
    },
    {
      "name": "WhatsApp - Enviar",
      "type": "n8n-nodes-base.whatsapp",
      "position": [1050, 300]
    }
  ]
}
```

---

**Dica:** Salve este workflow como template no N8N para reutilizar em novos projetos!
