![logo.png](/docs/images/logo.png)
------
# PipeSUS

![Status: Em Desenvolvimento](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange?style=for-the-badge)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logoColor=white)
![AWS](https://img.shields.io/badge/AWS%20-FF9900?style=for-the-badge&logo=aws&logoColor=white)

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

### Fase 1 — Ingestão: FTP DataSUS → S3 Bronze

**Meta:** EventBridge Scheduler e Lambda funcionais, extraindo arquivos `.dbc` do FTP do DataSUS e depositando-os na camada Bronze com idempotência.

| Entrega | Status |
|---------|--------|
| `src/lambda/ingestao.py` com a função lambda de ingestão | 🔄 |
| **Logs** configurados na `src/lambda/ingestao.py` | 🔲 |
| **EventBridge Scheduler** configurado | 🔲 |
| `notebooks/01-exploracao-ftp-datasus.ipynb` | 🔲 |
| Infrastrutura de provisionamento no Terraform (IaC) | 🔲 |
| `README.md` atualização do andamento do projeto | 🔲 |
| `docs/07-roadmap.md` atualização do andamento do projeto | 🔲 |

---

> Quer acessar o roadmap completo? Veja em [Roadmap de Evolução da Pipeline](/docs/07-roadmap.md).