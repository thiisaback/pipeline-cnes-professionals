![logo.png](/docs/images/logo.png)
------
## Decisões de Arquitetura

A escolha pela arquitetura do projeto foi baseada nas seguintes decisões:

- **Arquitetura Medallion:** Separação estrita entre dados brutos, tratados e analíticos para evitar retrabalho de extração em caso de falhas nas regras de negócio.

- **S3 como Data Lake:** Escolhido pelo baixo custo e alta escalabilidade.

- **Retenção do formato `.dbc` na Camada Bronze:** Os arquivos no formato legado `.dbc` do DataSUS são transferidos nesse formato para a nuvem, transferindo o gargalo computacional da descompressão para o processamento distribuído da AWS (Fase 2).

> [Próximo - Estrutura do Repositório >](/docs/06-estrutura-do-repositorio.md)

> [< Anterior - Arquitetura do Projeto](/docs/04-arquitetura-do-projeto.md)