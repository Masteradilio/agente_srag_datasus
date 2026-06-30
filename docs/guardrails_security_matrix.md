# Matriz de Guardrails, Segurança e Privacidade

Este documento resume os controles implementados para demonstrar a cobertura de
guardrails, segurança, tratamento de dados sensíveis e transparência técnica.

## Mapa de cobertura

| Camada | Já cobria | Incremento enterprise | Evidência |
|---|---|---|---|
| Input | Escopo SRAG/DataSUS, prompt injection simples, pedido linha a linha, conselho médico individual | Bloqueio de exfiltração de segredos, acesso a arquivos locais/metadata interna, comandos destrutivos, SQL/comandos perigosos e bypass de instruções | `src/guardrails/input_guard.py`, `tests/test_input_guardrails.py` |
| Output | Dados individuais por termo, recomendação clínica individual, fontes, limitações e aviso de uso | Bloqueio de CPF por padrão, credenciais/tokens, caminhos locais, vazamento de system/developer prompt, conteúdo perigoso e URLs fora da allowlist | `src/guardrails/output_guard.py`, `tests/test_output_guardrails.py` |
| Privacy | Tamanho mínimo de grupo, bloqueio de campos individuais e granularidade excessiva | Detecção de CPF, e-mail e telefone nos valores dos registros, além de campos como CNS, cartão SUS, latitude/longitude e endereço | `src/guardrails/privacy.py`, `tests/test_privacy_guardrails.py` |
| Fontes externas | Allowlist de domínios | Validação de URLs também no relatório final, para impedir que uma resposta do LLM introduza fonte fora da allowlist | `src/guardrails/domain_allowlist.py`, `src/guardrails/output_guard.py` |

## Riscos endereçados

- Prompt injection e tentativa de ignorar instruções.
- Vazamento de prompt do sistema, mensagem de desenvolvedor ou instruções internas.
- Exfiltração de chaves de API, tokens, senhas e arquivos `.env`.
- Acesso a recursos locais ou internos, como `file://`, `localhost`, `127.0.0.1`
  e endpoints de metadata.
- Comandos destrutivos ou perigosos, incluindo shell, SQL destrutivo e execução
  dinâmica de código.
- Exposição de dados pessoais ou identificadores individuais em dados de saúde.
- Reidentificação por granularidade excessiva.
- Fontes externas fora da allowlist.
- Recomendações clínicas individualizadas no relatório final.

## Limites assumidos

Os guardrails são implementados como controles determinísticos adequados para uma
PoC técnica. Eles não substituem uma plataforma completa de segurança, DLP ou
moderação especializada, mas reduzem riscos comuns e tornam os critérios de
avaliação auditáveis por código, testes e artefatos de execução.
