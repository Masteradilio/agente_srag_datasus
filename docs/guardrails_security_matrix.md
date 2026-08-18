# Matriz de Guardrails, Segurança e Privacidade (v2.0.0)

Este documento detalha os controles defensivos, barreira contra injeção adversarial de prompts, proteção à privacidade e conformidade com a LGPD.

## 1. Mapa de Controles e Camadas de Defesa

| Camada de Defesa | Tipos de Ameaça Endereçadas | Mecanismo de Bloqueio | Evidência de Teste |
|---|---|---|---|
| **Input Guardrail** | Direct Prompt Injection, Jailbreak, Exfiltração de `.env`/chaves, SQL Injection, comandos shell | Validação léxica, detecção de padrões perigosos e verificação de escopo temático | `src/guardrails/input_guard.py`, `tests/test_evals_framework.py` |
| **Output Guardrail** | Vazamento de System Prompt, Alucinação de fontes fora da allowlist, caminhos de arquivo locais (`C:\Users`), recomendações médicas individualizadas | Análise sintática de saída, validação de URLs institucionais e regex de PII | `src/guardrails/output_guard.py`, `tests/test_output_guardrails.py` |
| **Privacidade & LGPD** | Exposição de CPF, CNS, nomes de pacientes, e-mails, telefones ou reidentificação de pequenos grupos (< 5 casos) | Filtros de anonimização e mascaramento | `src/guardrails/privacy.py`, `tests/test_privacy_guardrails.py` |
| **Allowlist Institucional** | Injeção indireta via web scraping (*Indirect Prompt Injection*) | Validação estrita de domínio antes do fetch HTTP | `src/guardrails/domain_allowlist.py`, `tests/test_agent_reach_subagents.py` |
| **Contratos Tipados de Ferramenta** | Respostas inválidas de ferramentas ou violação de esquema | Validação Pydantic em runtime | `src/evals/agent_evals.py` |

---

## 2. Resultados do Benchmark Adversarial

No benchmark de segurança executado em `src/evals/agent_evals.py`:
- **Acurácia Defensiva Contra Prompts Maliciosos:** **100.0%**
- **Taxa de Falsos Positivos em Perguntas Legítimas:** **0.0%**
- **Vazamento de Chaves / System Prompts:** **0 incidentes**
