"""
Script de testes para API Relatório LSP-R
Execute: python test_api.py
"""

import requests
import json
from pathlib import Path

# Configuração
API_URL = "http://localhost:3344"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def test_health():
    """Teste 1: Health check"""
    print("\n" + "="*50)
    print("Teste 1: Health Check")
    print("="*50)
    
    try:
        response = requests.get(f"{API_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API está rodando - Status: {data['status']}")
            
            # Verificar checks
            checks = data.get('checks', {})
            for check, status in checks.items():
                if status:
                    print_success(f"  {check}: OK")
                else:
                    print_error(f"  {check}: FALHOU")
            
            return True
        else:
            print_error(f"Status code inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Não foi possível conectar à API")
        print_info("Certifique-se de que a API está rodando: python app.py")
        return False
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_templates_disponiveis():
    """Teste 2: Listar templates"""
    print("\n" + "="*50)
    print("Teste 2: Templates Disponíveis")
    print("="*50)
    
    try:
        response = requests.get(f"{API_URL}/templates-disponiveis")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Total esperado: {data['total_esperado']}")
            print_success(f"Templates completos: {data['total_completos']}")
            
            if data['templates_completos']:
                print("\nTemplates prontos para uso:")
                for template in data['templates_completos']:
                    print(f"  • {template}")
            
            if data['templates_incompletos']:
                print_warning(f"\nTemplates incompletos: {len(data['templates_incompletos'])}")
                for item in data['templates_incompletos']:
                    print(f"  • {item['arquivo']}")
                    print(f"    - DOCX: {'✓' if item['docx_existe'] else '✗'}")
                    print(f"    - PDF corpo: {'✓' if item['pdf_corpo_existe'] else '✗'}")
            
            return data['total_completos'] > 0
        else:
            print_error(f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_gerar_relatorio_valido():
    """Teste 3: Gerar relatório válido"""
    print("\n" + "="*50)
    print("Teste 3: Gerar Relatório Válido")
    print("="*50)
    
    # Dados de teste
    dados = {
        "participante": "João Silva - TESTE",
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
    
    print_info(f"Testando com arquivo: {dados['arquivo']}")
    print_info(f"Participante: {dados['participante']}")
    
    try:
        response = requests.post(
            f"{API_URL}/gerar-relatorio",
            json=dados,
            timeout=30
        )
        
        if response.status_code == 200:
            # Salvar PDF
            output_file = Path("test_output.pdf")
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            print_success(f"PDF gerado com sucesso!")
            print_success(f"Arquivo salvo em: {output_file.absolute()}")
            print_info(f"Tamanho do arquivo: {len(response.content) / 1024:.2f} KB")
            return True
        elif response.status_code == 404:
            print_error("Template ou corpo do PDF não encontrado")
            print_warning("Execute test_templates_disponiveis() para ver o que está faltando")
            return False
        else:
            print_error(f"Status code: {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Erro: {error_data.get('detail', 'Desconhecido')}")
            except:
                print_error(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Timeout - A geração do PDF demorou muito")
        return False
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_validacoes():
    """Teste 4: Validações de entrada"""
    print("\n" + "="*50)
    print("Teste 4: Validações de Entrada")
    print("="*50)
    
    testes = [
        {
            "nome": "Predominante = Menos desenvolvido",
            "dados": {
                "participante": "Teste",
                "pontuacoes": {"PESSOAS": 25, "ACAO": 25, "TEMPO": 25, "MENSAGEM": 25},
                "predominante": "TEMPO",
                "menosDesenvolvido": "TEMPO",
                "arquivo": "relatório_mais_tempo_e_menos_ação"
            },
            "deve_falhar": True
        },
        {
            "nome": "Pontuação inválida (>60)",
            "dados": {
                "participante": "Teste",
                "pontuacoes": {"PESSOAS": 70, "ACAO": 25, "TEMPO": 25, "MENSAGEM": 25},
                "predominante": "PESSOAS",
                "menosDesenvolvido": "ACAO",
                "arquivo": "relatório_mais_pessoas_e_menos_ação"
            },
            "deve_falhar": True
        },
        {
            "nome": "Nome vazio",
            "dados": {
                "participante": "",
                "pontuacoes": {"PESSOAS": 25, "ACAO": 25, "TEMPO": 25, "MENSAGEM": 25},
                "predominante": "PESSOAS",
                "menosDesenvolvido": "ACAO",
                "arquivo": "relatório_mais_pessoas_e_menos_ação"
            },
            "deve_falhar": True
        },
        {
            "nome": "Arquivo inválido",
            "dados": {
                "participante": "Teste",
                "pontuacoes": {"PESSOAS": 25, "ACAO": 25, "TEMPO": 25, "MENSAGEM": 25},
                "predominante": "PESSOAS",
                "menosDesenvolvido": "ACAO",
                "arquivo": "arquivo_que_nao_existe"
            },
            "deve_falhar": True
        }
    ]
    
    resultados = []
    for teste in testes:
        print(f"\n  Testando: {teste['nome']}")
        
        try:
            response = requests.post(
                f"{API_URL}/gerar-relatorio",
                json=teste['dados'],
                timeout=10
            )
            
            if teste['deve_falhar']:
                if response.status_code >= 400:
                    print_success("  Validação funcionou corretamente")
                    resultados.append(True)
                else:
                    print_error("  Deveria ter falhado mas não falhou!")
                    resultados.append(False)
            else:
                if response.status_code == 200:
                    print_success("  Request válido aceito")
                    resultados.append(True)
                else:
                    print_error("  Request válido foi rejeitado")
                    resultados.append(False)
                    
        except Exception as e:
            print_error(f"  Erro: {e}")
            resultados.append(False)
    
    return all(resultados)


def test_performance():
    """Teste 5: Performance"""
    print("\n" + "="*50)
    print("Teste 5: Performance (tempo de resposta)")
    print("="*50)
    
    dados = {
        "participante": "Teste Performance",
        "pontuacoes": {"PESSOAS": 30, "ACAO": 20, "TEMPO": 40, "MENSAGEM": 35},
        "predominante": "TEMPO",
        "menosDesenvolvido": "ACAO",
        "arquivo": "relatório_mais_tempo_e_menos_ação"
    }
    
    import time
    
    try:
        print_info("Gerando relatório...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_URL}/gerar-relatorio",
            json=dados,
            timeout=30
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if response.status_code == 200:
            print_success(f"Tempo de resposta: {elapsed:.2f} segundos")
            
            if elapsed < 5:
                print_success("Performance EXCELENTE (< 5s)")
            elif elapsed < 10:
                print_success("Performance BOA (< 10s)")
            else:
                print_warning("Performance ACEITÁVEL (> 10s)")
            
            return True
        else:
            print_error("Falha na geração do PDF")
            return False
            
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def main():
    """Executar todos os testes"""
    print("\n" + "="*70)
    print("  TESTES DA API RELATÓRIO LSP-R")
    print("="*70)
    
    resultados = {}
    
    # Teste 1: Health
    resultados['health'] = test_health()
    
    if not resultados['health']:
        print_error("\nAPI não está acessível. Abortando testes.")
        return
    
    # Teste 2: Templates
    resultados['templates'] = test_templates_disponiveis()
    
    # Teste 3: Gerar relatório
    if resultados['templates']:
        resultados['gerar'] = test_gerar_relatorio_valido()
    else:
        print_warning("\nPulando teste de geração (nenhum template completo)")
        resultados['gerar'] = None
    
    # Teste 4: Validações
    resultados['validacoes'] = test_validacoes()
    
    # Teste 5: Performance
    if resultados['templates']:
        resultados['performance'] = test_performance()
    else:
        resultados['performance'] = None
    
    # Resumo
    print("\n" + "="*70)
    print("  RESUMO DOS TESTES")
    print("="*70)
    
    for teste, resultado in resultados.items():
        if resultado is None:
            status = f"{Colors.YELLOW}⊘ PULADO{Colors.END}"
        elif resultado:
            status = f"{Colors.GREEN}✓ PASSOU{Colors.END}"
        else:
            status = f"{Colors.RED}✗ FALHOU{Colors.END}"
        
        print(f"{teste.ljust(20)}: {status}")
    
    # Resultado final
    testes_executados = [r for r in resultados.values() if r is not None]
    if all(testes_executados):
        print_success("\n🎉 Todos os testes passaram!")
    else:
        print_error("\n❌ Alguns testes falharam")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
