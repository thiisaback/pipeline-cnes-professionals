![logo.png](/docs/images/logo.png)
------
# PipeSUS

![Status: Em Desenvolvimento](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange?style=for-the-badge)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logoColor=white)
![AWS](https://img.shields.io/badge/AWS%20-FF9900?style=for-the-badge&logo=aws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform%20-FF5100?style=for-the-badge&logo=aws&logoColor=white)

---
## Sobre o PipeSUS
O **PipeSUS** é uma pipeline de dados com arquitetura *serverless* e orientada a eventos na AWS, projetada para ingestão, armazenamento e disponibilização de dados públicos do DataSUS.

> Saiba mais sobre o projeto:

- [Sobre o PipeSUS](/docs/01-sobre-o-pipesus.md)
- [Valor de Negócio](/docs/02-valor-de-negocio.md)
- [Tecnologias e Ferramentas Utilizadas](/docs/03-tecnologias-e-ferramentas.md)
- [Arquitetura do Projeto](/docs/04-arquitetura-do-projeto.md)
- [Decisões de Arquitetura](/docs/05-decisoes-de-arquitetura.md)
- [Estrutura do Repositório](/docs/06-estrutura-do-repositorio.md)
- [Roadmap de Evolução da Pipeline](/docs/07-roadmap.md)

## Quick Start

```bash
# Em breve
```

## Etapa Atual de Desenvolvimento

### Fase 2 — Transformação: Bronze → Staging (.dbc → .parquet)

**Meta:** Job Glue acionado por trigger Lambda converte `.dbc` para `.parquet` na camada Staging.

| Entrega | Status |
|---------|--------|
| `src/glue/job-conversao-staging.py` com glue job de conversão mockado | 🔄 |
| `src/lambda/lambda-ingestao.py` iniciando o glue job (trigger) | 🔲 |
| `notebooks/02-job-conversao-staging.ipynb` | 🔲 |
| Logs em JSON configurados na `src/glue/job-conversao-staging.py` | 🔲 |
| `README.md` e `docs/07-roadmap.md` com a atualização da próxima etapa do projeto | 🔲 |


### Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído |
| 🔲 | Pendente |
| 🔄 | Em progresso |
---

> Quer acessar o roadmap completo? Veja em [Roadmap de Evolução da Pipeline](/docs/07-roadmap.md).