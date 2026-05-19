![logo.png](/docs/images/logo.png)
------
## Estrutura do Repositório

O repositório segue uma organização modular que separa as responsabilidades por camada da pipeline.

```
pipesus/
├── src/
│   ├── lambda/                    # Funções AWS Lambda
│   │   ├── ingestao.py            # Extração FTP DataSUS → S3 Bronze
│   ├── glue/                      # Jobs AWS Glue
│   ├── utils/                     # Funções utilitárias complementares do projeto
├── notebooks/                     # Análises exploratórias e prototipação
├── docs/                          # Documentação do projeto
│   └── images/                    # Imagens e diagramas
├── requirements.txt               # Dependências do projeto
├── .env.example                   # Variáveis de ambiente necessárias
├── .gitignore                     # Arquivos não commitados para o repositório
└── README.md                      # Página de entrada do projeto
```

---

### Convenções de Nomenclatura

| Escopo | Padrão |
|--------|--------|
| Arquivos Python | nomenclatura com espaços substituídos por traço |
| Funções Lambda | arquivo nomeado pela responsabilidade (`ingestao.py`, `trigger-glue.py`) |
| Jobs Glue | nomeados pelo fluxo de transformação (`origem-to-destino.py`) |
| Notebooks | prefixo numérico de ordenação (`01-`, `02-`, ...) |
| Variáveis de ambiente | `UPPER_SNAKE_CASE` |

---

### Regras de Acesso por Camada

| Camada | Leitura | Escrita | Observação |
|--------|---------|---------|------------|
| Bronze | Lambda (trigger), Glue | Lambda (ingestão) | Imutável após gravação |
| Staging | Glue (staging→silver) | Glue (bronze→staging) | Transitória |
| Silver | Glue (silver→gold) | Glue (staging→silver) | Dados confiáveis |
| Gold | Tableau, Power BI, Python | Glue (silver→gold) | Consumo analítico |

> [Próximo - Roadmap de Evolução da Pipeline >](/docs/07-roadmap.md)

> [< Anterior - Decisões de Arquitetura](/docs/05-decisoes-de-arquitetura.md)