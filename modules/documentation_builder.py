import os
import requests
import json

API_URL = "https://api.openai.com/v1/chat/completions"

def build_documentation(repo_path, classification, commits, code_analysis):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[doc_builder] Chave da API não encontrada.")
        return None

    prompt = build_killer_prompt(repo_path, classification, commits, code_analysis)
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_message = ("Você é um arquiteto de soluções e redator técnico de elite, com a rara habilidade de analisar sistemas complexos e produzir documentação cristalina. "
                      "Sua análise é incisiva, precisa e antecipa as necessidades do leitor. Você segue padrões de documentação rigorosos como o 'Diátaxis' e o 'arc42'. "
                      "Seu público são outros engenheiros de software; a clareza e a precisão técnica são imperativas. Use Markdown e formatação Mermaid para diagramas quando aplicável.")

    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}],
        "temperature": 0.4
    }

    print("[doc_builder] Gerando documentação com o prompt de elite...")
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        response_data = response.json()
        doc_content = response_data["choices"][0]["message"]["content"]
        token_usage = response_data.get("usage", {})
        print(f"[doc_builder] Total de tokens usados: {token_usage.get('total_tokens', 'N/A')}")
        doc_filepath = os.path.join(repo_path, "README_GERADO.md")
        with open(doc_filepath, "w", encoding="utf-8") as f:
            f.write(doc_content)
        return doc_filepath
    except Exception as e:
        print(f"[doc_builder] Erro na chamada da API: {e}")
        return None

def build_killer_prompt(repo_path, classification, commits, code_analysis):
    repo_name = os.path.basename(repo_path.strip("/"))
    prompt = f"""# Análise e Documentação Técnica do Projeto: {repo_name}

## 1. Análise Arquitetural (Framework Diátaxis - Visão Geral)

Com base em toda a informação fornecida (estrutura de arquivos, código-fonte, commits), sintetize a arquitetura do projeto. Descreva o **propósito fundamental**, o **domínio do problema** que ele resolve, e os **principais componentes de software** e suas interações. Se possível, gere um diagrama de componentes simples usando Mermaid.

## 2. Guia de Iniciação Rápida (Tutorial)

Crie um guia passo a passo para um novo desenvolvedor configurar e executar este projeto localmente. Baseie-se nos arquivos de dependência (ex: `package.json`, `requirements.txt`) e de build.

## 3. Referência Técnica Detalhada (How-to Guides & Reference)

### 3.1. Estrutura do Projeto

(Aqui você descreve a estrutura de arquivos que já estava sendo feita)

### 3.2. Análise do Código-Fonte

Para cada arquivo analisado, gere a documentação técnica seguindo o formato rigoroso abaixo:

"""

    for filepath, analysis in code_analysis.items():
        rel_path = os.path.relpath(filepath, repo_path)
        prompt += f"#### Arquivo: `{rel_path}`\n\n"

        if analysis.get("constants"):
            prompt += "##### Constantes e Variáveis Globais\n| Nome | Valor/Inicialização | Descrição |\n|---|---|---|\n"
            for const in analysis["constants"]:
                prompt += f"| `{const['name']}` | `{const.get('value', 'N/A')}` | (Inferir o propósito da constante) |\n"
            prompt += "\n"

        if analysis.get("functions"):
            prompt += "##### Funções\n"
            for func in analysis["functions"]:
                prompt += f"- **Função: `{func['name']}`**\n"
                prompt += f"  - **Descrição:** (Analise o bloco de código e a docstring `{func.get('docstring', 'N/A')}` para criar uma descrição técnica precisa.)\n"
                prompt += f"  - **Parâmetros:**\n    | Nome | Descrição |\n    |---|---|\n"
                if func['args']:
                    for arg in func['args']:
                        prompt += f"    | `{arg}` | (Descreva o parâmetro) |\n"
                else:
                    prompt += "    | N/A | - |\n"
                prompt += f"  - **Retorno:** (Analise o bloco de código para determinar o que é retornado.)\n"
                prompt += f"  - **Bloco de Código:**\n```python\n{func.get('code_block', 'N/A')}\n```\n"

        if analysis.get("endpoints"):
            prompt += "##### Endpoints de API\n| Método | Rota | Propósito Esperado |\n|---|---|---|\n"
            for ep in analysis["endpoints"]:
                prompt += f"| `{ep['method']}` | `{ep['path']}` | (Inferir o propósito do endpoint) |\n"
            prompt += "\n"

    prompt += "## 4. Análise do Histórico de Desenvolvimento (Explanation)\n\nCom base nos commits, resuma a evolução do projeto, destacando as principais features adicionadas e as correções mais relevantes.\n\n"
    # ... (lógica de commits existente)

    prompt += "---\n*Documentação gerada por um especialista em análise de sistemas. Revise para garantir 100% de precisão.*"
    return prompt