# 📁 Assets

Esta pasta contém os recursos estáticos necessários para a API.

## 📂 Estrutura

```
assets/
├── logo_cerebro.png      ← Logo em azul turquesa
└── corpos_pdf/           ← 12 PDFs do corpo dos relatórios
```

---

## 🖼️ Logo (logo_cerebro.png)

**Adicione aqui:** `logo_cerebro.png`

### Especificações:
- **Formato:** PNG com fundo transparente
- **Tamanho sugerido:** 200x200px a 400x400px
- **Cor:** Azul turquesa claro (#5DD3D3 ou RGB: 93, 211, 211)
- **Conteúdo:** Cérebro estilizado com padrão de engrenagens/circuitos
- **Uso:** Será inserido no header de cada relatório

---

## 📄 Corpos PDF (corpos_pdf/)

**Adicione aqui os 12 PDFs:**

1. `relatório_mais_ação_menos_mensagem.pdf`
2. `relatório_mais_ação_menos_pessoas.pdf`
3. `relatório_mais_ação_menos_tempo.pdf`
4. `relatório_mais_mensagem_menos_ação.pdf`
5. `relatório_mais_mensagem_menos_pessoas.pdf`
6. `relatório_mais_mensagem_menos_tempo.pdf`
7. `relatório_mais_pessoas_e_menos_ação.pdf`
8. `relatório_mais_pessoas_e_menos_mensagem.pdf`
9. `relatório_mais_pessoas_e_menos_tempo.pdf`
10. `relatório_mais_tempo_e_menos_ação.pdf`
11. `relatório_mais_tempo_e_menos_mensagem.pdf`
12. `relatório_mais_tempo_e_menos_pessoas.pdf`

### Especificações:
- **Formato:** PDF
- **Conteúdo:** Corpo completo do relatório (SEM a primeira página/capa)
- **Tamanho:** Variável (tipicamente 500KB - 2MB cada)
- **Importante:** Os nomes dos arquivos devem ser EXATAMENTE iguais aos listados acima

---

## ⚠️ Importante

1. **Nomes dos arquivos:**
   - Devem ser EXATOS (case-sensitive)
   - Use underscores `_` não espaços
   - Sem caracteres especiais além de `_` e `-`

2. **Gitignore:**
   - Por padrão, estes arquivos SERÃO versionados no Git
   - Se quiser evitar versionar (arquivos grandes), descomente no `.gitignore`:
     ```
     assets/logo_cerebro.png
     assets/corpos_pdf/*.pdf
     ```
   - E use Git LFS ou SCP para transferir

3. **Teste:**
   Após adicionar os arquivos, teste:
   ```bash
   curl http://localhost:3344/templates-disponiveis
   ```
   Deve mostrar os 12 templates como "completos"

---

**Status atual: ⚠️ VAZIO - Adicione os arquivos!**
