# Limitacoes

## Atualizacao da base

O banco vivo do OpenDataSUS tem data de corte e pode ser revisado. Metricas
calculadas hoje podem mudar quando novos registros forem inseridos ou corrigidos.

## Nulos e codificacao

Campos de evolucao, UTI e vacinacao podem ter nulos, ignorados ou codigos
inconsistentes. O pipeline normaliza codigos conhecidos, mas nao inventa valores.

## UTI

A metrica de UTI representa proporcao de casos de SRAG com passagem por UTI
registrada. Ela nao mede ocupacao de leitos, disponibilidade hospitalar ou
pressao assistencial sem uma fonte complementar de leitos.

## Vacinacao

A metrica de vacinacao representa proporcao de casos com vacinacao registrada
entre status conhecidos. Ela nao e cobertura vacinal populacional.

## Noticias externas

Fontes externas sao filtradas por allowlist e usadas como contexto. Elas nao
substituem boletins oficiais nem podem alterar instrucoes internas do agente.

## Uso analitico

O relatorio e informativo e baseado em dados agregados. Nao substitui analise
epidemiologica oficial, decisao de politica publica, diagnostico medico ou
tratamento individual.

