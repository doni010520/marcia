"""
API para geração de Relatórios LSP-R (Listening Styles Profile - Revised)
Gera capa personalizada e junta com corpo do relatório em PDF
VERSÃO 1.2.0 - Força Arial 12pt e remove fundo azul no nome do participante
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict
import os
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Pt
from datetime import datetime
import subprocess
from PyPDF2 import PdfMerger
import logging
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="API Relatório LSP-R",
    description="API para geração de relatórios de Perfil de Escuta e Comunicação",
    version="1.2.0"
)

# Diretórios
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
CORPOS_PDF_DIR = ASSETS_DIR / "corpos_pdf"
TEMP_DIR = BASE_DIR / "temp"

# Criar diretórios se não existirem
TEMP_DIR.mkdir(exist_ok=True)

# Mapeamento dos 12 arquivos possíveis
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

# Mapeamento de estilos para nomes completos
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


# Modelos de dados
class Pontuacoes(BaseModel):
    PESSOAS: int = Field(..., ge=0, le=60, description="Pontuação Pessoas (0-60)")
    ACAO: int = Field(..., ge=0, le=60, description="Pontuação Ação (0-60)")
    TEMPO: int = Field(..., ge=0, le=60, description="Pontuação Tempo (0-60)")
    MENSAGEM: int = Field(..., ge=0, le=60, description="Pontuação Mensagem (0-60)")


class RelatorioRequest(BaseModel):
    participante: str = Field(..., min_length=1, description="Nome completo do participante")
    pontuacoes: Pontuacoes
    predominante: str = Field(..., pattern="^(PESSOAS|ACAO|TEMPO|MENSAGEM)$")
    menosDesenvolvido: str = Field(..., pattern="^(PESSOAS|ACAO|TEMPO|MENSAGEM)$")
    arquivo: str = Field(..., description="Nome do arquivo template (sem extensão)")


def substituir_texto_em_runs(para, texto_antigo: str, texto_novo: str, forcar_formatacao: bool = False):
    """
    Substitui texto em um parágrafo preservando formatação dos runs
    Se forcar_formatacao=True, força Arial 12pt sem highlight
    """
    texto_completo = para.text
    
    if texto_antigo not in texto_completo:
        return False
    
    # Encontrar posição do texto a substituir
    inicio = texto_completo.find(texto_antigo)
    fim = inicio + len(texto_antigo)
    
    # Calcular posição em cada run
    pos_atual = 0
    run_inicio = None
    run_fim = None
    offset_inicio = 0
    offset_fim = 0
    
    for i, run in enumerate(para.runs):
        run_len = len(run.text)
        
        if run_inicio is None and pos_atual <= inicio < pos_atual + run_len:
            run_inicio = i
            offset_inicio = inicio - pos_atual
        
        if pos_atual <= fim <= pos_atual + run_len:
            run_fim = i
            offset_fim = fim - pos_atual
            break
        
        pos_atual += run_len
    
    if run_inicio is None or run_fim is None:
        return False
    
    # Substituir texto
    if run_inicio == run_fim:
        # Texto está em um único run
        run = para.runs[run_inicio]
        run.text = run.text[:offset_inicio] + texto_novo + run.text[offset_fim:]
        
        # Forçar formatação se necessário
        if forcar_formatacao:
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.font.highlight_color = None  # Remove fundo azul
    else:
        # Texto está em múltiplos runs
        run = para.runs[run_inicio]
        run.text = run.text[:offset_inicio] + texto_novo
        
        # Forçar formatação se necessário
        if forcar_formatacao:
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.font.highlight_color = None
        
        for i in range(run_inicio + 1, run_fim + 1):
            para.runs[i].text = "" if i < run_fim else para.runs[i].text[offset_fim:]
    
    return True


def substituir_numero_tabela(para, pontuacao: str):
    """
    Substitui o número em uma linha da tabela (última sequência de dígitos)
    """
    # Procurar último run com número
    for i in range(len(para.runs) - 1, -1, -1):
        run = para.runs[i]
        # Procurar números no run
        numeros = re.findall(r'\d+', run.text)
        if numeros:
            # Substituir último número encontrado
            ultimo_numero = numeros[-1]
            run.text = run.text.replace(ultimo_numero, pontuacao, 1)  # Substituir apenas primeira ocorrência da direita
            return True
    
    return False


def substituir_campos_docx(doc_path: Path, dados: RelatorioRequest, output_path: Path):
    """
    Substitui campos dinâmicos no arquivo DOCX preservando 100% da formatação
    """
    try:
        doc = Document(doc_path)
        
        # Preparar textos de substituição
        participante_novo = dados.participante
        
        # Pontuações
        pontuacoes_map = {
            "Pessoas (Relacional)": str(dados.pontuacoes.PESSOAS),
            "Ação (Processo)": str(dados.pontuacoes.ACAO),
            "Tempo (Solução imediata)": str(dados.pontuacoes.TEMPO),
            "Mensagem (Conteúdo / Analítico)": str(dados.pontuacoes.MENSAGEM)
        }
        
        # Estilos
        predominante_texto = NOMES_ESTILOS_LONGOS[dados.predominante]
        menos_desenvolvido_texto = NOMES_ESTILOS_LONGOS[dados.menosDesenvolvido]
        
        # Percorrer todos os parágrafos
        for para in doc.paragraphs:
            texto_completo = para.text
            
            # 1. Substituir nome do participante (FORÇAR Arial 12pt sem fundo)
            if "Nome completo" in texto_completo:
                if substituir_texto_em_runs(para, "Nome completo", participante_novo, forcar_formatacao=True):
                    logger.info(f"✓ Substituído 'Nome completo' por '{participante_novo}' (Arial 12pt, sem fundo)")
            
            # 2. Substituir pontuações na tabela
            for estilo_nome, pontuacao in pontuacoes_map.items():
                if estilo_nome in texto_completo:
                    if substituir_numero_tabela(para, pontuacao):
                        logger.info(f"✓ Substituído pontuação em '{estilo_nome}': {pontuacao}")
            
            # 3. Substituir estilo predominante
            if "Estilo predominante:" in texto_completo and "Orientado para" in texto_completo:
                # Encontrar texto após "Estilo predominante: "
                padrao = r"Estilo predominante:\s*(.+?)$"
                match = re.search(padrao, texto_completo)
                if match:
                    texto_antigo = match.group(1).strip()
                    if substituir_texto_em_runs(para, texto_antigo, predominante_texto):
                        logger.info(f"✓ Substituído predominante: {predominante_texto}")
            
            # 4. Substituir estilo menos desenvolvido
            if "Estilo menos desenvolvido:" in texto_completo and "Orientado para" in texto_completo:
                # Encontrar texto após "Estilo menos desenvolvido: "
                padrao = r"Estilo menos desenvolvido:\s*(.+?)$"
                match = re.search(padrao, texto_completo)
                if match:
                    texto_antigo = match.group(1).strip()
                    if substituir_texto_em_runs(para, texto_antigo, menos_desenvolvido_texto):
                        logger.info(f"✓ Substituído menos desenvolvido: {menos_desenvolvido_texto}")
        
        # Salvar documento modificado
        doc.save(output_path)
        logger.info(f"✓ DOCX modificado salvo em: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao substituir campos no DOCX: {e}")
        raise


def converter_docx_para_pdf(docx_path: Path, pdf_path: Path):
    """
    Converte DOCX para PDF usando LibreOffice headless
    """
    try:
        # Comando LibreOffice headless
        comando = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(pdf_path.parent),
            str(docx_path)
        ]
        
        logger.info(f"Convertendo DOCX para PDF: {docx_path}")
        result = subprocess.run(comando, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"Erro na conversão: {result.stderr}")
            raise Exception(f"Falha na conversão DOCX para PDF: {result.stderr}")
        
        # Renomear arquivo gerado (LibreOffice mantém o nome original)
        arquivo_gerado = pdf_path.parent / f"{docx_path.stem}.pdf"
        if arquivo_gerado != pdf_path and arquivo_gerado.exists():
            shutil.move(str(arquivo_gerado), str(pdf_path))
        
        logger.info(f"✓ PDF gerado com sucesso: {pdf_path}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout na conversão DOCX para PDF")
        raise Exception("Timeout na conversão do documento")
    except Exception as e:
        logger.error(f"Erro ao converter DOCX para PDF: {e}")
        raise


def juntar_pdfs(capa_pdf: Path, corpo_pdf: Path, output_pdf: Path):
    """
    Junta PDF da capa com PDF do corpo
    """
    try:
        merger = PdfMerger()
        
        # Adicionar capa (primeira página)
        logger.info(f"Adicionando capa: {capa_pdf}")
        merger.append(str(capa_pdf))
        
        # Adicionar corpo (restante do relatório)
        logger.info(f"Adicionando corpo: {corpo_pdf}")
        merger.append(str(corpo_pdf))
        
        # Salvar PDF final
        merger.write(str(output_pdf))
        merger.close()
        
        logger.info(f"✓ PDF completo gerado: {output_pdf}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao juntar PDFs: {e}")
        raise


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "API Relatório LSP-R",
        "version": "1.2.0",
        "endpoints": {
            "health": "/health",
            "gerar": "POST /gerar-relatorio",
            "templates": "/templates-disponiveis"
        }
    }


@app.get("/health")
async def health_check():
    """Verifica saúde da API"""
    # Verificar se diretórios existem
    checks = {
        "templates_dir": TEMPLATES_DIR.exists(),
        "corpos_pdf_dir": CORPOS_PDF_DIR.exists(),
        "libreoffice": shutil.which("libreoffice") is not None
    }
    
    status = "ok" if all(checks.values()) else "warning"
    
    return {
        "status": status,
        "message": "API Relatório LSP-R v1.2.0",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/templates-disponiveis")
async def listar_templates():
    """Lista templates disponíveis"""
    templates_encontrados = []
    templates_faltando = []
    
    for arquivo in ARQUIVOS_VALIDOS:
        docx_path = TEMPLATES_DIR / f"{arquivo}.docx"
        pdf_path = CORPOS_PDF_DIR / f"{arquivo}.pdf"
        
        status = {
            "arquivo": arquivo,
            "docx_existe": docx_path.exists(),
            "pdf_corpo_existe": pdf_path.exists(),
            "status": "completo" if (docx_path.exists() and pdf_path.exists()) else "incompleto"
        }
        
        if status["status"] == "completo":
            templates_encontrados.append(arquivo)
        else:
            templates_faltando.append(status)
    
    return {
        "templates_completos": templates_encontrados,
        "total_completos": len(templates_encontrados),
        "templates_incompletos": templates_faltando,
        "total_esperado": len(ARQUIVOS_VALIDOS)
    }


@app.post("/gerar-relatorio")
async def gerar_relatorio(dados: RelatorioRequest):
    """
    Gera relatório completo (capa personalizada + corpo)
    """
    try:
        # Validar que predominante != menosDesenvolvido
        if dados.predominante == dados.menosDesenvolvido:
            raise HTTPException(
                status_code=400,
                detail="Predominante e menosDesenvolvido não podem ser iguais"
            )
        
        # Validar arquivo
        if dados.arquivo not in ARQUIVOS_VALIDOS:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo '{dados.arquivo}' não é válido. Use /templates-disponiveis para ver opções."
            )
        
        # Verificar se template DOCX existe
        template_docx = TEMPLATES_DIR / f"{dados.arquivo}.docx"
        if not template_docx.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Template DOCX não encontrado: {dados.arquivo}.docx"
            )
        
        # Verificar se corpo PDF existe
        corpo_pdf = CORPOS_PDF_DIR / f"{dados.arquivo}.pdf"
        if not corpo_pdf.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Corpo do PDF não encontrado: {dados.arquivo}.pdf"
            )
        
        # Criar nome único para arquivos temporários
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_docx = TEMP_DIR / f"capa_{timestamp}.docx"
        temp_capa_pdf = TEMP_DIR / f"capa_{timestamp}.pdf"
        temp_final_pdf = TEMP_DIR / f"relatorio_completo_{timestamp}.pdf"
        
        try:
            # 1. Substituir campos no DOCX
            logger.info(f"Processando template: {dados.arquivo}")
            substituir_campos_docx(template_docx, dados, temp_docx)
            
            # 2. Converter DOCX para PDF (capa)
            converter_docx_para_pdf(temp_docx, temp_capa_pdf)
            
            # 3. Juntar capa + corpo
            juntar_pdfs(temp_capa_pdf, corpo_pdf, temp_final_pdf)
            
            # 4. Retornar PDF
            nome_arquivo_final = f"relatorio_{dados.participante.replace(' ', '_')}_{timestamp}.pdf"
            
            return FileResponse(
                path=str(temp_final_pdf),
                media_type="application/pdf",
                filename=nome_arquivo_final,
                headers={
                    "Content-Disposition": f"attachment; filename={nome_arquivo_final}"
                }
            )
            
        finally:
            # Limpar arquivos temporários após um delay
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar relatório: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Executa ao iniciar a aplicação"""
    logger.info("=" * 50)
    logger.info("API Relatório LSP-R v1.2.0 iniciada")
    logger.info(f"Templates dir: {TEMPLATES_DIR}")
    logger.info(f"Assets dir: {ASSETS_DIR}")
    logger.info(f"Corpos PDF dir: {CORPOS_PDF_DIR}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Executa ao encerrar a aplicação"""
    logger.info("API Relatório LSP-R encerrada")
    
    # Limpar arquivos temporários antigos
    try:
        for arquivo in TEMP_DIR.glob("*"):
            if arquivo.is_file():
                arquivo.unlink()
        logger.info("Arquivos temporários limpos")
    except Exception as e:
        logger.error(f"Erro ao limpar temp: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3344)
