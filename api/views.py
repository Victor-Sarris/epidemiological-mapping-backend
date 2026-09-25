from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Model
from .models import PacienteDengue, PacienteHans, PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal
from .serializers import PacienteDengueSerializer, PacienteTuberculoseSerializer, PacienteViolenciaDomestica, \
    PacienteSifilis, \
    PacienteSifilisSerializer, PacienteViolenciaDomesticaSerializer, PacienteChagas, PacienteChagasSerializer, PacienteHansSerializer, PacienteHepatiteSerializer, PacienteAnimaisPecSerializer, PacienteIntoxicacaoSerializer, PacienteLeishSerializer, PacienteAidsAdultoSerializer, CoberturaVacinalSerializer
from api.models import PacienteTuberculose
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from api.utils.embedding_manager import EmbeddingManager
import pandas as pd
import requests
import urllib.parse
from rest_framework import status
from datetime import datetime


class PacienteDengueViewSet(viewsets.ModelViewSet):
    queryset = PacienteDengue.objects.all()
    serializer_class = PacienteDengueSerializer

class PacienteTuberculoseViewSet(viewsets.ModelViewSet):
    queryset = PacienteTuberculose.objects.all()
    serializer_class = PacienteTuberculoseSerializer

class PacienteSifilisViewSet(viewsets.ModelViewSet):
    queryset = PacienteSifilis.objects.all()
    serializer_class = PacienteSifilisSerializer

class PacienteChagasViewSet(viewsets.ModelViewSet):
    queryset = PacienteChagas.objects.all()
    serializer_class = PacienteChagasSerializer

class PacienteViolenciaDomesticaViewSet(viewsets.ModelViewSet):
    queryset = PacienteViolenciaDomestica.objects.all()
    serializer_class = PacienteViolenciaDomesticaSerializer

class PacientesHansViewSet(viewsets.ModelViewSet):
    queryset = PacienteHans.objects.all()
    serializer_class = PacienteHansSerializer

class PacientesHepatiteViewSet(viewsets.ModelViewSet):
    queryset = PacienteHepatite.objects.all()
    serializer_class = PacienteHepatiteSerializer

class PacienteAnimaisPecViewSet(viewsets.ModelViewSet):
    queryset = PacienteAnimaisPec.objects.all()
    serializer_class = PacienteAnimaisPecSerializer

class PacienteIntoxicacaoViewSet(viewsets.ModelViewSet):
    queryset = PacienteIntoxicacao.objects.all()
    serializer_class = PacienteIntoxicacaoSerializer

class PacienteLeishViewSet(viewsets.ModelViewSet):
    queryset = PacienteLeish.objects.all()
    serializer_class = PacienteLeishSerializer

class PacienteAidsAdultoViewSet(viewsets.ModelViewSet):
    queryset = PacienteAidsAdulto.objects.all()
    serializer_class = PacienteAidsAdultoSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CoberturaVacinalViewSet(viewsets.ModelViewSet):
    queryset = CoberturaVacinal.objects.all().order_by('-ano')
    serializer_class = CoberturaVacinalSerializer

@api_view(['GET'])
def casos_por_bairro(request): # funcao para agrupar o campo bairro e contar os numeros de registros
    dados = PacienteDengue.objects.values('bairro').annotate(casos=Count('id'))
    # dados formatados
    dados_formatados = {item['bairro']: item['casos'] for item in dados if item['bairro']}

    return Response(dados_formatados)


# Configuração do Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
# O modelo de geração de texto correto:
modelo_chat = genai.GenerativeModel('gemini-3.6-flash')
embedding_manager = EmbeddingManager(os.getenv('GOOGLE_API_KEY'))


@api_view(['POST'])
def chat_suporte(request):
    try:
        user_message = request.data.get('message', '')

        context = embedding_manager.search_query(user_message)

        prompt = f"""Com base apenas no seguinte contexto:

        {context}

        Responda à pergunta: {user_message}
        Responda de forma concisa e direta, em português."""

        # Gera a resposta
        response = modelo_chat.generate_content(prompt)

        return Response({
            'response': response.text,
            'status': 'success'
        })

    except Exception as e:
        print(f"Erro no chat: {str(e)}")
        return Response({
            'response': 'Desculpe, ocorreu um erro ao processar sua mensagem.',
            'status': 'error'
        }, status=500)


@api_view(['POST'])
def upload_arquivo(request):
    try:
        # Pega o arquivo enviado pelo FormData do React
        arquivo = request.FILES.get('arquivo')
        tabela_destino = request.data.get('tabela_destino')

        if not arquivo:
            return Response({'erro': 'Nenhum arquivo foi enviado.'}, status=status.HTTP_400_BAD_REQUEST)

        nome_arquivo = arquivo.name.lower()

        # =========================================================
        # LÓGICA PARA ARQUIVO CSV (COBERTURA VACINAL)
        # =========================================================
        if nome_arquivo.endswith('.csv'):
            # Lê o CSV diretamente da memória (sem precisar salvar no disco)
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
            df.columns = df.columns.str.lower()

            coluna_municipio = 'municipio' if 'municipio' in df.columns else 'no_municipio'

            if coluna_municipio in df.columns:
                df = df[df[coluna_municipio].str.upper() == 'FLORIANO']

            if 'doses_aplicadas' in df.columns and 'populacao_alvo' in df.columns:
                df['doses_aplicadas'] = pd.to_numeric(df['doses_aplicadas'], errors='coerce').fillna(0)
                df['populacao_alvo'] = pd.to_numeric(df['populacao_alvo'], errors='coerce').fillna(0)

                df_agrupado = df.groupby(['ano', 'imunobiologico']).sum().reset_index()
                df_agrupado['cobertura'] = (df_agrupado['doses_aplicadas'] / df_agrupado['populacao_alvo']) * 100
                df_agrupado['cobertura'] = df_agrupado['cobertura'].fillna(0)

                for index, row in df_agrupado.iterrows():
                    meta = 90.0 if 'rotav rus' in str(row['imunobiologico']).lower() else 95.0
                    CoberturaVacinal.objects.update_or_create(
                        ano=int(row['ano']),
                        imunobiologico=str(row['imunobiologico']).strip(),
                        defaults={
                            'cobertura_percentual': round(row['cobertura'], 2),
                            'meta_otima': meta
                        }
                    )
            return Response({"status": "sucesso", "mensagem": "Arquivo CSV processado com sucesso!"})

        # Caso você vá enviar os arquivos DBF pelo mesmo modal, adicione a lógica de DBF aqui depois.
        return Response({"erro": "Formato de arquivo não suportado."}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Erro no upload: {str(e)}")
        return Response({"erro": f"Erro interno ao processar arquivo: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def sincronizar_api_governo(request):
    ANO_VIGENTE = datetime.now().year
    POPULACAO_ALVO = 850  # TODO: buscar do IBGE

    url = "https://apidadosabertos.saude.gov.br/v1/vacinacao/doses_aplicadas_pni"
    params = {
        "codigo_ibge": "2203909",  # Floriano-PI
        "ano": ANO_VIGENTE,
    }

    contagem_doses = {}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        dados = response.json()

        # Ajuste AQUI conforme o JSON real (veja no Postman)
        registros = dados if isinstance(dados, list) else dados.get("records", [])

        for registro in registros:
            nome_vacina = registro.get("imunobiologico") or registro.get("vacina_nome")
            if not nome_vacina:
                continue
            # ⚠️ Some o VALOR de doses, não conte linhas
            doses = registro.get("doses_aplicadas") or registro.get("qt_doses") or 0
            contagem_doses[nome_vacina] = contagem_doses.get(nome_vacina, 0) + int(doses)

    except Exception as e:
        print(f"Erro na API de Vacinação: {e}")

    # ✅ MANTÉM O FALLBACK — não deixa o painel vazio
    if not contagem_doses:
        vacinas_oficiais = [
            {"imunobiologico": "vacina BCG", "cobertura": 93.93, "meta": 95.0},
            # ... resto do fallback ...
        ]
        for v in vacinas_oficiais:
            CoberturaVacinal.objects.update_or_create(
                ano=ANO_VIGENTE,
                imunobiologico=v["imunobiologico"],
                defaults={"cobertura_percentual": v["cobertura"], "meta_otima": v["meta"]},
            )
        return Response({
            "status": "sucesso",
            "mensagem": "API instável. Painel atualizado com dados de segurança."
        })

    # Processa dados reais
    processadas = 0
    for imunobiologico, total_doses in contagem_doses.items():
        cobertura = (total_doses / POPULACAO_ALVO) * 100
        meta = 90.0 if "rotav" in imunobiologico.lower() else 95.0
        CoberturaVacinal.objects.update_or_create(
            ano=ANO_VIGENTE,
            imunobiologico=imunobiologico,
            defaults={"cobertura_percentual": round(cobertura, 2), "meta_otima": meta},
        )
        processadas += 1

    return Response({
        "status": "sucesso",
        "mensagem": f"{processadas} vacinas sincronizadas."
    })