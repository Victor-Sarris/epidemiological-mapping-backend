# api/utils/assistente.py
from api.models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas,
    PacienteViolenciaDomestica, PacienteHans, PacienteHepatite,
    PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish,
    PacienteAidsAdulto, CoberturaVacinal,
)

DOENCAS = {
    "dengue":              {"modelo": PacienteDengue,               "campo_ano": "data_notificacao__year", "tem_bairro": True},
    "tuberculose":         {"modelo": PacienteTuberculose,          "campo_ano": "ano_notific",            "tem_bairro": False},
    "sifilis":             {"modelo": PacienteSifilis,              "campo_ano": "ano_notific",            "tem_bairro": False},
    "chagas":              {"modelo": PacienteChagas,               "campo_ano": "ano_notific",            "tem_bairro": False},
    "violencia":           {"modelo": PacienteViolenciaDomestica,   "campo_ano": "ano_notific",            "tem_bairro": False},
    "hanseniase":          {"modelo": PacienteHans,                 "campo_ano": "ano_notific",            "tem_bairro": False},
    "hepatite":            {"modelo": PacienteHepatite,             "campo_ano": "ano_notific",            "tem_bairro": False},
    "animais_peconhentos": {"modelo": PacienteAnimaisPec,           "campo_ano": "ano_notific",            "tem_bairro": False},
    "intoxicacao":         {"modelo": PacienteIntoxicacao,          "campo_ano": "ano_notific",            "tem_bairro": False},
    "leishmaniose":        {"modelo": PacienteLeish,                "campo_ano": "ano_notific",            "tem_bairro": False},
    "aids":                {"modelo": PacienteAidsAdulto,           "campo_ano": "ano_notific",            "tem_bairro": False},
}

ALIASES = {
    "tb": "tuberculose",
    "sífilis": "sifilis",
    "hans": "hanseniase", "hanseníase": "hanseniase",
    "violência": "violencia", "violencia domestica": "violencia", "violência doméstica": "violencia",
    "animais peconhentos": "animais_peconhentos", "animais peçonhentos": "animais_peconhentos",
    "intoxicação": "intoxicacao",
    "leish": "leishmaniose",
    "aids adulto": "aids", "aids adulto ": "aids",
}


def _normalizar_doenca(nome: str):
    if not nome:
        return None
    key = nome.strip().lower()
    if key in DOENCAS:
        return key
    return ALIASES.get(key)


def consultar_casos(doenca: str, ano: int = None, bairro: str = None) -> dict:
    chave = _normalizar_doenca(doenca)
    if not chave:
        return {"erro": f"Doença '{doenca}' não monitorada.",
                "disponiveis": list(DOENCAS.keys())}

    info = DOENCAS[chave]
    qs = info["modelo"].objects.all()

    if ano:
        qs = qs.filter(**{info["campo_ano"]: ano})

    if bairro:
        if not info["tem_bairro"]:
            return {
                "doenca": chave, "ano": ano, "total": qs.count(),
                "aviso": f"Filtro por bairro não está disponível para {chave}. "
                         f"Total geral retornado."
            }
        qs = qs.filter(endereco__icontains=bairro)

    return {"doenca": chave, "ano": ano, "bairro": bairro, "total": qs.count()}


def ranking_bairros(ano: int = None, top: int = 5) -> dict:
    """Ranking de bairros por casos de Dengue.
    Nota: parseia o campo 'endereco' em Python pois não temos um campo
    'bairro' dedicado no modelo. Considere criar esse campo em produção.
    """
    qs = PacienteDengue.objects.all()
    if ano:
        qs = qs.filter(data_notificacao__year=ano)

    contagem = {}
    for endereco in qs.values_list("endereco", flat=True).iterator():
        if not endereco:
            continue
        partes = [p.strip() for p in endereco.split(",") if p.strip()]
        if not partes:
            continue
        ultima = partes[-1]
        eh_cep = (ultima.isdigit() or
                  (ultima.replace("-", "").replace(".", "").isdigit()
                   and len(ultima) <= 10))
        bairro = partes[-2] if (eh_cep and len(partes) >= 2) else partes[-1]
        chave = bairro.upper()
        contagem[chave] = contagem.get(chave, 0) + 1

    ranking = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:int(top)]
    return {"ano": ano, "top": top,
            "ranking": [{"bairro": b, "casos": c} for b, c in ranking]}


def cobertura_vacinal(ano: int = None, imunobiologico: str = None) -> dict:
    qs = CoberturaVacinal.objects.all()
    if ano:
        qs = qs.filter(ano=ano)
    if imunobiologico:
        qs = qs.filter(imunobiologico__icontains=imunobiologico)

    resultados = list(qs.values(
        "ano", "imunobiologico", "cobertura_percentual", "meta_otima"
    )[:30])
    return {"total": qs.count(), "resultados": resultados}


def resumo_geral(ano: int = None) -> dict:
    """Contagem de casos de TODAS as doenças monitoradas."""
    totais = {}
    for chave, info in DOENCAS.items():
        qs = info["modelo"].objects.all()
        if ano:
            qs = qs.filter(**{info["campo_ano"]: ano})
        totais[chave] = qs.count()
    return {"ano": ano, "totais": totais}


TOOLS = [{
    "function_declarations": [
        {
            "name": "consultar_casos",
            "description": (
                "Conta o número de casos notificados de uma doença específica. "
                "Use SEMPRE que o usuário perguntar 'quantos casos de X', 'total de "
                "notificações de X', 'casos de X em 2024', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doenca": {
                        "type": "string",
                        "description": (
                            "Nome da doença. Use um destes valores: dengue, tuberculose, "
                            "sifilis, chagas, violencia, hanseniase, hepatite, "
                            "animais_peconhentos, intoxicacao, leishmaniose, aids."
                        )
                    },
                    "ano": {
                        "type": "integer",
                        "description": "Ano de notificação (ex: 2024). Opcional."
                    },
                    "bairro": {
                        "type": "string",
                        "description": "Nome do bairro. Só suportado para dengue. Opcional."
                    }
                },
                "required": ["doenca"]
            }
        },
        {
            "name": "ranking_bairros",
            "description": (
                "Retorna os bairros com mais casos de DENGUE, ordenados do maior "
                "para o menor. Use para 'qual bairro tem mais casos', 'top bairros'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {"type": "integer", "description": "Ano (opcional)"},
                    "top": {"type": "integer", "description": "Quantos bairros retornar (padrão 5)"}
                }
            }
        },
        {
            "name": "cobertura_vacinal",
            "description": (
                "Retorna dados de cobertura vacinal (percentual e meta) por "
                "imunobiológico. Use para perguntas sobre 'vacinação', 'cobertura', 'BCG'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {"type": "integer", "description": "Ano (opcional)"},
                    "imunobiologico": {
                        "type": "string",
                        "description": "Nome parcial da vacina (ex: 'BCG', 'rotavírus'). Opcional."
                    }
                }
            }
        },
        {
            "name": "resumo_geral",
            "description": (
                "Retorna a contagem de casos de TODAS as doenças monitoradas, "
                "opcionalmente filtrado por ano. Use para 'visão geral', 'panorama', "
                "'resumo das endemias'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {"type": "integer", "description": "Ano (opcional)"}
                }
            }
        }
    ]
}]


FUNCOES_REGISTRADAS = {
    "consultar_casos": consultar_casos,
    "ranking_bairros": ranking_bairros,
    "cobertura_vacinal": cobertura_vacinal,
    "resumo_geral": resumo_geral,
}


def executar_funcao(nome: str, args: dict) -> dict:
    """Dispatcher: executa a função pedida pelo modelo. Nunca levanta exceção —
    sempre devolve um dict, porque o resultado volta pro LLM como texto."""
    fn = FUNCOES_REGISTRADAS.get(nome)
    if not fn:
        return {"erro": f"Função '{nome}' não encontrada."}
    try:
        kwargs = {k: v for k, v in (args or {}).items() if v is not None}
        return fn(**kwargs)
    except Exception as e:
        return {"erro": f"Erro ao executar {nome}: {str(e)}"}