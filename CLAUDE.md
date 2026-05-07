# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PipeSUS** is a data pipeline that ingests public health data from DataSUS (Brazil's Ministry of Health FTP server) into AWS S3 as a Bronze layer Data Lake, following the Medallion architecture. Currently only Phase 1 (ingestion) is implemented.

The pipeline: connects anonymously to `ftp.datasus.gov.br` → identifies the latest CNES (healthcare facilities registry) competency → compares with what's already in S3 Bronze → deletes outdated files and uploads the latest `.dbc` files to `s3://<bucket>/bronze/cnes/profissionais/`.

## Running the Pipeline

**Via Docker (recommended):**
```bash
cp .env.example .env   # fill in AWS credentials
docker compose up --build
docker compose down
```

**Locally (requires Python 3.12):**
```bash
pip install -r requirements.txt
python main.py
```

## Environment Variables

All required in `.env` (see `.env.example`):
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — IAM credentials with S3 read/write and bucket creation permissions
- `AWS_DEFAULT_REGION` — AWS region for the S3 bucket
- `S3_BUCKET_NAME` — target bucket name (created automatically if it doesn't exist)

## Architecture

```
main.py
└── src/ingestao/ingestao.py   # all pipeline logic
    ├── mapear_arquivos_ftp()          # lists latest .dbc files on DataSUS FTP
    ├── verificar_bucket() / criar_bucket()  # S3 bucket management
    ├── mapear_arquivos_bucket()       # checks existing Bronze layer files
    ├── excluir_arquivos_bucket()      # removes stale competency files
    ├── transferir_ftp_para_s3()       # streams files directly FTP → S3 (no local disk)
    └── processar_ingestao()           # orchestrates the full flow

src/utils/logger.py            # get_logger() factory — console or file handlers
logs/process/                  # structured debug logs per execution (timestamped)
```

**Key design decisions:**
- Files stream directly from FTP to S3 via `urllib.request.urlopen` + `upload_fileobj` — no local disk buffering.
- `.dbc` files are stored raw (Bronze immutability); format conversion is deferred to Phase 2 (AWS Glue).
- The pipeline replaces entire competency batches: if FTP competency > bucket competency, all old files are deleted before uploading the new set.
- Two loggers per run: `logger_console` (INFO to stdout) and `logger_process` (DEBUG to timestamped file in `logs/process/`).

## Planned Phases (Not Yet Implemented)

- **Phase 2:** AWS Lambda trigger on S3 PutObject → AWS Glue job converts `.dbc` to `.parquet` → Silver layer
- **Phase 3:** Amazon Athena queries over Gold layer
- **Phase 4:** Apache Airflow orchestration + Terraform IaC
