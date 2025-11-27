"""
API para geração de Relatórios LSP-R
VERSÃO 1.4.1 - DEBUG EXTREMO
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
from docx import Document
from docx.shared import Pt
from datetime import datetime
import subprocess
import shutil
from PyPDF2 import PdfMerger
import logging
import re

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Relatório LSP-R", version="1.4.1")

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


def debug_documento(doc, label=""):
    """Debug: mostrar estrutura do documento"""
    logger.debug(f"=== DEBUG DOCUMENTO {label} ===")
    logger.debug(f"Total de parágrafos: {len(doc.paragraphs)}")
    
    for i, para in enumerate(doc.paragraphs[:15]):  # Primeiros 15 parágrafos
        logger.debug(f"Parágrafo {i}: '{para.text[:100]}'")
        logger.debug(f"  Total de runs: {len(para.runs)}")
        for j, run in enumerate(para.runs[:5]):  # Primeiros 5 runs
            logger.debug(f"    Run {j}: '{run.text}' | Font: {run.font.name} | Size: {run.font.size}")


def substituir_campos_docx(doc_path: Path, dados: RelatorioRequest, output_path: Path):
    """Substitui campos com DEBUG EXTREMO"""
    try:
        logger.info("="*80)
        logger.info(f"INICIANDO SUBSTITUIÇÃO DE CAMPOS")
        logger.info(f"Template: {doc_path.name}")
        logger.info(f"Participante: {dados.participante}")
        logger.info(f"Pontuações: P={dados.pontuacoes.PESSOAS}, A={dados.pontuacoes.ACAO}, T={dados.pontuacoes.TEMPO}, M={dados.pontuacoes.MENSAGEM}")
        logger.info("="*80)
        
        # Carregar documento
        doc = Document(doc_path)
        logger.info(f"✓ Documento carregado: {len(doc.paragraphs)} parágrafos")
        
        # Debug inicial
        debug_documento(doc, "ANTES")
        
        # Preparar dados
        pont_map = {
            "PESSOAS": str(dados.pontuacoes.PESSOAS),
            "ACAO": str(dados.pontuacoes.ACAO),
            "TEMPO": str(dados.pontuacoes.TEMPO),
            "MENSAGEM": str(dados.pontuacoes.MENSAGEM)
        }
        
        predominante_texto = NOMES_ESTILOS_LONGOS[dados.predominante]
        menos_desenvolvido_texto = NOMES_ESTILOS_LONGOS[dados.menosDesenvolvido]
        
        substituicoes_feitas = 0
        
        # Percorrer parágrafos
        for i, para in enumerate(doc.paragraphs):
            texto_para = para.text
            
            # 1. NOME DO PARTICIPANTE
            if "Nome completo" in texto_para:
                logger.info(f"→ Parágrafo {i}: ENCONTRADO 'Nome completo'")
                logger.debug(f"  Texto completo: '{texto_para}'")
                logger.debug(f"  Total de runs: {len(para.runs)}")
                
                for j, run in enumerate(para.runs):
                    logger.debug(f"    Run {j}: '{run.text}'")
                    if "Nome completo" in run.text:
                        texto_antigo = run.text
                        run.text = run.text.replace("Nome completo", dados.participante)
                        logger.info(f"  ✓ SUBSTITUÍDO: '{texto_antigo}' → '{run.text}'")
                        substituicoes_feitas += 1
            
            # 2. PONTUAÇÕES
            for estilo_key, pont_valor in pont_map.items():
                estilo_nome = NOMES_ESTILOS[estilo_key]
                
                if estilo_nome in texto_para:
                    logger.info(f"→ Parágrafo {i}: ENCONTRADO '{estilo_nome}'")
                    logger.debug(f"  Texto completo: '{texto_para}'")
                    
                    # Procurar run com número
                    for j in range(len(para.runs) - 1, -1, -1):
                        run = para.runs[j]
                        texto_run = run.text.strip()
                        
                        logger.debug(f"    Run {j}: '{run.text}' (strip: '{texto_run}')")
                        
                        if texto_run.isdigit():
                            # Preservar prefixo (tabs/espaços)
                            prefixo = ""
                            for char in run.text:
                                if char in ['\t', ' ']:
                                    prefixo += char
                                else:
                                    break
                            
                            pont_formatado = pont_valor.rjust(2)
                            texto_antigo = run.text
                            run.text = prefixo + pont_formatado
                            
                            logger.info(f"  ✓ SUBSTITUÍDO PONTUAÇÃO: '{texto_antigo}' → '{run.text}'")
                            logger.debug(f"    Prefixo preservado: {len(prefixo)} caracteres")
                            substituicoes_feitas += 1
                            break
            
            # 3. ESTILO PREDOMINANTE
            if "Estilo predominante:" in texto_para and "Orientado" in texto_para:
                logger.info(f"→ Parágrafo {i}: ENCONTRADO 'Estilo predominante'")
                logger.debug(f"  Texto antes: '{texto_para}'")
                
                texto_completo = "".join(run.text for run in para.runs)
                novo_texto = re.sub(
                    r'(Estilo predominante:\s*)(.+)',
                    r'\1' + predominante_texto,
                    texto_completo
                )
                
                if novo_texto != texto_completo:
                    for run in para.runs:
                        run.text = ""
                    if para.runs:
                        para.runs[0].text = novo_texto
                    logger.info(f"  ✓ SUBSTITUÍDO: '{predominante_texto}'")
                    substituicoes_feitas += 1
            
            # 4. ESTILO MENOS DESENVOLVIDO
            if "Estilo menos desenvolvido:" in texto_para and "Orientado" in texto_para:
                logger.info(f"→ Parágrafo {i}: ENCONTRADO 'Estilo menos desenvolvido'")
                
                texto_completo = "".join(run.text for run in para.runs)
                novo_texto = re.sub(
                    r'(Estilo menos desenvolvido:\s*)(.+)',
                    r'\1' + menos_desenvolvido_texto,
                    texto_completo
                )
                
                if novo_texto != texto_completo:
                    for run in para.runs:
                        run.text = ""
                    if para.runs:
                        para.runs[0].text = novo_texto
                    logger.info(f"  ✓ SUBSTITUÍDO: '{menos_desenvolvido_texto}'")
                    substituicoes_feitas += 1
        
        # FORÇAR LIBERATION SANS
        logger.info("→ Forçando Liberation Sans 12pt em todo documento...")
        runs_modificados = 0
        for para in doc.paragraphs:
            for run in para.runs:
                run.font.name = 'Liberation Sans'
                run.font.size = Pt(12)
                run.font.highlight_color = None
                runs_modificados += 1
        logger.info(f"  ✓ {runs_modificados} runs modificados")
        
        # Debug final
        debug_documento(doc, "DEPOIS")
        
        # Salvar
        doc.save(output_path)
        logger.info("="*80)
        logger.info(f"✓ DOCUMENTO SALVO: {output_path}")
        logger.info(f"✓ TOTAL DE SUBSTITUIÇÕES: {substituicoes_feitas}")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ERRO: {e}", exc_info=True)
        raise


def converter_docx_para_pdf(docx_path: Path, pdf_path: Path):
    """Converte DOCX para PDF"""
    try:
        logger.info(f"→ Convertendo DOCX → PDF: {docx_path.name}")
        
        comando = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(pdf_path.parent),
            str(docx_path)
        ]
        
        logger.debug(f"  Comando: {' '.join(comando)}")
        
        result = subprocess.run(comando, capture_output=True, text=True, timeout=30)
        
        logger.debug(f"  Return code: {result.returncode}")
        logger.debug(f"  STDOUT: {result.stdout}")
        
        if result.returncode != 0:
            logger.error(f"  STDERR: {result.stderr}")
            raise Exception(f"Conversão falhou: {result.stderr}")
        
        # Renomear
        arquivo_gerado = pdf_path.parent / f"{docx_path.stem}.pdf"
        if arquivo_gerado != pdf_path and arquivo_gerado.exists():
            shutil.move(str(arquivo_gerado), str(pdf_path))
        
        tamanho = pdf_path.stat().st_size if pdf_path.exists() else 0
        logger.info(f"  ✓ PDF gerado: {tamanho} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro na conversão: {e}")
        raise


def juntar_pdfs(capa_pdf: Path, corpo_pdf: Path, output_pdf: Path):
    """Junta PDFs"""
    try:
        logger.info(f"→ Juntando PDFs...")
        logger.debug(f"  Capa: {capa_pdf} ({capa_pdf.stat().st_size} bytes)")
        logger.debug(f"  Corpo: {corpo_pdf} ({corpo_pdf.stat().st_size} bytes)")
        
        merger = PdfMerger()
        merger.append(str(capa_pdf))
        merger.append(str(corpo_pdf))
        merger.write(str(output_pdf))
        merger.close()
        
        tamanho = output_pdf.stat().st_size
        logger.info(f"  ✓ PDF completo: {tamanho} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao juntar: {e}")
        raise


@app.get("/")
async def root():
    return {"message": "API Relatório LSP-R", "version": "1.4.1 DEBUG"}


@app.get("/health")
async def health():
    checks = {
        "templates_dir": TEMPLATES_DIR.exists(),
        "corpos_pdf_dir": CORPOS_PDF_DIR.exists(),
        "libreoffice": shutil.which("libreoffice") is not None
    }
    return {"status": "ok" if all(checks.values()) else "warning", "checks": checks}


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
        logger.info("="*80)
        logger.info(f"REQUISIÇÃO RECEBIDA")
        logger.info(f"Participante: {dados.participante}")
        logger.info(f"Arquivo: {dados.arquivo}")
        logger.info("="*80)
        
        # Validações
        if dados.predominante == dados.menosDesenvolvido:
            raise HTTPException(400, "Predominante e menosDesenvolvido iguais")
        
        if dados.arquivo not in ARQUIVOS_VALIDOS:
            raise HTTPException(400, f"Arquivo inválido: {dados.arquivo}")
        
        template_docx = TEMPLATES_DIR / f"{dados.arquivo}.docx"
        corpo_pdf = CORPOS_PDF_DIR / f"{dados.arquivo}.pdf"
        
        if not template_docx.exists():
            raise HTTPException(404, f"Template não encontrado: {template_docx}")
        
        if not corpo_pdf.exists():
            raise HTTPException(404, f"Corpo não encontrado: {corpo_pdf}")
        
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
            
            logger.info("="*80)
            logger.info("✓✓✓ SUCESSO ✓✓✓")
            logger.info("="*80)
            
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
    logger.info("="*80)
    logger.info("API Relatório LSP-R v1.4.1 DEBUG EXTREMO")
    logger.info("="*80)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3344, log_level="debug")
