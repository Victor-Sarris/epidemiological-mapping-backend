CONHECIMENTO_BASE = """
# Sobre a Plataforma EPI-DATA
O EPI-DATA é um sistema de mapeamento epidemiológico setorial e dashboard de saúde pública desenvolvido para a Secretaria de Saúde de Floriano, Piauí. O principal objetivo da plataforma é acompanhar a evolução de casos, monitorar focos de endemias e mapear as zonas de abrangência das Unidades Básicas de Saúde (UBSs), fornecendo suporte à decisão para o controle de surtos e vetores em tempo real.

# Funcionalidades do Sistema e Endemias
A plataforma conta com Dashboards interativos e Mapas de Calor Georreferenciados para diversas endemias. Os agravos monitorados incluem: Dengue, Tuberculose, Sífilis, Doença de Chagas, Violência Doméstica, Hanseníase, Hepatite, Acidentes com Animais Peçonhentos, Intoxicação, Leishmaniose e AIDS Adulto. Através desses painéis, os gestores de saúde podem visualizar curvas epidêmicas, perfis demográficos e distribuição por bairros e quadrantes.

# O Papel do Assistente Virtual
A Inteligência Artificial atua como um assistente de suporte focado em ajudar os usuários a extraírem o máximo da plataforma. A IA é capaz de explicar como os dados são organizados, como ler os mapas de densidade, o que significam os KPIs (Total de Casos, Casos em Alerta) e orientar a navegação geral da interface do usuário. A IA não fornece diagnósticos médicos.

# Importação de Dados DBF
O sistema permite a importação de dados através de arquivos DBF do SINAN. Ao fazer upload, o sistema lê o nome do arquivo para identificar a doença (ex: 'deng' para Dengue, 'tubercu' para Tuberculose, 'sifi' para Sífilis, 'violencia' para Violência Doméstica, etc). O sistema automaticamente limpa os dados, formata as datas (ignorando datas inválidas como 30/12/1899) e agrupa informações de endereço (Logradouro, Número, Complemento, Bairro e CEP).

# Tratamento de Endereços e Localização
Especialmente para os casos de Dengue, o sistema é capaz de gerar relatórios de casos agrupados por bairro. Ele concatena os dados de endereço vindos do arquivo DBF para formatar um endereço completo, permitindo a geolocalização e a contagem de casos através da API de agrupamento de bairros.

# Informações de Contato e Suporte Humano
A IA responde com base no contexto estrutural da plataforma EPI-DATA. Para solicitar acesso a funcionalidades restritas, relatar inconsistências graves nos dados importados via arquivo DBF, falhas no banco de dados, ou para tratar de assuntos sigilosos referentes a pacientes, o usuário deve acionar o suporte humano através do e-mail oficial: vigilanciafloriano@gmail.com.
"""