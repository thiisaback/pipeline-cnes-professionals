# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Visão Geral do Projeto

**PipeSUS** é um pipeline de dados que ingere informações públicas de saúde do DataSUS (servidor FTP do Ministério da Saúde do Brasil) para o AWS S3 como camada Bronze de um Data Lake, seguindo a arquitetura Medallion. Atualmente, apenas a Fase 1 (ingestão) está implementada.

O pipeline: conecta anonimamente a `ftp.datasus.gov.br` → identifica a competência mais recente do CNES (cadastro de estabelecimentos de saúde) → compara com o que já está no S3 Bronze → deleta arquivos desatualizados e faz upload dos arquivos `.dbc` mais recentes para `s3://<bucket>/bronze/cnes/profissionais/`.

## Executando o Pipeline

**Via Docker (recomendado):**
```bash
cp .env.example .env   # preencha as credenciais AWS
docker compose up --build
docker compose down
```

**Localmente (requer Python 3.12):**
```bash
pip install -r requirements.txt
python main.py
```

## Variáveis de Ambiente

Todas obrigatórias no `.env` (veja `.env.example`):
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — credenciais IAM com permissões de leitura/escrita no S3 e criação de bucket
- `AWS_DEFAULT_REGION` — região AWS para o bucket S3
- `S3_BUCKET_NAME` — nome do bucket de destino (criado automaticamente se não existir)

## Arquitetura

```
main.py
└── src/ingestao/ingestao.py   # toda a lógica do pipeline
    ├── mapear_arquivos_ftp()          # lista os arquivos .dbc mais recentes no FTP do DataSUS
    ├── verificar_bucket() / criar_bucket()  # gerenciamento do bucket S3
    ├── mapear_arquivos_bucket()       # verifica os arquivos existentes na camada Bronze
    ├── excluir_arquivos_bucket()      # remove arquivos de competências desatualizadas
    ├── transferir_ftp_para_s3()       # transmite arquivos diretamente FTP → S3 (sem disco local)
    └── processar_ingestao()           # orquestra o fluxo completo

src/utils/logger.py            # fábrica get_logger() — handlers de console ou arquivo
logs/process/                  # logs de debug estruturados por execução (com timestamp)
```

**Decisões de design relevantes:**
- Os arquivos são transmitidos diretamente do FTP para o S3 via `urllib.request.urlopen` + `upload_fileobj` — sem buffer em disco local.
- Os arquivos `.dbc` são armazenados brutos (imutabilidade da camada Bronze); a conversão de formato é adiada para a Fase 2 (AWS Glue).
- O pipeline substitui lotes inteiros de competência: se a competência do FTP for mais recente que a do bucket, todos os arquivos antigos são deletados antes do upload do novo conjunto.
- Dois loggers por execução: `logger_console` (INFO no stdout) e `logger_process` (DEBUG em arquivo com timestamp em `logs/process/`).

## Fases Planejadas (Não Implementadas)

- **Fase 2:** Trigger AWS Lambda no S3 PutObject → job AWS Glue converte `.dbc` para `.parquet` → camada Silver
- **Fase 3:** Consultas Amazon Athena sobre a camada Gold
- **Fase 4:** Orquestração com Apache Airflow + IaC com Terraform
