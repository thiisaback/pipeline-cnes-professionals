![logo.png](/docs/images/logo.png)
------
## Arquitetura do Projeto

O **PipeSUS** está sendo desenvolvido utilizando-se o padrão de **Arquitetura Medallion**, com separação clara entre as camadas Bronze, Silver e Gold. 

Além disso, há uma camada de *staging* entre as camadas Bronze e Silver, responsável por armazenar os dados convertidos do formato `.dbc` para `.parquet`.

![arquitetura-do-projeto.png](/docs/images/arquitetura-do-projeto.png)

---

### Fluxo de Dados

- **Ingestão:** Extração dos dados do FTP do DataSUS e *upload* dos arquivos `.dbc` na camada Bronze do *bucket* no Amazon S3, caso os dados estejam desatualizados.

- **Transformação:** *Trigger* via AWS Lambda e processamento via AWS Glue, convertendo os dados de `.dbc` para `.parquet` e realizando processos de limpeza e enriquecimento dos dados.

- **Armazenamento:** Armazenamento em um *Data Lake* no Amazon S3, nas camadas bronze, *staging*, silver e gold.

- **Disponibilização:** Os dados da camada gold poderão ser acessados via conexão direta do Tableau com o S3, ou do Power BI/outros projetos Python, através do código Python de integração.

> [Próximo - Arquitetura do Projeto >](/docs/05-decisoes-de-arquitetura.md)

> [< Anterior - Tecnologias e Ferramentas Utilizadas](/docs/03-tecnologias-e-ferramentas.md)