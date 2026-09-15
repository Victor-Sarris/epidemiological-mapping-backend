from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas, PacienteViolenciaDomestica


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PacienteDengueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteDengue
        fields = "__all__"

class PacienteTuberculoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteTuberculose
        fields = "__all__"

class PacienteSifilisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteSifilis
        fields = "__all__"

class PacienteChagasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteChagas
        fields = "__all__"

class PacienteViolenciaDomesticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteViolenciaDomestica
        fields = "__all__"