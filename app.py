"""
API para geração de Relatórios LSP-R
VERSÃO 2.0.1 - Tabela DOCX REAL com bordas invisíveis
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from datetime import datetime
import subprocess
import shutil
from PyPDF2 import PdfMerger
import logging
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Relatório LSP-R", version="2.0.1")

# Diretórios
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
CORPOS_PDF_DIR = BASE_DIR / "assets" / "corpos_pdf"
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

ARQUIVOS_VALIDOS = [
    'relatório_mais_ação_menos_mensagem',
    'relatório_mais_ação_menos_pessoas',
    'relatório_mais_ação_menos_tempo',
    'relatório_mais_mensagem_menos_ação',
    'relatório_mais_mensagem_menos_pessoas',
    'relatório_mais_mensagem_menos_tempo',
    'relatório_mais_pessoas_e_menos_ação',
    'relatório_mais_pessoas_e_menos_mensagem',
    'relatório_mais_pessoas_e_menos_tempo',
    'relatório_mais_tempo_e_menos_ação',
    'relatório_mais_tempo_e_menos_mensagem',
    'relatório_mais_tempo_e_menos_pessoas'
]

NOMES_ESTILOS = {
    "PESSOAS": "Pessoas (Relacional)",
    "ACAO": "Ação (Processo)",
    "TEMPO": "Tempo (Solução imediata)",
    "MENSAGEM": "Mensagem (Conteúdo / Analítico)"
}

NOMES_ESTILOS_LONGOS = {
    "PESSOAS": "Orientado para Pessoas (Relacional)",
    "ACAO": "Orientado para Ação (Processo)",
    "TEMPO": "Orientado para o Tempo (Solução imediata)",
    "MENSAGEM": "Orientado para Mensagem (Conteúdo / Analítico)"
}

class Pontuacoes(BaseModel):
    PESSOAS: int = Field(..., ge=0, le=60)
    ACAO: int = Field(..., ge=0, le=60)
    TEMPO: int = Field(..., ge=0, le=60)
    MENSAGEM: int = Field(..., ge=0, le=60)

class RelatorioRequest(BaseModel):
    participante: str = Field(..., min_length=1)
    pontuacoes: Pontuacoes
    predominante: str = Field(..., pattern="^(PESSOAS|ACAO|TEMPO|MENSAGEM)$")
    menosDesenvolvido: str = Field(..., pattern="^(PESSOAS|ACAO|TEMPO|MENSAGEM)$")
    arquivo: str


def remover_bordas_tabela(tabela):
    """Remove todas as bordas de uma tabela"""
    for row in tabela.rows:
        for cell in row.cells:
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'none')
                tcBorders.append(border)
            tcPr.append(tcBorders)


def criar_tabela_pontuacoes(doc, dados: RelatorioRequest):
    """Cria tabela DOCX real com bordas invisíveis"""
    logger.info("→ Criando tabela de pontuações...")
    
    # Criar tabela: 5 linhas (cabeçalho + 4 dados), 2 colunas
    tabela = doc.add_table(rows=5, cols=2)
    
    # Remover bordas
    remover_bordas_tabela(tabela)
    
    # CABEÇALHO
    cabecalho_cells = tabela.rows[0].cells
    cabecalho_cells[0].text = "Estilo de escuta"
    cabecalho_cells[1].text = "Pontuação"
    
    # Centralizar cabeçalho "Pontuação"
    cabecalho_cells[1].paragraphs[0].alignment = 1  # CENTER
    
    # DADOS (ordem correta)
    dados_tabela = [
        (NOMES_ESTILOS["PESSOAS"], str(dados.pontuacoes.PESSOAS)),
        (NOMES_ESTILOS["ACAO"], str(dados.pontuacoes.ACAO)),
        (NOMES_ESTILOS["TEMPO"], str(dados.pontuacoes.TEMPO)),
        (NOMES_ESTILOS["MENSAGEM"], str(dados.pontuacoes.MENSAGEM))
    ]
    
    for i, (nome, pontuacao) in enumerate(dados_tabela, start=1):
        row = tabela.rows[i]
        row.cells[0].text = nome
        row.cells[1].text = pontuacao
        
        # Alinhar número ao CENTRO (embaixo de "Pontuação")
        row.cells[1].paragraphs[0].alignment = 1  # CENTER
        
        logger.info(f"  ✓ Linha {i}: {nome} = {pontuacao}")
    
    # Aplicar fonte DejaVu Sans em toda tabela
    for row in tabela.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = 'DejaVu Sans'
                    run.font.size = Pt(9)
    
    logger.info("✓ Tabela criada com sucesso")
    return tabela


def substituir_campos_docx(doc_path: Path, dados: RelatorioRequest, output_path: Path):
    """Substitui campos e cria tabela"""
    try:
        logger.info("="*60)
        logger.info(f"PROCESSANDO: {doc_path.name}")
        logger.info(f"Participante: {dados.participante}")
        logger.info("="*60)
        
        doc = Document(doc_path)
        logger.info(f"✓ Documento carregado: {len(doc.paragraphs)} parágrafos")
        
        paragrafos_para_remover = []
        paragrafo_tabela_idx = None
        
        # 1. SUBSTITUIR NOME e MARCAR LINHAS DA TABELA para remoção
        for i, para in enumerate(doc.paragraphs):
            texto = para.text
            
            # Substituir nome
            if "Nome completo" in texto:
                for run in para.runs:
                    if "Nome completo" in run.text:
                        run.text = run.text.replace("Nome completo", dados.participante)
                        logger.info(f"✓ Nome substituído: {dados.participante}")
            
            # Identificar cabeçalho da tabela
            if "Estilo de escuta" in texto and "Pontuação" in texto:
                logger.info(f"✓ Encontrado cabeçalho da tabela (parágrafo {i})")
                paragrafo_tabela_idx = i
                paragrafos_para_remover.append(i)
                continue
            
            # Marcar 4 linhas seguintes para remoção
            if paragrafo_tabela_idx is not None:
                offset = i - paragrafo_tabela_idx
                if 1 <= offset <= 4:
                    for estilo_nome in NOMES_ESTILOS.values():
                        if estilo_nome in texto:
                            logger.info(f"✓ Marcado para remoção: linha {i}")
                            paragrafos_para_remover.append(i)
                            break
            
            # Substituir predominante/menos desenvolvido
            if "Estilo predominante:" in texto:
                novo_texto = re.sub(
                    r'(Estilo predominante:\s*)(.+)',
                    r'\1' + NOMES_ESTILOS_LONGOS[dados.predominante],
                    "".join(run.text for run in para.runs)
                )
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = novo_texto
                logger.info("✓ Predominante substituído")
            
            if "Estilo menos desenvolvido:" in texto:
                novo_texto = re.sub(
                    r'(Estilo menos desenvolvido:\s*)(.+)',
                    r'\1' + NOMES_ESTILOS_LONGOS[dados.menosDesenvolvido],
                    "".join(run.text for run in para.runs)
                )
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = novo_texto
                logger.info("✓ Menos desenvolvido substituído")
        
        # 2. REMOVER PARÁGRAFOS DA TABELA ANTIGA
        logger.info(f"→ Removendo {len(paragrafos_para_remover)} parágrafos...")
        for idx in sorted(paragrafos_para_remover, reverse=True):
            p = doc.paragraphs[idx]._element
            p.getparent().remove(p)
        
        # 3. INSERIR TABELA DOCX REAL
        if paragrafo_tabela_idx is not None:
            logger.info("→ Inserindo tabela DOCX...")
            
            # Criar tabela
            tabela = criar_tabela_pontuacoes(doc, dados)
            
            # Inserir no documento (antes do próximo parágrafo)
            para_ref = doc.paragraphs[max(0, paragrafo_tabela_idx - 1)]._element
            para_ref.addnext(tabela._element)
            
            logger.info("✓ Tabela inserida")
        
        # 4. APLICAR DEJAVU SANS em todo documento
        logger.info("→ Aplicando DejaVu Sans 12pt...")
        for para in doc.paragraphs:
            for run in para.runs:
                run.font.name = 'DejaVu Sans'
                run.font.size = Pt(12)
                run.font.highlight_color = None
        
        # Salvar
        doc.save(output_path)
        logger.info(f"✓ Documento salvo: {output_path.name}")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ERRO: {e}", exc_info=True)
        raise


def converter_docx_para_pdf(docx_path: Path, pdf_path: Path):
    """Converte DOCX para PDF usando LibreOffice"""
    try:
        logger.info(f"→ Convertendo para PDF...")
        
        comando = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(pdf_path.parent),
            str(docx_path)
        ]
        
        result = subprocess.run(comando, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"Conversão falhou: {result.stderr}")
        
        # Renomear se necessário
        arquivo_gerado = pdf_path.parent / f"{docx_path.stem}.pdf"
        if arquivo_gerado != pdf_path and arquivo_gerado.exists():
            shutil.move(str(arquivo_gerado), str(pdf_path))
        
        logger.info(f"✓ PDF gerado: {pdf_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro na conversão: {e}")
        raise


def juntar_pdfs(capa_pdf: Path, corpo_pdf: Path, output_pdf: Path):
    """Junta capa e corpo em um PDF final"""
    try:
        logger.info("→ Juntando PDFs...")
        
        merger = PdfMerger()
        merger.append(str(capa_pdf))
        merger.append(str(corpo_pdf))
        merger.write(str(output_pdf))
        merger.close()
        
        logger.info(f"✓ PDF completo: {output_pdf.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao juntar: {e}")
        raise


@app.get("/")
async def root():
    return {"message": "API Relatório LSP-R", "version": "2.0.1"}


@app.get("/health")
async def health():
    checks = {
        "templates_dir": TEMPLATES_DIR.exists(),
        "corpos_pdf_dir": CORPOS_PDF_DIR.exists(),
        "libreoffice": shutil.which("libreoffice") is not None
    }
    return {
        "status": "ok" if all(checks.values()) else "warning",
        "version": "2.0.1",
        "checks": checks
    }


@app.get("/templates-disponiveis")
async def listar_templates():
    templates_completos = []
    for arquivo in ARQUIVOS_VALIDOS:
        docx_exists = (TEMPLATES_DIR / f"{arquivo}.docx").exists()
        pdf_exists = (CORPOS_PDF_DIR / f"{arquivo}.pdf").exists()
        if docx_exists and pdf_exists:
            templates_completos.append(arquivo)
    
    return {"templates_completos": templates_completos, "total": len(templates_completos)}


@app.post("/gerar-relatorio")
async def gerar_relatorio(dados: RelatorioRequest):
    try:
        logger.info("="*60)
        logger.info("NOVA REQUISIÇÃO")
        logger.info("="*60)
        
        # Validações
        if dados.predominante == dados.menosDesenvolvido:
            raise HTTPException(400, "Predominante e menos desenvolvido não podem ser iguais")
        
        if dados.arquivo not in ARQUIVOS_VALIDOS:
            raise HTTPException(400, f"Arquivo inválido: {dados.arquivo}")
        
        template_docx = TEMPLATES_DIR / f"{dados.arquivo}.docx"
        corpo_pdf = CORPOS_PDF_DIR / f"{dados.arquivo}.pdf"
        
        if not template_docx.exists():
            raise HTTPException(404, f"Template não encontrado")
        
        if not corpo_pdf.exists():
            raise HTTPException(404, f"Corpo não encontrado")
        
        # Arquivos temporários
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_docx = TEMP_DIR / f"capa_{timestamp}.docx"
        temp_pdf = TEMP_DIR / f"capa_{timestamp}.pdf"
        temp_final = TEMP_DIR / f"final_{timestamp}.pdf"
        
        try:
            # Processar
            substituir_campos_docx(template_docx, dados, temp_docx)
            converter_docx_para_pdf(temp_docx, temp_pdf)
            juntar_pdfs(temp_pdf, corpo_pdf, temp_final)
            
            logger.info("="*60)
            logger.info("✓✓✓ SUCESSO ✓✓✓")
            logger.info("="*60)
            
            return FileResponse(
                path=str(temp_final),
                media_type="application/pdf",
                filename=f"relatorio_{dados.participante.replace(' ', '_')}.pdf"
            )
            
        finally:
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗✗✗ ERRO FATAL: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@app.on_event("startup")
async def startup():
    logger.info("="*60)
    logger.info("API Relatório LSP-R v2.0.1 - Tabela DOCX Real")
    logger.info("="*60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3344)
