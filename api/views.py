from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count
from .models import PacienteDengue
from .serializers import PacienteDengueSerializer, PacienteTuberculoseSerializer, PacienteViolenciaDomestica, \
    PacienteSifilis, \
    PacienteSifilisSerializer, PacienteViolenciaDomesticaSerializer, PacienteChagas, PacienteChagasSerializer
from api.models import PacienteTuberculose


class PacienteDengueViewSet(viewsets.ReadOnlyModelViewSet):
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

@api_view(['GET'])
def casos_por_bairro(request): # funcao para agrupar o campo bairro e contar os numeros de registros
    dados = PacienteDengue.objects.values('bairro').annotate(casos=Count('id'))
    # dados formatados
    dados_formatados = {item['bairro']: item['casos'] for item in dados if item['bairro']}

    return Response(dados_formatados)