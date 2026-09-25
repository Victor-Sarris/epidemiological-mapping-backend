import requests
import pandas as pd
from django.core.management.base import BaseCommand
from api.models import CoberturaVacinal


class Command(BaseCommand):
    help = 'Busca e processa dados reais de vacinação do OpenDataSUS'

    def handle(self, *args, **options):
        # 1. URL da API do OpenDataSUS (CKAN)
        # IMPORTANTE: Você precisará substituir 'SEU_RESOURCE_ID' pelo código do dataset do PNI no portal
        url = "https://opendatasus.saude.gov.br/api/3/action/datastore_search?resource_id=https://apidadosabertos.saude.gov.br/vacinacao/doses-aplicadas-pni-2026?limit=100&offset=0"

        try:
            self.stdout.write("Conectando à API do DataSUS...")

            # Faz a requisição HTTP real
            response = requests.get(url)
            response.raise_for_status()  # Lança um erro se a API estiver fora do ar

            # Extrai os dados do JSON
            dados_api = response.json()
            registros = dados_api['result']['records']

            if not registros:
                self.stdout.write(self.style.WARNING("A API retornou vazia."))
                return

            self.stdout.write("Processando os dados dinâmicos com Pandas...")

            # 2. Transforma o JSON em DataFrame
            df = pd.DataFrame(registros)

            # 3. A "Peneira" (Filtros e Cálculos)
            # Como a API do SUS traz o Brasil inteiro, você filtra pelo município alvo (Floriano)
            # Nota: O nome exato da coluna depende da tabela do DataSUS (ex: 'sg_uf', 'no_municipio')
            if 'no_municipio' in df.columns:
                df = df[df['no_municipio'] == 'FLORIANO']

            # Converte colunas para números para poder calcular
            df['doses_aplicadas'] = pd.to_numeric(df['doses_aplicadas'], errors='coerce').fillna(0)
            df['populacao_alvo'] = pd.to_numeric(df['populacao_alvo'], errors='coerce').fillna(0)

            # Agrupa os dados somando as doses e a população por vacina e ano
            df_agrupado = df.groupby(['ano', 'imunobiologico']).sum().reset_index()

            # Calcula a cobertura real baseada nos dados recebidos: (Doses / População) * 100
            df_agrupado['cobertura'] = (df_agrupado['doses_aplicadas'] / df_agrupado['populacao_alvo']) * 100
            df_agrupado['cobertura'] = df_agrupado['cobertura'].fillna(0)  # Evita erros de divisão por zero

            self.stdout.write("Atualizando o Banco de Dados do EPI-DATA...")

            # 4. Salva os dados processados no seu banco Django
            for index, row in df_agrupado.iterrows():
                # Define a meta ótima. Rotavírus costuma ser 90, o resto 95.
                meta = 90.0 if 'Rotavírus' in str(row['imunobiologico']) else 95.0

                CoberturaVacinal.objects.update_or_create(
                    ano=int(row['ano']),
                    imunobiologico=str(row['imunobiologico']),
                    defaults={
                        'cobertura_percentual': round(row['cobertura'], 2),
                        'meta_otima': meta
                    }
                )

            self.stdout.write(
                self.style.SUCCESS('Carga dinâmica finalizada! O painel React já reflete os dados reais.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro na integração dinâmica: {e}'))