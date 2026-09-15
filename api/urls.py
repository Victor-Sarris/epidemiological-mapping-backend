from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'dengue', views.PacienteDengueViewSet)
router.register(r'tuberculose', views.PacienteTuberculoseViewSet)
router.register(r'sifilis', views.PacienteSifilisViewSet)
router.register(r'chagas', views.PacienteChagasViewSet)
router.register(r'violencia domestica', views.PacienteViolenciaDomesticaViewSet)
router.register(r'hans', views.PacientesHansViewSet)
router.register(r'hepatite', views.PacientesHepatiteViewSet)
router.register(r'animaispec', views.PacienteAnimaisPecViewSet)
router.register(r'intoxicacao', views.PacienteIntoxicacaoViewSet)
router.register(r'leish', views.PacienteLeishViewSet)
router.register(r'aidsadulta', views.PacienteAidsAdultoViewSet)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/casos_por_bairro/', views.casos_por_bairro, name='casos_por_bairro'),
]