"""
API para geração de Relatórios LSP-R (Listening Styles Profile - Revised)
Gera capa personalizada e junta com corpo do relatório em PDF
VERSÃO 1.4.0 - Liberation Sans (equivalente Aptos) + números centralizados
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict
import os
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
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
    version="1.4.0"
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


def substituir_em_run(run, substituicoes: dict):
    """
    Substitui múltiplos textos em um run preservando formatação
    """
    texto = run.text
    texto_original = texto
    
    for antigo, novo in substituicoes.items():
        if antigo in texto:
            texto = texto.replace(antigo, novo)
    
    if texto != texto_original:
        run.text = texto
        return True
    return False


def forcar_fonte_em_documento(doc):
    """
    Força Liberation Sans 12pt em todos os parágrafos do documento
    Liberation Sans é a fonte mais próxima do Aptos (Body) no LibreOffice
    Preserva negrito e outras formatações
    """
    logger.info("Forçando Liberation Sans 12pt em todo o documento...")
    
    for para in doc.paragraphs:
        for run in para.runs:
            # Forçar fonte e tamanho
            run.font.name = 'Liberation Sans'
            run.font.size = Pt(12)
            # Remover highlight
            run.font.highlight_color = None
            # NÃO mexer em: bold, italic, color (preservar)
    
    logger.info("✓ Liberation Sans 12pt aplicado em todo documento")


def substituir_campos_docx(doc_path: Path, dados: RelatorioRequest, output_path: Path):
    """
    Substitui campos dinâmicos no arquivo DOCX de forma robusta
    NOVA ABORDAGEM: Percorre TODOS os runs e substitui texto
    """
    try:
        doc = Document(doc_path)
        
        # Preparar todas as substituições
        substituicoes = {
            "Nome completo": dados.participante,
            # Pontuações - substituir números específicos por contexto
        }
        
        # Pontuações individuais
        pont_map = {
            "PESSOAS": str(dados.pontuacoes.PESSOAS),
            "ACAO": str(dados.pontuacoes.ACAO),
            "TEMPO": str(dados.pontuacoes.TEMPO),
            "MENSAGEM": str(dados.pontuacoes.MENSAGEM)
        }
        
        # Estilos longos
        predominante_texto = NOMES_ESTILOS_LONGOS[dados.predominante]
        menos_desenvolvido_texto = NOMES_ESTILOS_LONGOS[dados.menosDesenvolvido]
        
        logger.info(f"Processando documento: {doc_path.name}")
        logger.info(f"Participante: {dados.participante}")
        logger.info(f"Pontuações: P={pont_map['PESSOAS']}, A={pont_map['ACAO']}, T={pont_map['TEMPO']}, M={pont_map['MENSAGEM']}")
        
        # Percorrer TODOS os parágrafos e runs
        for i, para in enumerate(doc.paragraphs):
            texto_para = para.text
            
            # 1. SUBSTITUIR NOME DO PARTICIPANTE
            if "Nome completo" in texto_para:
                logger.info(f"  Parágrafo {i}: Encontrado 'Nome completo'")
                for run in para.runs:
                    if "Nome completo" in run.text:
                        run.text = run.text.replace("Nome completo", dados.participante)
                        logger.info(f"    ✓ Substituído: '{dados.participante}'")
            
            # 2. SUBSTITUIR PONTUAÇÕES NA TABELA
            # Estratégia: procurar linha com nome do estilo + número
            # PRESERVAR tabs e CENTRALIZAR números
            for estilo_key, pont_valor in pont_map.items():
                estilo_nome = NOMES_ESTILOS[estilo_key]
                
                if estilo_nome in texto_para:
                    logger.info(f"  Parágrafo {i}: Encontrado '{estilo_nome}'")
                    
                    # Encontrar o run que contém APENAS dígitos (geralmente o último)
                    for j in range(len(para.runs) - 1, -1, -1):
                        run = para.runs[j]
                        texto_run = run.text.strip()
                        
                        # Se o run é APENAS um número (ou tabs + número)
                        if texto_run.isdigit():
                            # Preservar tabs/espaços do início
                            prefixo = ""
                            for char in run.text:
                                if char in ['\t', ' ']:
                                    prefixo += char
                                else:
                                    break
                            
                            # Centralizar número (adicionar espaços se número for 1 dígito)
                            # Para centralizar sob "Pontuação", alinhamos à direita com 2 dígitos
                            pont_formatado = pont_valor.rjust(2)  # Alinha à direita com 2 chars
                            
                            # Reconstruir com tabs + número centralizado
                            run.text = prefixo + pont_formatado
                            logger.info(f"    ✓ Substituído pontuação: {texto_run} → {pont_valor} (tabs preservados, centralizado)")
                            break
            
            # 3. SUBSTITUIR ESTILO PREDOMINANTE
            if "Estilo predominante:" in texto_para and "Orientado" in texto_para:
                logger.info(f"  Parágrafo {i}: Encontrado 'Estilo predominante'")
                # Substituir todo texto após "Estilo predominante: "
                texto_completo = ""
                for run in para.runs:
                    texto_completo += run.text
                
                # Usar regex para encontrar e substituir
                novo_texto = re.sub(
                    r'(Estilo predominante:\s*)(.+)',
                    r'\1' + predominante_texto,
                    texto_completo
                )
                
                if novo_texto != texto_completo:
                    # Limpar todos os runs e recriar
                    for run in para.runs:
                        run.text = ""
                    if para.runs:
                        para.runs[0].text = novo_texto
                    logger.info(f"    ✓ Substituído: {predominante_texto}")
            
            # 4. SUBSTITUIR ESTILO MENOS DESENVOLVIDO
            if "Estilo menos desenvolvido:" in texto_para and "Orientado" in texto_para:
                logger.info(f"  Parágrafo {i}: Encontrado 'Estilo menos desenvolvido'")
                texto_completo = ""
                for run in para.runs:
                    texto_completo += run.text
                
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
                    logger.info(f"    ✓ Substituído: {menos_desenvolvido_texto}")
        
        # FORÇAR LIBERATION SANS 12PT EM TODO O DOCUMENTO (no final)
        forcar_fonte_em_documento(doc)
        
        # Salvar documento modificado
        doc.save(output_path)
        logger.info(f"✓ DOCX salvo: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao substituir campos: {e}", exc_info=True)
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
        
        logger.info(f"Convertendo DOCX → PDF: {docx_path.name}")
        result = subprocess.run(comando, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"Erro LibreOffice: {result.stderr}")
            raise Exception(f"Falha na conversão: {result.stderr}")
        
        # Renomear arquivo gerado
        arquivo_gerado = pdf_path.parent / f"{docx_path.stem}.pdf"
        if arquivo_gerado != pdf_path and arquivo_gerado.exists():
            shutil.move(str(arquivo_gerado), str(pdf_path))
        
        logger.info(f"✓ PDF gerado: {pdf_path.name}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("✗ Timeout na conversão")
        raise Exception("Timeout na conversão do documento")
    except Exception as e:
        logger.error(f"✗ Erro na conversão: {e}")
        raise


def juntar_pdfs(capa_pdf: Path, corpo_pdf: Path, output_pdf: Path):
    """
    Junta PDF da capa com PDF do corpo
    """
    try:
        merger = PdfMerger()
        
        logger.info(f"Juntando PDFs...")
        logger.info(f"  Capa: {capa_pdf.name}")
        logger.info(f"  Corpo: {corpo_pdf.name}")
        
        merger.append(str(capa_pdf))
        merger.append(str(corpo_pdf))
        
        merger.write(str(output_pdf))
        merger.close()
        
        logger.info(f"✓ PDF completo: {output_pdf.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao juntar PDFs: {e}")
        raise


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "API Relatório LSP-R",
        "version": "1.3.1",
        "endpoints": {
            "health": "/health",
            "gerar": "POST /gerar-relatorio",
            "templates": "/templates-disponiveis"
        }
    }


@app.get("/health")
async def health_check():
    """Verifica saúde da API"""
    checks = {
        "templates_dir": TEMPLATES_DIR.exists(),
        "corpos_pdf_dir": CORPOS_PDF_DIR.exists(),
        "libreoffice": shutil.which("libreoffice") is not None
    }
    
    status = "ok" if all(checks.values()) else "warning"
    
    return {
        "status": status,
        "message": "API Relatório LSP-R v1.4.0",
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
        # Validações
        if dados.predominante == dados.menosDesenvolvido:
            raise HTTPException(
                status_code=400,
                detail="Predominante e menosDesenvolvido não podem ser iguais"
            )
        
        if dados.arquivo not in ARQUIVOS_VALIDOS:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo inválido. Use /templates-disponiveis"
            )
        
        # Verificar arquivos
        template_docx = TEMPLATES_DIR / f"{dados.arquivo}.docx"
        if not template_docx.exists():
            raise HTTPException(status_code=404, detail=f"Template DOCX não encontrado")
        
        corpo_pdf = CORPOS_PDF_DIR / f"{dados.arquivo}.pdf"
        if not corpo_pdf.exists():
            raise HTTPException(status_code=404, detail=f"Corpo PDF não encontrado")
        
        # Arquivos temporários
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_docx = TEMP_DIR / f"capa_{timestamp}.docx"
        temp_capa_pdf = TEMP_DIR / f"capa_{timestamp}.pdf"
        temp_final_pdf = TEMP_DIR / f"relatorio_{timestamp}.pdf"
        
        try:
            logger.info("="*60)
            logger.info(f"GERANDO RELATÓRIO: {dados.arquivo}")
            logger.info("="*60)
            
            # 1. Substituir campos
            substituir_campos_docx(template_docx, dados, temp_docx)
            
            # 2. Converter para PDF
            converter_docx_para_pdf(temp_docx, temp_capa_pdf)
            
            # 3. Juntar PDFs
            juntar_pdfs(temp_capa_pdf, corpo_pdf, temp_final_pdf)
            
            # 4. Retornar
            nome_arquivo = f"relatorio_{dados.participante.replace(' ', '_')}_{timestamp}.pdf"
            
            logger.info("="*60)
            logger.info(f"✓ RELATÓRIO GERADO COM SUCESSO")
            logger.info("="*60)
            
            return FileResponse(
                path=str(temp_final_pdf),
                media_type="application/pdf",
                filename=nome_arquivo
            )
            
        finally:
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ ERRO: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Executa ao iniciar"""
    logger.info("="*60)
    logger.info("API Relatório LSP-R v1.4.0")
    logger.info("="*60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3344)
