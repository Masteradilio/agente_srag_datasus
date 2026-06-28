CASE_GROWTH_RATE_7D = "case_growth_rate_7d"
KNOWN_MORTALITY_RATE = "known_mortality_rate"
CRUDE_MORTALITY_RATE = "crude_mortality_rate"
ICU_CASE_RATE = "icu_case_rate"
REGISTERED_VACCINATION_CASE_RATE = "registered_vaccination_case_rate"

METRIC_NAMES = {
    CASE_GROWTH_RATE_7D: "Taxa de aumento de casos em 7 dias",
    KNOWN_MORTALITY_RATE: "Taxa de mortalidade conhecida",
    CRUDE_MORTALITY_RATE: "Taxa de mortalidade bruta",
    ICU_CASE_RATE: "Proporcao de casos de SRAG com passagem por UTI",
    REGISTERED_VACCINATION_CASE_RATE: "Proporcao de casos de SRAG com vacinacao registrada",
}

METRIC_LIMITATIONS = {
    CASE_GROWTH_RATE_7D: "Retorna nulo quando o periodo anterior nao tem casos.",
    KNOWN_MORTALITY_RATE: "Depende do preenchimento do campo de evolucao.",
    ICU_CASE_RATE: (
        "Nao representa ocupacao hospitalar real de leitos sem base complementar "
        "de leitos disponiveis."
    ),
    REGISTERED_VACCINATION_CASE_RATE: (
        "Nao representa cobertura vacinal populacional geral sem denominador populacional."
    ),
}
