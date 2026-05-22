![logo.png](/docs/images/logo.png)
------
## Roadmap de Evolução da Pipeline

O roadmap está organizado em 6 fases, seguindo o fluxo natural da pipeline de dados: da fundação técnica até a observabilidade em produção.

---

### Fase 0 — Fundação Técnica ✅

**Meta:** ambiente de desenvolvimento funcional e repositório pronto para código.

| Entrega | Status |
|---------|--------|
| Estrutura inicial de diretórios | ✅ |
| `requirements.txt` com dependências do projeto | ✅ |
| `.env.example` documentando variáveis necessárias | ✅ |
| `.gitignore` arquivos e diretórios não commitáveis | ✅ |
| `docs/01-sobre-o-pipesus.md` | ✅ |
| `docs/02-valor-de-negocio.md` | ✅ |
| `docs/03-tecnologias-e-ferramentas.md` | ✅ |
| `docs/04-arquitetura-do-projeto.md` | ✅ |
| `docs/05-decisoes-de-arquitetura.md` | ✅ |
| `docs/06-estrutura-do-repositorio.md` | ✅ |
| `docs/07-roadmap.md` (este documento) | ✅ |

---

### Fase 1 — Ingestão: FTP DataSUS → S3 Bronze

**Meta:** EventBridge Scheduler e Função Lambda funcionais, extraindo arquivos `.dbc` do FTP do DataSUS e os depositando-os na camada Bronze com idempotência.

| Entrega | Status |
|---------|--------|
| `src/lambda/ingestao.py` com a função lambda de ingestão | ✅ |
| **EventBridge Scheduler** configurado | ✅ |
| `notebooks/01-lambda-ingestao.ipynb` | ✅ |
| Logs em JSON configurados na `src/lambda/ingestao.py` | 🔄 |
| `docs/07-roadmap.md` atualização do andamento do projeto | 🔲 |
| `README.md` atualização do andamento do projeto | 🔲 |

---

### Fase 2 — Transformação: Bronze → Staging (.dbc → .parquet)

**Meta:** Job Glue acionado por trigger Lambda converte `.dbc` para `.parquet` na camada Staging.

---

### Fase 3 — Transformação: Staging → Silver (Limpeza e Enriquecimento)

**Meta:** Job Glue aplica regras de qualidade de dados, limpeza e enriquecimento, gravando na camada Silver.

---

### Fase 4 — Camada Gold e Disponibilização

**Meta:** Dados analíticos prontos para consumo via Tableau, Power BI ou Python.

---

### Fase 5 — Observabilidade e CI/CD

**Meta:** Pipeline auditável com logs estruturados, alertas e automação de testes no CI.

---

### Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído |
| 🔲 | Pendente |
| 🔄 | Em progresso |

> [< Anterior - Estrutura do Repositório](/docs/06-estrutura-do-repositorio.md)