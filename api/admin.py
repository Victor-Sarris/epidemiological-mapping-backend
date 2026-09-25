import os
from django.contrib import admin
from dbfread import DBF
import pandas as pd

from .models import PacienteDengue, PacienteTuberculose, PacienteSifilis,UploadDBF, PacienteChagas, PacienteViolenciaDomestica, PacienteHans, PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal
from datetime import datetime


@admin.register(PacienteDengue)
class PacienteDengueAdmin(admin.ModelAdmin):
    list_display = ("numero_notificacao", "id_unidade", "nome_paciente", "data_notificacao", "endereco", "data_nascimento",
                    "data_pri_sintoma", "id_agravo", "hospital", "cs_sexo", "classi_fin")
    search_fields = ("endereco", "id_unidade")


@admin.register(PacienteTuberculose)
class PacienteTuberculoseAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")

@admin.register(PacienteSifilis)
class PacienteSifilisAdmin(admin.ModelAdmin):
    list_display = ("nu_notific", "id_unidade", "un_saude", "nm_ubs", "mu_residen", "nu_notific", "dt_notific", "id_agravo", "nm_pacient")
    search_fields = ("nu_notific", "nu_notific", "id_agravo", "id_unidade")

@admin.register(PacienteChagas)
class PacienteChagasAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")

@admin.register(PacienteViolenciaDomestica)
class PacienteViolenciaDomesticaAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteHans)
class PacienteHansAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteHepatite)
class PacienteHepatiteAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteAnimaisPec)
class PacienteAnimaisPecAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")

@admin.register(PacienteIntoxicacao)
class PacienteIntoxicacaoAdmin(admin.ModelAdmin):
    list_display = ("ano_notific", "nu_notific" )
    search_fields = ("ano_notific", "nu_notific")

@admin.register(PacienteLeish)
class PacienteLeishAdmin(admin.ModelAdmin):
    list_display = ("ano_notific", "nu_notific")
    search_fields = ("ano_notific", "nu_notific")

@admin.register(PacienteAidsAdulto)
class PacienteAidsAdultoAdmin(admin.ModelAdmin):
    list_display = ("ano_notific", "nu_notific")
    search_fields = ("ano_notific", "nu_notific")

@admin.register(CoberturaVacinal)
class CoberturaVacinalAdmin(admin.ModelAdmin):
    list_display = ("ano", 'imunobiologico', "cobertura_percentual", "meta_otima", 'data_atualizacao')
    search_fields = ("ano", 'imunobiologico', "cobertura_percentual", "meta_otima", 'data_atualizacao')


@admin.register(UploadDBF)
class UploadDBFAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        nome_arquivo = os.path.basename(obj.arquivo.name).lower()
        caminho_arquivo = obj.arquivo.path

        # =========================================================
        # 1. NOVA LÓGICA: SE O ARQUIVO FOR CSV (COBERTURA VACINAL)
        # =========================================================
        if nome_arquivo.endswith('.csv'):
            try:
                # Lê o CSV (Arquivos do DataSUS geralmente usam ';' como separador e 'utf-8' ou 'iso-8859-1')
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', low_memory=False)

                # Padroniza nomes das colunas para minúsculo para evitar erros de digitação
                df.columns = df.columns.str.lower()

                # Filtra apenas a cidade desejada (O DataSUS pode usar 'municipio' ou 'no_municipio')
                coluna_municipio = 'municipio' if 'municipio' in df.columns else 'no_municipio'
                if coluna_municipio in df.columns:
                    df = df[df[coluna_municipio].str.upper() == 'FLORIANO']

                # Verifica se as colunas necessárias existem no CSV baixado
                if 'doses_aplicadas' in df.columns and 'populacao_alvo' in df.columns:
                    df['doses_aplicadas'] = pd.to_numeric(df['doses_aplicadas'], errors='coerce').fillna(0)
                    df['populacao_alvo'] = pd.to_numeric(df['populacao_alvo'], errors='coerce').fillna(0)

                    df_agrupado = df.groupby(['ano', 'imunobiologico']).sum().reset_index()

                    df_agrupado['cobertura'] = (df_agrupado['doses_aplicadas'] / df_agrupado['populacao_alvo']) * 100
                    df_agrupado['cobertura'] = df_agrupado['cobertura'].fillna(0)

                    for index, row in df_agrupado.iterrows():
                        meta = 90.0 if 'rotavírus' in str(row['imunobiologico']).lower() else 95.0

                        CoberturaVacinal.objects.update_or_create(
                            ano=int(row['ano']),
                            imunobiologico=str(row['imunobiologico']).strip(),
                            defaults={
                                'cobertura_percentual': round(row['cobertura'], 2),
                                'meta_otima': meta
                            }
                        )
            except Exception as e:
                print(f"Erro ao processar CSV de Vacinas: {e}")

            # Encerra a função aqui para que não tente ler o CSV como DBF
            return

            # =========================================================
        # 2. LÓGICA ORIGINAL: SE O ARQUIVO FOR DBF (SINAN)
        # =========================================================
        try:
            table = DBF(caminho_arquivo, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)
        except Exception as e:
            print(f"Erro ao ler arquivo DBF: {e}")
            return

        def formatar_data(valor_data):
            if not valor_data:
                return None
            try:
                data_limpa = str(valor_data).strip().split(" ")[0]
                if data_limpa == "30/12/1899":
                    return None
                data_obj = datetime.strptime(data_limpa, "%d/%m/%Y")
                return data_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError, AttributeError):
                return None

        registros_dengue = []
        registros_tubercu = []
        registros_sifi = []
        registros_violencia = []
        registros_chagas = []
        registros_hans = []
        registros_hepatite = []
        registros_animaispec = []
        registros_intoxi = []
        registros_leish = []
        registros_aids = []
        registros_vacinas = []

        for record in table:
            if 'deng' in nome_arquivo:
                partes_endereco = [
                    record.get('NM_LOGRADO'),
                    record.get('NM_NUMERO'),
                    record.get('NM_COMPLEM'),
                    record.get('NM_BAIRRO'),
                    record.get('NU_CEP'),
                ]
                partes_validadas = [str(p).strip() for p in partes_endereco if p and str(p).strip()]
                endereco_formatado = ", ".join(partes_validadas)
                nova_linha = PacienteDengue(
                    numero_notificacao=record.get('NU_NOTIFIC'),
                    nome_paciente=record.get('NM_PACIENT'),
                    data_notificacao=formatar_data(record.get('DT_NOTIFIC')),
                    data_pri_sintoma=formatar_data(record.get('DT_SIN_PRI')),
                    data_nascimento=formatar_data(record.get('DT_NASC')),
                    endereco=endereco_formatado,
                    id_agravo=record.get('ID_AGRAVO'),
                    id_unidade=record.get('ID_UNIDADE'),
                    hospital=record.get('HOSPITAL'),
                    cs_sexo=record.get('CS_SEXO'),
                    classi_fin=record.get('CLASSI_FIN'),
                )
                registros_dengue.append(nova_linha)
            elif 'tubercu' in nome_arquivo:
                nova_linha = PacienteTuberculose(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UNIDADE'),
                    nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                )
                registros_tubercu.append(nova_linha)
            elif 'sifi' in nome_arquivo:
                nova_linha = PacienteSifilis(
                    mu_notific=record.get('MU_NOTIFIC'),
                    un_saude=record.get('UN_SADE'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UNIDADE'),
                    mu_residen=record.get('MU_RESIDEN'),
                    nu_notific=record.get('NU_NOTIFIC'),
                    dt_notific=record.get('DT_NOTIFIC'),
                    id_agravo=record.get('ID_AGRAVO'),
                    nm_pacient=record.get('NM_PACIENT'),
                )
                registros_sifi.append(nova_linha)
            elif 'violencia' in nome_arquivo:
                nova_linha = PacienteViolenciaDomestica(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UBS'),
                    nu_notific=record.get('NU_NOTIFIC'),
                )
                registros_violencia.append(nova_linha)
            elif 'chaga' in nome_arquivo:
                nova_linha = PacienteChagas(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UBS'),
                    nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                )
                registros_chagas.append(nova_linha)
            elif 'hans' in nome_arquivo:
                nova_linha = PacienteHans(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UBS'),
                    nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                )
                registros_hans.append(nova_linha)
            elif 'hepatite' in nome_arquivo:
                nova_linha = PacienteHepatite(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UBS'),
                    nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                )
                registros_hepatite.append(nova_linha)
            elif 'animaispec' in nome_arquivo:
                nova_linha = PacienteAnimaisPec(
                    id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                    nm_ubs=record.get('NM_UBS') or record.get('ID_UBS'),
                    hospital=record.get('HOSPITAL') or record.get('HOSPITAL'),
                    ano_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                    nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                )
                registros_animaispec.append(nova_linha)
            elif 'intoxicacao' in nome_arquivo:
                nova_linha = PacienteIntoxicacao(
                    ano_notific=record.get('ANO_NOTIFIC'),
                    nu_notific=record.get('NU_NOTIFIC'),
                )
                registros_intoxi.append(nova_linha)
            elif 'leish' in nome_arquivo:
                nova_linha = PacienteLeish(
                    ano_notific=record.get('ANO_NOTIFIC'),
                    nu_notific=record.get('NU_NOTIFIC'),
                )
                registros_leish.append(nova_linha)
            elif 'aidsadulto' in nome_arquivo:
                nova_linha = PacienteAidsAdulto(
                    ano_notific=record.get('ANO_NOTIFIC'),
                    nu_notific=record.get('NU_NOTIFIC'),
                )
                registros_aids.append(nova_linha)
            elif 'vacinas' in nome_arquivo:
                nova_linha = CoberturaVacinal(
                    ano=record.get('ANO'),
                    imunobiologico=record.get('IMUNOBIOLOGICO'),
                    cobertura_percentual=record.get('COBERTURA_PERCENTUAL'),
                    meta_otima=record.get('META_OTIMA'),
                    data_atualizacao=record.get('DATA_ATUALIZACAO'),
                )
                registros_vacinas.append(nova_linha)

        if registros_dengue:
            PacienteDengue.objects.bulk_create(registros_dengue, ignore_conflicts=True)
        if registros_tubercu:
            PacienteTuberculose.objects.bulk_create(registros_tubercu, ignore_conflicts=True)
        if registros_sifi:
            PacienteSifilis.objects.bulk_create(registros_sifi, ignore_conflicts=True)
        if registros_violencia:
            PacienteViolenciaDomestica.objects.bulk_create(registros_violencia, ignore_conflicts=True)
        if registros_chagas:
            PacienteChagas.objects.bulk_create(registros_chagas, ignore_conflicts=True)
        if registros_hans:
            PacienteHans.objects.bulk_create(registros_hans, ignore_conflicts=True)
        if registros_hepatite:
            PacienteHepatite.objects.bulk_create(registros_hepatite, ignore_conflicts=True)
        if registros_animaispec:
            PacienteAnimaisPec.objects.bulk_create(registros_animaispec, ignore_conflicts=True)
        if registros_intoxi:
            PacienteIntoxicacao.objects.bulk_create(registros_intoxi, ignore_conflicts=True)
        if registros_leish:
            PacienteLeish.objects.bulk_create(registros_leish, ignore_conflicts=True)
        if registros_aids:
            PacienteAidsAdulto.objects.bulk_create(registros_aids, ignore_conflicts=True)
        if registros_vacinas:
            CoberturaVacinal.objects.bulk_create(registros_vacinas, ignore_conflicts=True)