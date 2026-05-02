from src.ingestao.ingestao import processar_ingestao

if __name__ == '__main__':
    # Inicia o processo de ingestão de dados do servidor FTP do DataSUS para o Amazon S3
    processar_ingestao()