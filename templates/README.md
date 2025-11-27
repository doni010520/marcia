# 📁 Templates

Esta pasta contém os templates DOCX das capas dos relatórios LSP-R.

---

## 📄 Arquivos Necessários (12 templates)

**Adicione aqui os 12 arquivos DOCX:**

1. `relatório_mais_ação_menos_mensagem.docx`
2. `relatório_mais_ação_menos_pessoas.docx`
3. `relatório_mais_ação_menos_tempo.docx`
4. `relatório_mais_mensagem_menos_ação.docx`
5. `relatório_mais_mensagem_menos_pessoas.docx`
6. `relatório_mais_mensagem_menos_tempo.docx`
7. `relatório_mais_pessoas_e_menos_ação.docx`
8. `relatório_mais_pessoas_e_menos_mensagem.docx`
9. `relatório_mais_pessoas_e_menos_tempo.docx`
10. `relatório_mais_tempo_e_menos_ação.docx`
11. `relatório_mais_tempo_e_menos_mensagem.docx`
12. `relatório_mais_tempo_e_menos_pessoas.docx`

---

## 📝 Especificações dos Templates

### Conteúdo:
Cada template DOCX deve conter APENAS a **primeira página (capa)** com:
- Logo no header
- Título: "Relatório de Perfil de Escuta e Comunicação"
- Campo: "Participante: Nome completo" ← será substituído
- Seção "Resultado geral" com:
  - Tabela de pontuações (4 estilos) ← pontuações serão substituídas
  - Linha "Estilo predominante: ..." ← será substituído
  - Linha "Estilo menos desenvolvido: ..." ← será substituído
- Seção "Descrição geral dos 4 estilos:"
  - 4 parágrafos descritivos
- Nota final

### Formatação:
- **Fonte:** Aptos (Body) 12pt
- **Margens:** 2.5cm (superior/inferior), 3cm (esquerda/direita)
- **Espaçamento:** 5pt antes/depois de cada parágrafo
- **Header:** Logo centralizado
- **Cores:** 
  - Texto principal: Preto
  - "Nome completo": Azul ciano (#00B0F0)

---

## 🔄 Como a API usa os templates

1. API recebe JSON com dados do participante
2. Abre o template DOCX correto (baseado no campo `arquivo`)
3. **Substitui apenas:**
   - "Nome completo" → nome real do participante
   - Pontuações na tabela (4 números)
   - Linha "Estilo predominante: ..." → texto completo
   - Linha "Estilo menos desenvolvido: ..." → texto completo
4. Converte DOCX → PDF (usando LibreOffice)
5. Junta com o corpo do PDF (de `assets/corpos_pdf/`)
6. Retorna PDF completo

---

## ⚠️ Importante

### Campos que serão substituídos:

1. **"Nome completo"** (no parágrafo "Participante:")
   - Texto EXATO: `Nome completo`
   - Será substituído pelo nome real

2. **Pontuações** (números na tabela)
   - Os 4 números nas linhas:
     - Pessoas (Relacional) → número
     - Ação (Processo) → número
     - Tempo (Solução imediata) → número
     - Mensagem (Conteúdo / Analítico) → número

3. **"Estilo predominante: ..."** (parágrafo inteiro)
   - Texto EXATO no início: `Estilo predominante:`
   - Parágrafo inteiro será substituído

4. **"Estilo menos desenvolvido: ..."** (parágrafo inteiro)
   - Texto EXATO no início: `Estilo menos desenvolvido:`
   - Parágrafo inteiro será substituído

### Mantenha EXATAMENTE:
- ✅ Formatação (negrito, fontes, cores)
- ✅ Espaçamentos
- ✅ Alinhamentos
- ✅ Logo no header
- ✅ Estrutura de parágrafos

### NÃO mude:
- ❌ Nomes dos campos que serão substituídos
- ❌ Estrutura geral do documento
- ❌ Ordem das seções

---

## 🧪 Testar Templates

Após adicionar os templates, teste:

```bash
# Verificar se API reconhece os templates
curl http://localhost:3344/templates-disponiveis

# Gerar PDF de teste
curl -X POST http://localhost:3344/gerar-relatorio \
  -H "Content-Type: application/json" \
  -d '{
    "participante": "Teste",
    "pontuacoes": {"PESSOAS": 25, "ACAO": 30, "TEMPO": 35, "MENSAGEM": 28},
    "predominante": "TEMPO",
    "menosDesenvolvido": "PESSOAS",
    "arquivo": "relatório_mais_tempo_e_menos_pessoas"
  }' \
  --output teste.pdf
```

---

## 📋 Diferenças entre os 12 templates

Cada um dos 12 templates tem **descrições diferentes** baseado na combinação predominante/menos desenvolvido. As diferenças estão principalmente nas seções que NÃO são substituídas dinamicamente.

### Estrutura comum a todos:
- ✅ Header com logo
- ✅ Título
- ✅ Campo participante (será substituído)
- ✅ Tabela de pontuações (será substituída)
- ✅ Linhas predominante/menos desenvolvido (serão substituídas)

### O que varia entre templates:
- ℹ️ Textos descritivos específicos
- ℹ️ Recomendações personalizadas
- ℹ️ Análises contextualizadas
- ℹ️ Páginas seguintes (no corpo do PDF)

---

## 🔗 Relação com Corpos PDF

Cada template DOCX deve ter um PDF corpo correspondente:

```
templates/relatório_mais_ação_menos_mensagem.docx
   ↕️
assets/corpos_pdf/relatório_mais_ação_menos_mensagem.pdf
```

**IMPORTANTE:** Os nomes devem ser IDÊNTICOS (exceto extensão)!

---

## 📊 Status

**Situação atual: ⚠️ VAZIO**

Você precisa adicionar os 12 arquivos DOCX aqui antes da API funcionar.

Após adicionar:
- ✅ API reconhecerá automaticamente
- ✅ Endpoint `/templates-disponiveis` listará como completos
- ✅ Geração de PDFs funcionará

---

**Dica:** Você pode começar com apenas 1 template para teste, e depois adicionar os outros 11.
